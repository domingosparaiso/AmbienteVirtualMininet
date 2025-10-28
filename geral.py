################################################################################
# Mostra mensagem na tele de acordo com o seu nível
#
# Parâmetros:
#   nivel - 0 - mensagens gerais de orquestração do programa
#           1 - mensagens dos serviços executados
#           2 - mensagens de erro
#           3 - mensagens de aviso
#           4 - mensagens de debug
def msg(nivel, texto):
    if nivel == 0:
        print(f'[*] {texto}', flush=True)
    if nivel == 1:
        print(f'  > {texto}', flush=True)
    if nivel == 2:
        print(f'---[E] {texto}', flush=True)
    if nivel == 3:
        print(f'---[W] {texto}', flush=True)
    if nivel == 4:
        print(f'   [#] {texto}', flush=True)
    return
