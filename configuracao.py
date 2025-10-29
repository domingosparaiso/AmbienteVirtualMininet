CONFIG_FILE = 'config.json'
import msg
import json

################################################################################
# Classe com as configurações carregadas do arquivo json
#
class configuracao():
    topologia = {}
    caminhos = []
    telemetria = []
    teste = []
    plotagem = []
    metodo = ""
    def load(self, json_context):
        try:
            self.topologia = json_context['topologia']
            self.caminhos = json_context['caminhos']
            self.telemetria = json_context['telemetria']
            self.teste = json_context['testefluxo']
            self.plotagem = json_context['plotagem']
            self.metodo = json_context['metodo']
            result = True
        except:
            result = False
        return result

################################################################################
# Lê o arquivo de configurações e carrega no objeto
#
# Parâmetros:
#   None
# Retorno:
#   objeto contendo toda a configuração carregada
#
def configuracaoCarregar():
    config = configuracao()
    msg.info(f"Lendo arquivo '{CONFIG_FILE}'...")
    try:
        f = open(CONFIG_FILE, 'r')
        json_context = json.loads(f.read())
        f.close()
    except:
        msg.erro(f"Erro ao carregar o arquivo de configuração '{CONFIG_FILE}' !!!")
        return None
    if config.load(json_context) == None:
        msg.erro(f"Erro no conteúdo do arquivo de configuração '{CONFIG_FILE}' !!!")
        return None
    else:
        msg.info("Configuração carregada!")
    return config
