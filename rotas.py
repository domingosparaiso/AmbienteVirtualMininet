import msg
import networkx as nx

def gerarRotasEstaticas(config, topologia, net):
    rotas = config.topologia['rotas']

    # retorna lista de rotas dinâmicas a serem geradas e rotas estáticas
    lista_rotas, procurar_rotas = organizaRotas(rotas)

    # Cria grafo da topologia
    Gtopo = grafoTopologia(topologia)

    # procurar as rotas dinâmicas e atualizar o dicionário
    procurar_rotas = expandirRotasDinamicas(procurar_rotas, Gtopo)

    # substituis rotas dinâmicas dentro das rotas estáticas
    lista_rotas = substituirRotasDinamicas(lista_rotas, procurar_rotas)

    rotas_estaticas = {}
    for item in lista_rotas:
        if len(item['caminho']) > 3:
            caminho = item['caminho'][1:-1]
            for x in [-1, 0]:
                destino = item['caminho'][x]
                if x == 0:
                    caminho.reverse()
                for i in range(0, len(caminho)-1):
                    switch_out = caminho[i]
                    switch_in = caminho[i+1]
                    dpid_out = topologia.switches_dpid.get(switch_out, None)
                    dpid_in = topologia.switches_dpid.get(switch_in, None)
                    if switch_out and switch_in:
                        lista = rotas_estaticas.get(dpid_out, {})
                        lista.update( { destino: dpid_in } )
                        rotas_estaticas.update( { dpid_out : lista } )
    return rotas_estaticas

def organizaRotas(rotas):
    lista_rotas = []
    procurar_rotas = {}
    # Todas as rotas configuradas
    for rota in rotas:
        caminho = rota['caminho']
        switch_origem = None
        switch_destino = None
        # Se existe um '*' no caminho, então precisa buscar rotas
        if '*' in caminho:
            # posição do '*' na lista
            indice = caminho.index('*')
            # não pode estar nem na primeira nem na última posição
            if indice > 0 and (indice+1) < len(caminho):
                # switches em torno do '*'
                switch_origem = caminho[indice-1]
                switch_destino = caminho[indice+1]
            else:
                # tem '*' mas está em uma posição inválida, ignora rota
                msg.aviso('Uma rota da configuração está inválida, ignorando.')
                continue
        # Se achou o '*' e os switches válidos, registrar onde procurar
        if switch_origem != None and switch_destino != None:
            # definir o par de switches sempre na mesma ordem
            if switch_origem < switch_destino:
                chave = switch_origem + ':' + switch_destino
            else:
                chave = switch_destino + ':' + switch_origem
            # dicionário das rotas que precisam ser procuradas
            # se não existir um item para a chave, cria com os valores padrão
            item = procurar_rotas.get(chave, {
                    'switch_origem': switch_origem,
                    'switch_destino': switch_destino,
                    'rotas': [],
                    'num_rotas': 0,
                    'indice': 0
            })
            # incrementa o num_rotas a cada nova rota que se fizer necessária
            item['num_rotas'] = item['num_rotas']+1
            # atualiza o item no dicionario
            procurar_rotas.update({chave: item})
            # adiciona nas rotas estáticas com a chave para buscar as rotas
            lista_rotas.append({'procurar': chave, 'caminho': caminho})
        else:
            # adiciona nas rotas estáticas, não vai pesquisar rotas
            lista_rotas.append({'procurar': None, 'caminho': caminho})
    return lista_rotas, procurar_rotas

def grafoTopologia(topologia):
    # Criar um grafo da topologia
    Gtopo = nx.Graph()  # Monta o grafo da topologia
    Gtopo.add_nodes_from(sorted(topologia.get_nodes_to_graph())) # nodes do grafo
    Gtopo.add_edges_from(topologia.get_links_to_graph())  # links do grafo
    return Gtopo

def expandirRotasDinamicas(procurar_rotas, Gtopo):
    # Descobrir as rotas e preencher no dicionário
    for chave, item in procurar_rotas.items():
        # Procurar rotas entre dois switches
        switch_origem = item['switch_origem']
        switch_destino = item['switch_destino']
        num_rotas = item['num_rotas']
        #Pesquisa no grafo os caminhos possíveis
        caminhos_dinamicos = list(nx.all_simple_paths(Gtopo, source=switch_origem, target=switch_destino))
        # ordena pelos caminhos mais curtos
        caminhos_ordenados = sorted(caminhos_dinamicos, key=len)
        item['rotas'] = []
        for i in range(num_rotas):
            # insere na lista rotas a quantidade necessária, se existir
            if i < len(caminhos_ordenados):
                item['rotas'].append(caminhos_ordenados[i][1:-1])
        # atualiza o dicionário
        procurar_rotas.update({ chave: item })
    return procurar_rotas

def substituirRotasDinamicas(lista_rotas, procurar_rotas):
    # substituir as rotas dinamicas nos templates '*'
    for i in range(len(lista_rotas)):
        rota = lista_rotas[i]
        chave = rota['procurar']
        # Verifica se foram encontradas rotas dinamicas
        if not chave in procurar_rotas:
            # Se não encontrou nenhuma, ignora a rota
            lista_rotas[i] = None
            continue
        # se não possui chave, então não é rota dinâmica
        if chave != None:
            # nova rota a ser construída
            novo_caminho = []
            for node in rota['caminho']:
                # tratar os nodes com '*' e substituir pelas rotas calculadas
                if node == '*':
                    # verficiar a última rota usada na lista
                    indice = procurar_rotas[chave]['indice']
                    # tamanho da lista de rotas
                    tamanho_rotas = len(procurar_rotas[chave]['rotas'])
                    # se chegar na última, volta para a primeira
                    if indice >= tamanho_rotas:
                        indice = 0
                    # inclui a rota no lugar do '*'
                    novo_caminho.extend(procurar_rotas[chave]['rotas'][indice])
                    # aponta para a próxima rota
                    procurar_rotas[chave]['indice'] = indice + 1
                else:
                    # se era um node normal (host ou switch), inclui na nova rota
                    novo_caminho.append(node)
            # atualiza o caminho
            lista_rotas[i]['caminho'] = novo_caminho
    return lista_rotas