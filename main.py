from geral import msg
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
    msg(0, "Carregando a configuração...")
    config = configuracaoCarregar()
    if config == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(0, "Criando a topologia de rede...")
    topologia = topologiaGenerica(config.topologia)
    if topologia == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(0, "Gerando grafo da topologia...")
    topologiaGerarGrafo(topologia, config.topologia)
    msg(0, "Inicializando o mininet com a topologia...")
    net = mininetInicializa(topologia)
    if net == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(0, "Inicializando o controlador...")
    controlador = controladorInicializa(net, config.metodo, topologia)
    if controlador == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(4, "Testando as conexões entre as máquinas da rede...")
    net.pingAll()
    msg(0, "Inicializando o servidor de telemetria...")
    telemetriaServidor = telemetriaInicializaServidor()
    if telemetriaServidor == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(0, "Inicializando agentes de telemetria...")
    telemetriaAgentes = telemetriaInicializaAgentes(config, telemetriaServidor, net)
    if telemetriaAgentes == None:
        msg(0, "Finalizando por falha.")
        exit(1)
    msg(0, "Executando os testes...")
    testeExecuta(config.teste, net)
    msg(0, "Finalizando agentes de telemetria...")
    telemetriaFinalizaAgentes(telemetriaAgentes)
    msg(0, "Obtendo o resultado dos testes...")
    resultado = telemetriaHistorico(telemetriaServidor)
    msg(0, "Finalizando o servidor de telemetria...")
    telemetriaFinalizaServidor(telemetriaServidor)
    msg(0, "Finalizando o controlador...")
    controladorFinaliza(controlador)
    msg(0, "Finalizando o mininet...")
    mininetFinaliza(net)
    msg(0, "Salvando o resultado em arquivos...")
    arquivosSalvar(resultado, config.telemetria, config.teste)
    msg(0, "Gerando os gráficos dos resultados...")
    graficosGerar(resultado, config.telemetria, config.teste)
    msg(0, "Fim do processamento.")
    exit(0)