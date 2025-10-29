import msg
from configuracao import configuracaoCarregar
from graficos import topologiaGerarGrafo, arquivosSalvar, graficosGerar
from rede import mininetInicializa, controladorInicializa, controladorFinaliza, mininetFinaliza
from telemetria import telemetriaInicializaServidor, telemetriaInicializaAgentes, telemetriaFinalizaAgentes, telemetriaHistorico, telemetriaFinalizaServidor
from topologia import topologiaGenerica
from teste import testeExecuta

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
    topologia = topologiaGenerica(config.topologia)
    if topologia == None:
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
    controlador = controladorInicializa(net, config.metodo, topologia)
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
    testeExecuta(config.teste, net)
    msg.main("Finalizando agentes de telemetria...")
    telemetriaFinalizaAgentes(telemetriaAgentes)
    msg.main("Obtendo o resultado dos testes...")
    resultado = telemetriaHistorico(telemetriaServidor)
    msg.main("Finalizando o servidor de telemetria...")
    telemetriaFinalizaServidor(telemetriaServidor)
    msg.main("Finalizando o controlador...")
    controladorFinaliza(controlador)
    msg.main("Finalizando o mininet...")
    mininetFinaliza(net)
    msg.main("Salvando o resultado em arquivos...")
    arquivosSalvar(resultado, config.telemetria, config.teste)
    msg.main("Gerando os gráficos dos resultados...")
    graficosGerar(resultado, config.telemetria, config.teste)
    msg.main("Fim do processamento.")
    exit(0)