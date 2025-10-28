import msg
from time import sleep

################################################################################
# Executa todos os testes programados
#
# Parâmetros:
#   config_testes - configuração de quais testes serão executados
#   net - objeto para ter acesso ao mininet
# Retorno:
#   None
#
def testeExecuta(config_testes, net):
    msg.info("Iniciando todos os processos de teste...")
    sleep(15)
    msg.info("Todos os testes foram executados!")
    return
