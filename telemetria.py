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
        if item is None:
            break
        if item['tipo'] == 'report':
            retorno.put(DataLake)
        else:
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
    if tipo == 'latency':
        nome = item['nome']
        valor = item['valor']
        msg.debug("Recebida telemetria: %s valor=%s" % (nome, valor))
        chave = tipo + '_' + nome
        baseDados = DataLake.get(chave, [])
        agora = datetime.now()
        datahora = agora.strftime("%Y-%m-%d %H:%M:%S")        
        # TODO: Limitar no máximo de itens suportados
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
    telemetriaServidor['fila'].put(None)
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
    telemetriaAgentes = []
    fila = telemetriaServidor['fila']
    config_telemetria = config.telemetria
    for item in config_telemetria:
        tipo = item['type']
        if tipo == 'latency':
            for origem in item['sources']:
                if origem == 'paths':
                    for rota in config.caminhos:
                        processo = Process(target=procAgenteTelemetria, args=(fila, tipo, rota, net))
                        processo.start()
                        telemetriaAgentes.append( { 
                            'tipo': tipo,
                            'nome': rota['name'],
                            'caminho': rota['path'],
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
#   rota - array contendo o caminho
#   net - objeto para acessar o Mininet e enviar os comandos aos hosts
#
def procAgenteTelemetria(fila, tipo, rota, net):
    nome = rota['name']
    caminho = rota['path']
    #msg.debug("Agente telemetria, tipo=Latência rota [%s]= [%s]" % (nome, caminho))
    if tipo == 'latency':
        origem = caminho[0]
        destino = caminho[-1]
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
                fila.put( { 'tipo': 'latency', 'nome': nome, 'valor': valor } )
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
    fila.put({'tipo': 'report'})
    # Aguarda na fila o retorno do dicionário contendo os dados coletados
    resultado = retorno.get()
    msg.info("Dados históricos carregados!")
    return resultado
