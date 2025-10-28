from mininet.topo import Topo
import json

################################################################################
# Classe que representa uma topologia no Mininet
#
class topologiaGenerica(Topo):
    switches_to_graph = []
    hosts_to_graph = []
    links_to_graph = []

    def __init__(self, topologia):
        # Inicializa a topologia
        Topo.__init__(self)
        # Lista de links
        links = []
        # Lista de switches
        switches = []
        for host in topologia['hosts']:
            self.addHost(host)
            self.hosts_to_graph.append(host)
        cont = 1
        for switch in topologia['switches']:
            switches.append(switch)
            self.switches_to_graph.append(switch)
            self.addSwitch(switch)
            self.addSwitch(switch, dpid=hex(cont).lstrip("0x"))
            cont = cont + 1
        for link in topologia['links']:
            if '-' in link:
                a,b = link.split('-')
                self.addLink(a, b)
                self.links_to_graph.append((a, b))

    # Funcoes que retornam switches, links e hosts para geracao do grafo
    def get_switches_to_graph(self):
        return self.switches_to_graph

    def get_hosts_to_graph(self):
        return self.hosts_to_graph

    def get_links_to_graph(self):
        return self.links_to_graph