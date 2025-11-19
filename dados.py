#
# Base de dados temporal
#
# Estrutura do DataLake
# {
#   tipo1: {
#       nome1: {
#           'valores': {
#               { tempo1: valor1 }, { tempo2: valor2 },...
#           },
#           'evento': {
#               { tempo1: evento1 }, { tempo2: evento2 },...
#           }
#       },...
#   },...
# }

import sys
from datetime import datetime

SIZE_CACHE = 10000
DataLake = {}
LogEventos = []

# get_dados - Consulta a base de dados temporal e retorna os dados interpolados dentro dos limites indicados
#
# Parâmetros:
#   filtro_tipo - tipos de dados que se procura, ex: 'latencia', ou '*' para todos os dados.
#   nome_filtro - nome do agente que criou os dados, ex: 'rota1', 'teste', ou '*' para todos os agentes
#   inicio, fim - data e hora de início e fim, pode ser um valor numérico equivalente a datetime.timestamp(datahora)
#       se for informado '*' o valor usado é a data e hora atuais, se iniciar com '-' deve ser seguido por um valor
#       inteiro e um sufixo ('h', 'm' ou 's') que indica o tempo relativo ao tempo atual (horas, minutos ou segundos)
#   intervalo - intervalo em segundos que deve ser usado para interpolar os resultados
# Retorno:
#   dicionário contendo os dados selecionados dentro do intervalo indicado
#
def get_all():
    resultado = { 'valores': {}, 'eventos': [] }
    resultado['eventos'] = sorted(LogEventos, key=lambda item: item['datahora'])
    maximo = None
    minimo = None
    for tipo, dados_tipo in DataLake.items():
        for nome, lista in dados_tipo.items():
            for datahora, valor in lista.items():
                dh = float(datahora)
                if maximo == None or dh > maximo:
                    maximo = dh
                if minimo == None or dh < minimo:
                    minimo = dh
    if maximo != None and minimo != None:
        resultado['valores'] = get_valores('*', '*', minimo, maximo, 1)
    return resultado

def get_valores(filtro_tipo, nome_filtro, inicio, fim, intervalo):
    resultado_tipo = {}
    for tipo, dados_tipo in DataLake.items():
        if filtro_tipo == '*' or filtro_tipo == tipo:
            resultado_nome = {}
            for nome, lista in dados_tipo.items():
                if nome_filtro == '*' or nome_filtro == nome:
                    valores = filtra_dados(
                        lista,
                        stringtime(inicio),
                        stringtime(fim),
                        intervalo
                    )
                    resultado_nome.update( { nome: valores } )
            resultado_tipo.update( { tipo: resultado_nome } )
    return resultado_tipo

# get_eventos - Consulta a base de dados temporal e retorna os eventos ocorridos
#
# Parâmetros:
#   filtro_tipo, nome_filtro, inicio e fim - similar à função get_dados()
#   obs: Não existe o parâmetro intervalo porque os eventos não são valores para que sejam interpolados
# Retorno:
#   dicionário contendo os eventos selecionados dentro do intervalo indicado
#
def get_eventos(filtro_tipo, nome_filtro, inicio, fim):
    resultado = []
    for item in LogEventos:
        tipo = item['tipo']
        nome = item['nome']
        datahora = item['datahora']
        evento = item['evento']
        if filtro_tipo == '*' or filtro_tipo == tipo:
            if nome_filtro == '*' or nome_filtro == nome:
                int_inicio = stringtime(inicio)
                int_fim = stringtime(fim)
                dh = datetime.strptime(
                    datahora,
                    "%Y-%m-%d %H:%M:%S"
                )
                ftempo = datetime.timestamp(dh)
                if ftempo >= int_inicio and ftempo <= int_fim:
                    resultado.append(item)
    return resultado

# set_valor - grava um valor float na base de dados ou None se for inválido
#
# Parâmetros:
#   tipo - tipo de dados a armazenar, ex: 'latencia', 'vazao'
#   nome - nome do agente que gerou o dado, ex: 'rota1', 'teste'
#   datahora - data e hora no formato timestamp, valor do tipo float
#       semelhante ao retornado por datetime.timestamp
#   valor - valor a ser armazenado em formato string, será convertido para float
# Retorno:
#   None
#
def set_valor(tipo, nome, datahora, valor):
    dados_tipo = DataLake.get(tipo, {})
    try:
        fvalor = float(valor)
    except:
        fvalor = None
    if type(datahora) == float:
        fdatahora = datahora
    else:
        try:
            fdatahora = float(datahora)
        except:
            fdatahora = datetime.timestamp(datetime.now())
    lista = dados_tipo.get(nome, {})
    chaves = lista.keys()
    if len(chaves)>(SIZE_CACHE):
        lista.pop(chaves[0])
    lista.update( { idx(fdatahora): fvalor } )
    dados_tipo.update( { nome: lista } )
    DataLake.update( { tipo: dados_tipo } )
    return None

# set_evento - grava um evento na base de eventos e None na base de dados
#
# Parâmetros:
#   tipo - tipo de dados a armazenar, ex: 'latencia', 'vazao'
#   nome - nome do agente que gerou o dado, ex: 'rota1', 'teste'
#   datahora - data e hora no formato timestamp, valor do tipo float
#       semelhante ao retornado por datetime.timestamp
#   evento - string com o evento a ser armazenado
# Retorno:
#   None
#
def set_evento(tipo, nome, datahora, evento):
    if type(datahora) == float:
        fdatahora = datahora
    else:
        try:
            fdatahora = float(datahora)
        except:
            fdatahora = datetime.timestamp(datetime.now())
    ts_datahora = datetime.fromtimestamp(fdatahora)
    dh = ts_datahora.strftime("%Y-%m-%d %H:%M:%S")
    LogEventos.append( { 
        'datahora': dh,
        'tipo': tipo,
        'nome': nome,
        'evento': evento
    } )
    dados_tipo = DataLake.get(tipo, {})
    lista = dados_tipo.get(nome, {})
    chaves = lista.keys()
    if len(chaves)>(SIZE_CACHE):
        lista.pop(chaves[0])
    lista.update( { idx(fdatahora): None } )
    dados_tipo.update( { nome: lista } )
    DataLake.update( { tipo: dados_tipo } )
    return None

# valor_interpolado - calcula e retorna um valor interpolado usando uma regra de três
#
# Parâmetros:
#   valor_anterior - último valor antes do tempo atual
#   proximo_valor - próximo valor após o tempo atual
#   tempo_anterior - timestamp do valor anterior
#   proximo_tempo - timestamp do próximo valor
#   tempo_atual - timestamp onde se deseja que o valor seja posicionado proporcionalmente
# Retorno:
#   valor interpolado (float)
#
def valor_interpolado(valor_anterior, proximo_valor, tempo_anterior, proximo_tempo, tempo_atual):
    if valor_anterior == None:
        return None
    if proximo_valor == None:
        return valor_anterior
    delta_tempo = proximo_tempo - tempo_anterior
    delta_valor = proximo_valor - valor_anterior
    delta_atual = tempo_atual - tempo_anterior
    diferenca = delta_atual / delta_tempo * delta_valor
    interpolado = valor_anterior + diferenca
    return interpolado

# filtra_dados - busca os dados brutos do repositório, interpola usando o intervalo especificado e retorna os dados
#
# Parâmetros:
#   dados - base de dados que será pesquisada, no formato {{timestamp1:valor1},{timestamp2:valor2},...}
#   inicio - timestamp inicial para filtrar
#   fim - timestamp final para filtrar
#   intervalo - intervalo de interpolação
# Retorno:
#   dicionário com os dados filtrado no formato {{timestamp1:valor1},{timestamp2:valor2},...}
#
def filtra_dados(dados, inicio, fim, intervalo):
    resultado = {}
    tempo = inicio
    chaves = [*dados.keys()]
    maximo = len(chaves)
    indice = 0
    while tempo <= fim:
        while indice < maximo and float(chaves[indice]) < tempo:
            indice = indice+1
        if indice < maximo and float(chaves[indice]) == tempo:
            resultado.update( { tempo : dados.get(idx(tempo), 0) } )
        else:
            if indice < maximo and indice > 0:
                tempo_anterior = float(chaves[indice-1])
                valor_anterior = dados.get(idx(tempo_anterior), 0)
                proximo_tempo = float(chaves[indice])
                proximo_valor = dados.get(idx(proximo_tempo), 0)
                # value (interpolate)
                #  <tempo_anterior>.....<tempo>.....<tempo+n>.....<proximo_tempo>
                valor = valor_interpolado(
                    valor_anterior, proximo_valor,
                    tempo_anterior, proximo_tempo,
                    tempo)
                resultado.update( { idx(tempo) : valor } )
        tempo = tempo + float(intervalo)
    return resultado

# stringtime - recebe uma string, faz o tratamento dos casos especiais e retorna um timestamp (float)
#
# Parâmetros:
#   tempo - string com o tempo que precisa ser convertido em timestamp
# Retorno:
#   tempo convertido em timestamp (float)
#
def stringtime(tempo):
    # valores especiais
    #    * = agora, ou seja, data e hora atuais
    #    -<valor><tempo> = relativo ao tempo atual, onde valor=número inteiro e tempo=h(hora),m(minuto) ou s(segundo)
    #        ex: -3m  (agora - 3 minutos)
    #            -40s (agora - 40 segundos)
    if type(tempo) == float:
        return tempo
    if tempo == '*':
        resultado = datetime.timestamp(datetime.now())
    else:
        if tempo[0:1] == '-':
            val = tempo[1:-1]
            uni = tempo[-1:]
            fator = 0
            if uni == 's':
                fator = 1
            if uni == 'm':
                fator = 60
            if uni == 'h':
                fator = 3600
            try:
                value = float(val)
            except:
                value = 0
            resultado = datetime.timestamp(datetime.now()) - ( value * fator )
        else:
            try:
                resultado = float(tempo)
            except:
                resultado = datetime.timestamp(datetime.now())
    return resultado

# idx - converte um timestamp em um índice para o banco de dados, chaves de dicionários precisam ser do tipo string
#
# Parâmetros:
#   tempo - timestamp, se for do tipo string ou int, tenta converter para float
# Retorno:
#   tempo convertido em uma string para uso como chave do dicionário na base de dados
#
def idx(tempo):
    t = tempo
    if type(tempo) == str or type(tempo) == int:
        try:
            t = float(tempo)
        except:
            t = datetime.timestamp(datetime.now())
    return f'{t:.8f}'
