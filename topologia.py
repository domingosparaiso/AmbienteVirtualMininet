from mininet.topo import Topo
from rotas import gerarRotasEstaticas
import json

################################################################################
# Classe que representa uma topologia no Mininet
#
class topologiaGenerica(Topo):
    switches_to_graph = []
    hosts_to_graph = []
    links_to_graph = []
    rotas_estaticas = None

    def __init__(self, config):
        topologia = config.topologia
        # Inicializa a topologia
        Topo.__init__(self)
        # Lista de links
        links = []
        # Lista de switches
        switches = []
        for host in topologia['hosts']:
            # ignora hosts com '#' no nome, serão inseridos posteriormente
            if not '#' in host:
                self.addHost(host)
                self.hosts_to_graph.append(host)
        cont = 1
        self.switches_dpid = {}
        for switch in topologia['switches']:
            switches.append(switch)
            self.switches_dpid.update( { switch: cont } )
            self.switches_to_graph.append(switch)
            self.addSwitch(switch)
            self.addSwitch(switch, dpid=hex(cont).lstrip("0x"))
            cont = cont + 1
        for link in topologia['links']:
            pontos = link['pontos']
            a = pontos[0]
            b = pontos[1]
            banda = link['banda']
            atraso = link['atraso']
            perda = link['perda']
            if type(banda) == str:
                if banda == '':
                    banda = None
                else:
                    try:
                        banda = int(banda)
                    except:
                        banda = None
            if atraso == '':
                atraso = None
            else:
                atraso = f'{atraso}ms'
            if type(perda) == str:
                if perda == '':
                    perda = None
                else:
                    try:
                        perda = int(perda)
                    except:
                        perda = None
            # TODO: Inserir no link as restrições de banda, atraso e perda
            self.addLink(a, b, bw=banda, delay=atraso, loss=perda)
            self.links_to_graph.append((a, b))

    # Funcoes que retornam switches, links e hosts para geracao do grafo
    def get_switches_to_graph(self):
        return self.switches_to_graph

    def get_hosts_to_graph(self):
        return self.hosts_to_graph

    def get_nodes_to_graph(self):
        return self.hosts_to_graph + self.switches_to_graph

    def get_links_to_graph(self):
        return self.links_to_graph

    def set_rotas_estaticas(self, rotas):
        self.rotas_estaticas = rotas
        return None

    def get_rotas_estaticas(self):
        return self.rotas_estaticas
