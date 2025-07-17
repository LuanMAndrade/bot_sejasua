import requests

token = '7149b2b736292118f84a97e53d576039db73020c59ad83d377efcdf14090c606'

# URL para cada tipo de requisição
url_pesquisar_produtos = 'https://api.tiny.com.br/api2/produtos.pesquisa.php'
url_obter_produto = 'https://api.tiny.com.br/api2/produto.obter.php'
url_pdv_pesquisar_produtos = 'https://api.tiny.com.br/api2/pdv.produtos.php'
estoque_url = 'https://api.tiny.com.br/api2/lista.atualizacoes.estoque'

# Parâmetros para cada requisição
params_pesquisar_produtos = {
    'token': token,
    'pesquisa':'CALCA LEGGING TRAINING',
    'formato': 'json'
}

params_obter_produto = {
    'token': token,
    'id': 776157874,
    'formato': 'json'
}

params_pdv_pesquisar_produtos = {
    'token': token,
    'pagina': 1,
    'situacao': 'A'
}

params_estoque = {
    'token': token,
    'dataAlteracao': '10/07/2025 00:00:00',
    'formato': 'json'
}


# Fazendo a requisição
#response = requests.get(estoque_url, params=params_estoque)
#response2 = requests.get(url_obter_produto, params=params_obter_produto)
response3 = requests.get(url_pdv_pesquisar_produtos, params=params_pdv_pesquisar_produtos)

        
# num = response3.json()['retorno']['numero_paginas']
# filtrado = []
# for i in range(num):
#     params_pdv_pesquisar_produtos = {
#     'token': token,
#     'pagina': i,
#     'situacao': 'A'
#     }
#     response3 = requests.get(url_pdv_pesquisar_produtos, params=params_pdv_pesquisar_produtos)
#     for p in response3.json()['retorno']['produtos']:
#         if p['categoria'] == 'Short':
#             filtrado.append(p)

print(response3.json())

# print(filtrado)
# print(len(filtrado))
