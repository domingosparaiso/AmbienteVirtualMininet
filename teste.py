import os
import numpy as np
import msg
from multiprocessing import Process
from datetime import datetime, time, timedelta
import time
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
def testeExecuta(config_testes, net, fila, config_topologia):
    msg.info("Iniciando todos os processos de teste...")
    processos = []
    for teste in config_testes:
        processo = Process(target=procTeste, args=(teste, net, fila, config_topologia))
        processo.start()
        processos.append({ 'proc': processo, 'id': teste['id']})
    msg.info("Aguardando o fim dos testes...")
    for processo in processos:
        processo['proc'].join()
    msg.info("Todos os testes foram executados!")
    return None

# todo: atualizar para permitir testes de poisson
## nova função: entre todos os hosts
## 
def procTeste(teste, net, fila, topologia):
    procid = teste['id']
    descricao = teste['descricao']
    msg.info(f'Iniciando de processo de teste [{procid}]: {descricao}')
    itens = teste['itens']
    for item in itens:
        tipo = item['tipo']
        if tipo == 'poisson':
            duracao = item['duracao']
            tamanhofluxo = item['tamanhofluxo']
            lambdarate = item['lambda']
            hosts = topologia['hosts']
            all2allpoisson(net, lambdarate, duracao, tamanhofluxo, hosts)
            continue
        if tipo == 'delay':
            duracao = item['duracao']
            msg.debug(f'[{procid}]: delay {duracao}s')
            time.sleep(duracao)
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

def all2allpoisson(net, lambdarate, duracao, tamanhofluxo, hosts):
    if len(hosts) > 0:
        msg.info("\n*** Running all-to-all poison tests\n")

        #arq_bwm = f"relatorios/poisson-tmp.bwm"
        #monitor_bw = Process(target=monitor_bwm_ng, args=(arq_bwm, 1.0))

        processos = []

        for origem in hosts:
            for destino in hosts:
                if origem != destino:
                    src = net.get(origem)
                    dst = net.get(destino)

                    processo = Process(target=generate_flows, args=(lambdarate, duracao, tamanhofluxo, src, dst))
                    processos.append(processo)
                    processo.start()

        for processo in processos:
            processo.join()
        
        print('acabou de verdade')
        #os.system("killall bwm-ng")

# Function to generate iperf flows with a fixed size, 
def generate_flows(lambda_rate, duration, flow_size_kb, src, dst):
    """
    Generate iperf TCP flows from a fixed source to a fixed destination based on a Poisson distribution
    for the initiation rate. Each flow uses a fixed size of 100KB.
    
    :param net: Mininet network object
    :param src: Source host for iperf flows
    :param dst: Destination host for iperf flows
    :param lambda_rate: Average rate (events per second) for the Poisson distribution
    :param duration: Duration to run the experiment
    :param flow_size_kb: Fixed size of each flow (in Kilobytes)
    """

    end_time = time.time() + duration
    port = 5001  # Starting port number
    
    while time.time() < end_time:
        # Generate time until the next event using Poisson distribution
        delay = np.random.poisson(1 / lambda_rate)
        time.sleep(delay)
        
        # Define the fixed flow size in bytes
        flow_size_bytes = flow_size_kb * 1024  # Convert size to bytes
        
        # Convert bytes to megabytes for iperf usage
        flow_size_mb = flow_size_bytes / (1024 * 1024)
        
        # Check if the port is available
        if port > 65535:
            print("Port number exceeded range.")
            break
        
        # Start iperf server on the destination host if not already running
        dst_port = port
        if not dst.cmd(f'netstat -an | grep {dst_port}'):
            dst.cmd(f'iperf3 -s -1 -p {dst_port} &')
        
        # Start iperf client on the source host
        # print("TCP mouse flows from H2 to H5")
        src.cmd(f'iperf3 -c {dst.IP()} -p {dst_port} -n {flow_size_mb:.2f}M &')
        print(f'iperf {src.name} to {dst.name} ')
        
        # Increment the port number for the next flow
        port += 1
    
    print('finalizado')


def monitor_bwm_ng(fname, interval_sec):
    cmd = f"sleep 1; bwm-ng -t {interval_sec * 1000} -o csv -u bytes -T rate -C ',' > {fname}"
    subprocess.Popen(cmd, shell=True).wait()