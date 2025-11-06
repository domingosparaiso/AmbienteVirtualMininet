import msg
from multiprocessing import Queue
from multiprocessing import Process
from time import sleep
from datetime import datetime

DataLake = {}

################################################################################
# Carrega em um novo processo o servidor de telemetria
#   este processo precisa ser carregado antes de incializar os agentes
#   e precisa estar ativo para que os dados sejam recuperados no fim do teste
#
# Parâmetros:
#   None
# Retorno:
#   Objeto para acesso ao servidor
#
def telemetriaInicializaServidor():
    fila = Queue()
    retorno = Queue()
    processo = Process(target=procServidorTelemetria, args=(fila, retorno))
    processo.start()
    telemetriaServidor = { 'processo': processo, 'fila': fila, 'retorno': retorno }
    msg.info("Servidor de telemetria incializado!")
    return telemetriaServidor

################################################################################
# Servidor de telemetria executado em um processo separado para recebimento dos 
#   dados de telemetria
#
# Parâmetros:
#    fila - objeto tipo Queue para receber a telemetria dos agentes
#    retorno - objeto tipo Queue usado para devolver os dados coletados
#
def procServidorTelemetria(fila, retorno):
    while True:
        item = fila.get()
        # Encerra o processo quando receber o valor None na fila
        if item is None:
            break
        # Envia os dados coletados quando receber um objeto do tipo 'dados'
        if item['tipo'] == 'dados':
            # Os dados coletados são enviados para a Queue de retorno
            retorno.put(DataLake)
        else:
            # Salva a nova informação de telemetria
            salvarTelemetria(item)
    return None

################################################################################
# Rotina de salvamento dos dados de telemetria na base de dados em memória
#
# Parâmetros:
#   item - objeto com os dados que serão guardados (formato depende da telemetria)
# Retorno:
#   None
#
def salvarTelemetria(item):
    tipo = item['tipo']
    # Verifica e armazena de acordo com o tipo de dado recebido
    if tipo == 'latencia':
        nome = item['nome']
        valor = item['valor']
        #msg.debug("Recebida telemetria: %s valor=%s" % (nome, valor))
        # cada telemetria possui uma chave diferente no formato "latencia_{nome}"
        chave = tipo + '_' + nome
        # Se a base já existe, obtem o histórico, se é nova, cria um array vazio
        baseDados = DataLake.get(chave, [])
        agora = datetime.now()
        # Coleta contém data/hora atuais
        datahora = agora.strftime("%Y-%m-%d %H:%M:%S")        
        # TODO: Limitar no máximo de itens suportados
        baseDados.append( { 'datahora': datahora, 'valor': valor } )
        # Atualiza a base de dados da latência recebida
        DataLake.update({chave: baseDados})
    if tipo == 'iperf':
        nome = item['nome']
        valor = item['valor']
        datahora = item['datahora']
        chave = tipo + '_' + nome
        baseDados = DataLake.get(chave, [])
        baseDados.append( { 'datahora': datahora, 'valor': valor } )
        DataLake.update({chave: baseDados})
    return None

################################################################################
# Finaliza o processo do servidor de telemetria
#
# Parâmetros:
#   telemetriaServidor - Objeto para acesso ao servidor que será finalizado
# Retorno:
#   None
#
def telemetriaFinalizaServidor(telemetriaServidor):
    # Sinaliza ao servidor que vamos finalizar colocando None na fila
    telemetriaServidor['fila'].put(None)
    # Aguarda o processo do servidor finalizar
    telemetriaServidor['processo'].join()
    msg.info("Servidor de telemetria finalizado!")
    return None

################################################################################
# Inicializa todos os agentes em processos separados para coleta de telemetria
#
# Parâmetros:
#   config - configuração completa
#   telemetriaServidor - Objeto para acesso à fila do servidor
#   net - objeto para acessar o Mininet e enviar os comandos aos hosts
# Retorno:
#   Dicionário contendo os objetos de acesso aos agentes
#
def telemetriaInicializaAgentes(config, telemetriaServidor, net):
    # Lista de agentes ativos
    telemetriaAgentes = []
    # Queue onde o servidor de telemetria aguarda os valores
    fila = telemetriaServidor['fila']
    config_topologia = config.topologia
    config_telemetria = config.telemetria
    # Passar por todas as telemetrias configuradas
    for item in config_telemetria:
        tipo = item['tipo']
        # Tratar de acordo com o tipo
        if tipo == 'latencia':
            for origem in item['origens']:
                # Quando origem == 'rotas', pegar da lista na configuração
                if origem == 'rotas':
                    for rota in config_topologia['rotas']:
                        # Inicia um processo de agente
                        processo = Process(target=procAgenteTelemetria, args=(fila, tipo, rota['nome'], rota['caminho'], net))
                        processo.start()
                        # Armazena os dados do processo para controle futuro
                        telemetriaAgentes.append( { 
                            'tipo': tipo,
                            'nome': rota['nome'],
                            'parametros': rota['caminho'],
                            'processo': processo
                        } )
    msg.info("Agentes de telemetria inicializados!")
    return telemetriaAgentes

################################################################################
# Rotina executada em um processo separado para coleta e envio de telemetria
#
# Parâmetros:
#   fila - objeto Queue para onde os dados devem ser enviados (servidor)
#   tipo - tipo de telemetria (ex: latência)
#   nome - nome do agente (ex: rota1)
#   parametros - objeto contendo os valores para configuração do agente
#   net - objeto para acessar o Mininet e enviar os comandos aos hosts
#
def procAgenteTelemetria(fila, tipo, nome, parametros, net):
    if tipo == 'latencia':
        origem = parametros[0]
        destino = parametros[-1]
        host_origem = net.get(origem)
        host_destino = net.get(destino)
        ip_destino = host_destino.IP()
        while True:
            host_origem.sendCmd('ping %s' % (ip_destino))
            for host, line in net.monitor(hosts=[host_origem]):
                try:
                    valor = float(line.strip().split(' ')[6].split('=')[1])
                except:
                    valor = 0
                #msg.debug("Enviando telemetria de '%s' para a fila" % (nome))
                fila.put( { 'tipo': 'latencia', 'nome': nome, 'valor': valor } )
    return None

################################################################################
# Finaliza todos processos dos agentes de telemetria
#
# Parâmetros:
#   telemetriaAgentes - dicionário com os agentes que serão finalizados
# Retorno:
#   None
#
def telemetriaFinalizaAgentes(telemetriaAgentes):
    for agente in telemetriaAgentes:
        nome = agente['nome']
        tipo = agente['tipo']
        msg.debug("Finalizando %s, tipo=%s" % (nome, tipo))
        processo = agente['processo']
        processo.terminate()
    sleep(2)
    for agente in telemetriaAgentes:
        processo = agente['processo']
        if processo.is_alive():
            processo.kill()
            processo.join()
    msg.info("Agentes de telemetria finalizados!")
    return None

################################################################################
# Obtem o histórico de telemetria e dados dos testes realizados
#   deve ser executado antes de finalizar o servidor de telemetria
#
# Parâmetros:
#   telemetriaServidor - objeto de acesso ao servidor de telemetria
# Retorno:
#   Dicionário contendo todos os dados obtidos pelo servidor de telemetria
#
def telemetriaHistorico(telemetriaServidor):
    fila = telemetriaServidor['fila']
    retorno = telemetriaServidor['retorno']
    # Envia mensagem solicitando os dados coletados
    fila.put({'tipo': 'dados'})
    # Aguarda na fila o retorno do dicionário contendo os dados coletados
    resultado = retorno.get()
    msg.info("Dados históricos carregados!")
    return resultado
