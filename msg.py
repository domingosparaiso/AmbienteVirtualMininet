################################################################################
# Mostra mensagem na tele de acordo com o seu nível
#
#   nivel - 0 - mensagens de erro
#           1 - mensagens de aviso
#           2 - mensagens gerais de orquestração do programa
#           3 - mensagens dos serviços executados
#           4 - mensagens de debug

MESSAGE_LEVEL = 4

def erro(texto):
    msg(0, texto)

def aviso(texto):
    msg(1, texto)

def main(texto):
    msg(2, texto)

def info(texto):
    msg(3, texto)

def debug(texto):
    msg(4, texto)

def msg(nivel, texto):
    if nivel <= MESSAGE_LEVEL:
        if nivel == 0:
            print(f'[Erro] {texto}', flush=True)
        if nivel == 1:
            print(f'[Aviso] {texto}', flush=True)
        if nivel == 2:
            print(f'[*] {texto}', flush=True)
        if nivel == 3:
            print(f'  | {texto}', flush=True)
        if nivel == 4:
            print(f'   [#] {texto}', flush=True)
    return
