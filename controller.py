#!/usr/bin/python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------
# Trabalho 2 - Automatizacao de teste de rede utilizando Ryu e Mininet
#
# Mestrado em Computacao Aplicada - PPCOMP 2020/1
# Disciplina de Redes de Computadores
#
# Aluno: Luciano Biancardi Fiorino
#
# Descrição:
#   Implementacao do Controlador OpenFlow usando Ryu
#--------------------------------------------------------------------------


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ether_types
from ryu.lib.packet import arp, icmp

from ryu.controller.dpset import EventDP
from ryu import cfg

import matplotlib.pyplot as plt
import networkx as nx
import argparse
import sys
import pickle


class Trabalho2Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(Trabalho2Controller, self).__init__(*args, **kwargs)

        #Parametro do metodo de roteamento
        self.CONF = cfg.CONF
        self.CONF.register_opts([
            cfg.StrOpt('routing_method', default=None,
                       help='Metodo de roteamento.')
        ])
        self.routing_method = self.CONF.routing_method
        if not self.routing_method:
            self.logger.info("\n********** Metodo de roteamento nao informado **********")
            self.logger.infoprint("Para OSPF -> ryu-manager controller.py --config-file=method-ospf.conf")
            self.logger.infoprint("Para ECMP -> ryu-manager controller.py --config-file=method-ecmp.conf")
            self.logger.infoprint("\n")
            exit(1)
        else:
            self.logger.info("Routing method = %s" % self.routing_method)
            # Cria arquivo temporario para salvar o modo de roteamento da execucao
            # para o script fctmain.py ler e adicionar no titulo dos graficos de vazao
            f = open("controller_routing_mode.tmp", "w")
            f.write(self.routing_method)
            f.close()           


        #self.mac_to_port = {}
        self.dpid_to_datapath = {} # Datapaths dos dpid (switches)
        #self.ip_to_mac = {}  # Mac dos ips dos hosts
        
        # -------------------- Le o arquivo com os dados da topologia ---------------------
        self.data_topo = pickle.load( open( "graph_topo.pickle", "rb" )) 
        self.ip_to_mac = self.data_topo['ip_to_mac']  # Mac dos ips dos hosts
        self.mac_to_switch = self.data_topo['mac_to_switch']   # Switch que o MAC esta conectado

        self.Gtopo = nx.DiGraph()  # Monta o grafo da topologia
        gnodes = self.data_topo['nodes']  # nodes do grafo
        gedges =  self.data_topo['edges'] # informacoes dos links incluindo as portas de conexao     
        self.Gtopo.add_nodes_from(sorted(gnodes))
        self.Gtopo.add_edges_from(gedges)

        #self.logger.info("\n\n********** GRAPH LINKS DATA **********")
        #self.logger.info(self.Gtopo.edges.data())
        # -------------------- fim da leitura dos dados da topologia ---------------------

        # Dicionario com os links e as portas
        # Links entre as conexoes com as portas de entrada e saida
        # Ex: (1, 2, 'port':3) - Link entre switch 1 e 2, para 1 chegar a 2 tem que sair pela porta 3. 
        self.link_port = nx.get_edge_attributes(self.Gtopo,'port')

    # Função para instalar table-miss
    # Fonte: ryu/app/simple_switch_13.py
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Funcao para capturar os switches e guardar os datapaths       
    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def _event_switch_enter_handler(self, event):
        datapath = event.dp
        dpid = datapath.id

        # Salva o datapath no dicionario
        self.dpid_to_datapath[dpid] = datapath 
        

        if event.enter:
            self.dpid_to_datapath[dpid] = datapath
            #self.logger.info("Switch dpid=%s connected.", dpid)
            
        else:
            self.dpid_to_datapath.pop(dpid)
            #self.logger.info("Switch dpid=%s disconected.", dpid)

    # Funcao descrita no manual do Ryu para adicionar um fluxo em um datapath
    # Fonte: ryu/app/simple_switch_13.py
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    # Funcao que trata os pacotes recebidos pelo controlador
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        #if ev.msg.msg_len < ev.msg.total_len:
        #    self.logger.debug("packet truncated: only %s of %s bytes",
        #                      ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        # Analise pacote icmp echo reply para entregar ao host de destino
        pkt_icmp = pkt.get_protocols(icmp.icmp)
        if len(pkt_icmp) > 0:
            #print (pkt_icmp)
            if (pkt_icmp[0].code == 0): # echo reply
                    data = pkt.data
                    datapath = self.dpid_to_datapath[self.mac_to_switch[dst]]
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    out_port = self.link_port[(self.mac_to_switch[dst], dst)]
                    actions = [parser.OFPActionOutput(out_port)]
                    out = parser.OFPPacketOut(datapath=datapath,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                in_port=ofproto.OFPP_CONTROLLER,
                                actions=actions,
                                data=data)

                    datapath.send_msg(out) 
        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        # Analisa pacote ARP
        pkt_arp = pkt.get_protocols(arp.arp)
        if len(pkt_arp)>0: # Se recebeu um pacote ARP
            #self.logger.info(pkt_arp)
            src_ip = pkt_arp[0].src_ip
            dst_ip = pkt_arp[0].dst_ip
            
            # Se conhece o mac do ip de destino, instala o path
            if dst_ip in self.ip_to_mac:
                #print (dst_ip, self.ip_to_mac[dst_ip])

                dst = self.ip_to_mac[dst_ip] 
                
                #print ("\n\nInstala caminho de [%s - switch %s] para [%s - switch %s]" % (src, self.mac_to_switch[src], dst, self.mac_to_switch[dst]))
                self.install_path(src = src, 
                                    dst = dst, 
                                    switch_src = self.mac_to_switch[src], 
                                    switch_dst = self.mac_to_switch[dst],
                                    pkt=pkt)

                                     

    # Funcao que instala os fluxos no caminho entre os hosts
    def install_path(self, src, dst, switch_src, switch_dst, pkt):

        path = self.find_route(switch_src, switch_dst, self.routing_method) # Procura a rota
        #print ("Caminho = %s" % path)

        for i, switch in enumerate(path): # Percorre o caminho 

            datapath = self.dpid_to_datapath[switch] # datapath do swich
            
            # Hosts no mesmo switch
            if len(path) == 1:
                # porta em que o host de origem esta conectado no switch
                in_port = self.link_port[(switch, src)]

                # porta em que o host de destino esta conectado no switch   
                out_port = self.link_port[(switch, dst)]  
        

            # Primeiro switch
            elif switch == path[0]:
                # porta em que o host de origem esta conectado no switch
                in_port = self.link_port[(switch, src)]          
                
                # porta de saida do switch para no proximo switch
                out_port = self.link_port[(switch, path[i+1])]    
            

            # Ultimo switch
            elif switch == path[-1]:
                # porta em que o switch anterior esta conectado
                in_port = self.link_port[(switch, path[i-1])]

                # porta em que o host de destino esta conectado no switch
                out_port = self.link_port[(switch, dst)]         


            # Switch intermediario   
            else:
                # porta em que o switch anterior esta conectado
                in_port = self.link_port[(switch, path[i-1])]

                # porta de saida do switch para no proximo switch
                out_port = self.link_port[(switch, path[i+1])]   

        
            #---------- Adiciona o fluxo no switch ----------
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            actions = [parser.OFPActionOutput(out_port)]
            
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)

            self.add_flow(datapath, 1, match, actions)
            #---------- Fim adiciona o fluxo no switch ----------
        

        # Envia o packet_out com a pacote arp para o ultimo switch do caminho        
        data = pkt.data
        out = parser.OFPPacketOut(datapath=datapath,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                in_port=ofproto.OFPP_CONTROLLER,
                                actions=actions,
                                data=data)
        datapath.send_msg(out)       
  
    def find_route(self, switch_in, switch_out, method):
        
        method = method.upper()
        
        if method == "OSPF":    # Roteamento OSPF
            #print ("OSPF")
            path = nx.shortest_path(self.Gtopo, switch_in, switch_out)
            #print "src=%s dst=%s path=%s" %(source, target, path)

        elif method == "ECMP":  # Roteamento ECMP    
            #print ("ECMP")
            paths = []
            for p in nx.all_shortest_paths(self.Gtopo, switch_in, switch_out):
                paths.append(p)
            #print paths
            path = self.get_route_ecmp(switch_in, switch_out, paths)
            #print "src=%s dst=%s path=%s" %(switch_src, switch_dst, paths)
            
        return path

    def get_route_ecmp(self, switch_in, switch_out, paths):
        #print(switch_in, switch_out, paths)
        if paths:
            # print(paths)
            # Escolha a função de hash que desejar, desde que gere um número
            hash = self.generate_hash(switch_in, switch_out)
            #print("Hash = %s" % hash)
            choice = hash % len(paths)
            #print("Choice = %s" % choice)
            path = sorted(paths)[choice]
        return path

    def generate_hash(self, switch_in, switch_out):
        s = str(switch_in)+str(switch_out)
        return hash(s)

