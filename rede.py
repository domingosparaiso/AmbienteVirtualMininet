import msg
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController
from subprocess import Popen
from multiprocessing import Process
from time import sleep
import pickle
from rotas import gerarRotasEstaticas

################################################################################
# Inicializa o mininet, zera a configuração atual e carrega a topologia configurada
#
# Parâmetros:
#   topologia - objeto com a topologia a ser usada nos testes
# Retorno:
#   net - objeto de acesso ao mininet
#   None - em caso de erro na inicialização
#
def mininetInicializa(topologia):
    try:
        # Limpa Mininet
        msg.debug("Limpando configuração do Mininet")
        process = Popen('sudo mn -c -v output'.split())
        process.wait() 
        net = Mininet(topologia, controller=None, autoSetMacs=True, link=TCLink, cleanup=True)
        net.addController("c0",
                          controller=RemoteController,
                          ip='127.0.0.1',
                          port=6633)
        net.start()
        msg.debug("Forçando os switches a suportarem OpenFlow 1.3")
        for switch in net.switches:
            switch.cmd("ovs-vsctl set bridge %s protocols=OpenFlow13" % switch)
        msg.debug("Desabilitando IPV6 nos hosts e switches")
        for host in net.hosts:
            host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
            host.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
            host.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        for switch in net.switches:
            switch.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
            switch.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
            switch.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        msg.info("Mininet inicializado!")
    except:
        msg.erro("Falha na inicialização do Mininet!!!")
        net = None
    return net

################################################################################
# Finaliza o mininet
#
# Parâmetros:
#   None
# Retorno:
#   None
#
def mininetFinaliza(net):
    #net.stop()
    process = Popen('sudo mn -c -v output'.split())
    process.wait()
    msg.info("Mininet finalizado!")
    return None

################################################################################
# Inicializa o controlador Ryu, a configuração indica qual método de roteamento será usado
#
# Parâmetros:
#   net - objeto usado para acessar o mininet
#   config - objeto com toda a configuração do sistema
#   topologia - objeto com a topologia a ser usada nos testes
# Retorno:
#   objeto para acessar o controlador
#
def controladorInicializa(net, config, topologia):
    # método de roteamento configurado (ospf, ecmp ou otimizador externo)
    config_metodo = config.metodo
    try:
        topologia.set_rotas_estaticas(gerarRotasEstaticas(config, topologia, net))
        # Lista de switches por dpid
        switches = []
        for s in topologia.switches():
            # Convert dpid para decimal, o Ryu usa decimal
            dpid = int(topologia.nodeInfo(s)["dpid"], 16) 
            switches.append(dpid)
        # Lista de arestas
        links = []
        # Dicionario com o MAC e o dpid do switch que o host está conectado
        mac_to_switch = {}
        for link in net.links:
            node1, port1 = link.intf1.name.split('-eth')
            node2, port2 = link.intf2.name.split('-eth')
            # Links entre os switches        
            if topologia.isSwitch(node1) and topologia.isSwitch(node2):
                node1_dpid = int(topologia.nodeInfo(node1)["dpid"], 16) 
                node2_dpid = int(topologia.nodeInfo(node2)["dpid"], 16)          
                links.append((node1_dpid, node2_dpid, {'port':int(port1)}))
                links.append((node2_dpid, node1_dpid, {'port':int(port2)}))
            # Links entre os hosts e os switches
            if not topologia.isSwitch(node1):
                node2_dpid = int(topologia.nodeInfo(node2)["dpid"], 16) 
                h = net.get(node1)
                links.append((node2_dpid, h.MAC(), {'port':int(port2)}))
                mac_to_switch[h.MAC()] = node2_dpid
            else:
                # Links entre os hosts e os switches
                if not topologia.isSwitch(node2):
                    node1_dpid = int(topologia.nodeInfo(node1)["dpid"], 16) 
                    h = net.get(node2)
                    links.append((node1_dpid, h.MAC(), {'port':int(port1)}))
                    mac_to_switch[h.MAC()] = node1_dpid

        # Atualizando o IP de destino nas rotas estáticas
        rotas_estaticas = {}
        for dpid, lista in topologia.rotas_estaticas.items():
            rotas = {}
            for destino, saida in lista.items():
                h = net.get(destino)
                rotas.update( { h.IP(): saida } )
            rotas_estaticas.update( { dpid: rotas } )

        # Salva os dados da topologia no arquivo para o controlador
        with open("graph_topo.pickle", 'wb') as f:
            G = {}
            G['nodes'] = sorted(switches)
            G['edges'] = links
            G['rotas'] = rotas_estaticas
            # Dicionario com o IP e o MAC dos hosts
            G['ip_to_mac'] = {host.IP(): host.MAC() for host in net.hosts}
            G['mac_to_switch'] = mac_to_switch
            # Salva o arquivo pickle para o controlador
            pickle.dump(G, f)
        controlador = Popen(f'ryu-manager controller.py --config-file=method-{config_metodo}.conf'.split())
        pid = controlador.pid
        sleep(2)
        msg.info(f"Controlador incializado com PID={pid}")
    except:
        msg.erro("Falha na incialização do controlador!!!")
        controlador = None
    return controlador

################################################################################
# Finaliza o controlador Ryu
#
# Parâmetros:
#   controlador - objeto para acessar o controlador
# Retorno:
#   None
#
def controladorFinaliza(controlador):
    controlador.terminate()
    controlador.wait()
    msg.info("Controlador finalizado!")
    return None

