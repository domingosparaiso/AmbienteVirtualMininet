import msg
from time import sleep
from multiprocessing import Process
from datetime import datetime, timedelta
import subprocess

################################################################################
# Executa todos os testes programados
#
# Parâmetros:
#   config_testes - configuração de quais testes serão executados
#   net - objeto para ter acesso ao mininet
#   fila - objeto tipo Queue para enviar dados ao servidor de telemetria
# Retorno:
#   None
#
def testeExecuta(config_testes, net, fila):
    msg.info("Iniciando todos os processos de teste...")
    processos = []
    for teste in config_testes:
        processo = Process(target=procTeste, args=(teste, net, fila))
        processo.start()
        processos.append({ 'proc': processo, 'id': teste['id']})
    msg.info("Aguardando o fim dos testes...")
    for processo in processos:
        processo['proc'].join()
    msg.info("Todos os testes foram executados!")
    return None

def procTeste(teste, net, fila):
    procid = teste['id']
    descricao = teste['descricao']
    msg.info(f'Iniciando de processo de teste [{procid}]: {descricao}')
    itens = teste['itens']
    for item in itens:
        tipo = item['tipo']
        if tipo == 'delay':
            duracao = item['duracao']
            msg.debug(f'[{procid}]: delay {duracao}s')
            sleep(duracao)
            continue
        if tipo == 'iperf':
            duracao = item['duracao']
            origem = item['origem']
            destino = item['destino']
            porta = item['porta']
            msg.debug(f'[{procid}]: iperf {origem} -> {destino}:{porta}, {duracao}s')
            parametros_origem = item['parametros_origem']
            parametros_destino = item['parametros_destino']
            otimizador = item['otimizador']
            host_origem = net.get(origem)
            if host_origem != None:
                host_destino = net.get(destino)
                if host_destino != None:
                    ip_destino = host_destino.IP()
                    cmd_destino = f"iperf3 -s -B {ip_destino} -p {porta} -1 -fk --forceflush --timestamps=%F;%T; {parametros_destino}"
                    cmd_origem = f"iperf3 -c {ip_destino} -p {porta} -t {duracao} {parametros_origem}"
                    p_destino = host_destino.popen(cmd_destino.strip().split(' '))
                    p_origem = host_origem.popen(cmd_origem.strip().split(' '))
                    stdout_d, stderr_d = p_destino.communicate()
                    stdout_o, stderr_o = p_origem.communicate()
                    lista = stdout_d.decode().split('\n')
                    envia = False
                    incializado = False
                    for linha in lista:
                        L = linha.split(' ')
                        if envia:
                            if L[-1] == '-':
                                break
                            K = [c for c in L if c]
                            try:
                                valor = float(K[-2])
                            except:
                                valor = 0
                            str_datahora = ' '.join(linha.split(';')[0:2])
                            if not incializado:
                                incializado = True
                                data = linha.split(';')[0:1][0].split('-')
                                hora = linha.split(';')[1:2][0].split(':')
                                dh = datetime(int(data[0]), int(data[1]), int(data[2]), int(hora[0]), int(hora[1]), int(hora[2])) - timedelta(seconds=1)
                                #agora = dh.strftime("%Y-%m-%d %H:%M:%S")
                                agora = datetime.timestamp(dh)
                                fila.put( {
                                    'tipo': 'iperf',
                                    'nome': procid,
                                    'datahora': agora,
                                    'valor': None,
                                    'evento': 'BEGIN'
                                } )
                            dh = datetime.strptime(
                                str_datahora,
                                "%Y-%m-%d %H:%M:%S"
                            )
                            datahora = datetime.timestamp(dh)
                            fila.put( { 
                                'tipo': 'iperf',
                                'nome': procid,
                                'datahora': datahora,
                                'valor': valor,
                                'evento': None
                            } )
                        else:
                            if L[-1] == 'Bitrate':
                                envia = True
                    datahora = datetime.timestamp(datetime.now())
                    fila.put( {
                        'tipo': 'iperf',
                        'nome': procid,
                        'datahora': datahora,
                        'valor': None,
                        'evento': 'END'
                    } )
                    continue
        msg.aviso(f'[{procid}] {tipo}: falha no item de teste.')
    msg.info(f'Fim de processo de teste [{procid}]: {descricao}')
    return None