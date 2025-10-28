CONFIG_FILE = 'config.json'
from geral import msg
import json

################################################################################
# Classe com as configurações carregadas do arquivo json
#
class configuracao():
    topologia = {}
    caminhos = []
    telemetria = []
    teste = []
    metodo = ""
    def load(self, json_context):
        try:
            self.topologia = json_context['topology']
            self.caminhos = json_context['paths']
            self.telemetria = json_context['telemetry']
            self.teste = json_context['flowtest']
            self.metodo = json_context['method']
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
    msg(1, f"Lendo arquivo '{CONFIG_FILE}'...")
    try:
        f = open(CONFIG_FILE, 'r')
        json_context = json.loads(f.read())
        f.close()
    except:
        msg(2, f"Erro ao carregar o arquivo de configuração '{CONFIG_FILE}' !!!")
        return None
    if config.load(json_context) == None:
        msg(2, f"Erro no conteúdo do arquivo de configuração '{CONFIG_FILE}' !!!")
        return None
    else:
        msg(1, "Configuração carregada!")
    return config
