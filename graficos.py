import msg
import networkx as nx
import matplotlib.pyplot as plt

################################################################################
# Gera uma imagem contendo o grafo da topologia usada
#   O nome do arquivo é 'report/<name>.jpg', onde <name> está no arquivo de
#   configuração em <topology.name>
#
# Parâmetros:
#   topologia - objeto contendo a topologia em uso
#   config_topologia - configuração da topologia a ser usada
#   config_plotagem - informações sobre a plotagem do grafo
# Retorno:
#   None
#
def topologiaGerarGrafo(topologia, config_topologia, config_plotagem):
    descricao = None
    for item in config_plotagem:
        if item['tipo'] == 'topologia':
            descricao = item['descricao']
    if descricao == None:
        msg.aviso('Grafo da topologia não foi configurado.')
        return None
    # Cria o grafo da topologia
    Gtopo = nx.DiGraph() # Grafo da topologia

    sw = topologia.get_switches_to_graph()
    hs = topologia.get_hosts_to_graph()
    ed = topologia.get_links_to_graph()
 
    Gtopo.add_nodes_from(sw)
    Gtopo.add_nodes_from(hs)
    Gtopo.add_edges_from(ed)

    # Define layout do grafo baseado na topologia para melhor visualizacao
    pos = nx.nx_agraph.graphviz_layout(Gtopo, prog='circo', args='')

    plt.figure(figsize=(50,30))
    plt.title(descricao, fontsize=60)

    nx.draw_networkx_nodes(Gtopo,pos, nodelist=sw, node_size=10000, node_color='g', label='Switches')
    nx.draw_networkx_nodes(Gtopo,pos, nodelist=hs, node_size=10000, node_color='b', label='Hosts')
    nx.draw_networkx_edges(Gtopo,pos, arrows=False, width=3)
    nx.draw_networkx_labels(Gtopo,pos, font_color='w', font_size=40, font_weight='bold')
    
    plt.axis('off')
    plt.legend(handletextpad=1.0, labelspacing=2.5, borderpad=1, fontsize=40, shadow=True)
    plt.savefig("relatorios/topologia_%s.png" % config_topologia['nome'])
    plt.clf()

    msg.info("Grafo da topologia gerado na pasta 'relatorios'.")
    return None

################################################################################
# Gerar os gráficos de telemetria e dos testes realizados
#
# Parâmetros:
#   resultado - dicionário contendo todos os dados obtidos pelo servidor de telemetria
#   config - objeto com a configuração do sistema
# Retorno:
#   None
#
def graficosGerar(resultado, config):
    for item in config.plotagem:
        if item['tipo'] == 'telemetria':
            msg.debug('Gráfico de telemetria: ' + item['descricao'])
        if item['tipo'] == 'testefluxo':
            msg.debug('Gráfico de teste de fluxo: ' + item['descricao'])
    msg.info("Imagens dos gráficos salvos na pasta 'relatorios'.")
    return None

