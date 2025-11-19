import msg
from datetime import datetime

################################################################################
# Salva o histórico de telemetria e dados de teste em arquivos texto
#
# Parâmetros:
#   resultado - dicionário contendo todos os dados obtidos pelo servidor contendo
#       telemetria e resultado dos testes de vazão
# Retorno:
#   None
#
def arquivosSalvar(resultado):
    valores = resultado['valores']
    for tipo, lista_nomes in valores.items():
        for nome, lista in lista_nomes.items():
            f = open(f'relatorios/{tipo}_{nome}.txt', 'w')
            for tempo, valor in lista.items():
                if type(tempo) == str:
                    ftempo = float(tempo)
                else:
                    ftempo = tempo
                ts_datahora = datetime.fromtimestamp(ftempo)
                datahora = ts_datahora.strftime("%Y-%m-%d %H:%M:%S")
                if valor == None:
                    svalor = 'None'
                else:
                    svalor = str(valor)
                f.write('%s\t%s\n' % (datahora, svalor))
            f.close()
    eventos = resultado['eventos']
    f = open(f'relatorios/eventos.txt', 'w')
    for item in eventos:
        datahora = item['datahora']
        tipo = item['tipo']
        nome = item['nome']
        evento = item['evento']
        f.write('%s\t%s\t%s\t%s\n' % (datahora, tipo, nome, evento))
    f.close()
    msg.info("Resultados salvos em arquivos na pasta 'relatorios'.")
    return None
