import msg
from configuracao import configuracaoCarregar
from graficos import topologiaGerarGrafo, graficosGerar
from relatorios import arquivosSalvar
from rede import mininetInicializa, controladorInicializa, controladorFinaliza, mininetFinaliza
from telemetria import telemetriaInicializaServidor, telemetriaInicializaAgentes, telemetriaFinalizaAgentes, telemetriaHistorico, telemetriaFinalizaServidor
from topologia import topologiaGenerica
from teste import testeExecuta
from rotas import gerarRotasEstaticas
#from mininet.cli import CLI

################################################################################
# Programa principal
#
if __name__ == '__main__':
    msg.main("Carregando a configuração...")
    config = configuracaoCarregar()
    if config == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Criando a topologia de rede...")
    topologia = topologiaGenerica(config)
    if topologia == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Gerando rotas estáticas...")
    if gerarRotasEstaticas(config, topologia) == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Gerando grafo da topologia...")
    topologiaGerarGrafo(topologia, config.topologia, config.plotagem)
    msg.main("Inicializando o mininet com a topologia...")
    net = mininetInicializa(topologia)
    if net == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Inicializando o controlador...")
    controlador = controladorInicializa(net, config, topologia)
    if controlador == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.debug("Testando as conexões entre as máquinas da rede...")
    net.pingAll()
    msg.main("Inicializando o servidor de telemetria...")
    telemetriaServidor = telemetriaInicializaServidor()
    if telemetriaServidor == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Inicializando agentes de telemetria...")
    telemetriaAgentes = telemetriaInicializaAgentes(config, telemetriaServidor, net)
    if telemetriaAgentes == None:
        msg.main("Finalizando por falha.")
        exit(1)
    msg.main("Executando os testes...")
    testeExecuta(config.testefluxo, net, telemetriaServidor['fila'], config.topologia)
    msg.main("Finalizando agentes de telemetria...")
    telemetriaFinalizaAgentes(telemetriaAgentes, telemetriaServidor['fila'])
    msg.main("Obtendo o resultado dos testes...")
    resultado = telemetriaHistorico(telemetriaServidor)
    #CLI(net)
    msg.main("Finalizando o servidor de telemetria...")
    telemetriaFinalizaServidor(telemetriaServidor)
    msg.main("Finalizando o controlador...")
    controladorFinaliza(controlador)
    msg.main("Finalizando o mininet...")
    mininetFinaliza(net)
    resultado.update( { 'rotas': config.topologia['rotas'] } )
    msg.main("Salvando o resultado em arquivos...")
    arquivosSalvar(resultado)
    msg.main("Gerando os gráficos dos resultados...")
    graficosGerar(resultado, config)
    msg.main("Fim do processamento.")
    exit(0)
