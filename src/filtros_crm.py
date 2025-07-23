import pandas as pd
from utils import config
import sqlite3


def filtrar_variacoes(categoria_filtro = None, cor_filtro = None, tamanho_filtro = None, tag_filtro = None, nome_filtro=None, descricao_filtro= None):
    
    resultados = []

    # Variável para guardar a categoria atual do produto pai (tipo variable)
    categoria_atual = None

    conn = sqlite3.connect('estoque.db')

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM estoque")

    for row in cursor.fetchall():
        row = dict(row)
        tipo = str(row.get('Tipo')).strip().lower()

        if tipo == 'variable':
            # Armazena a categoria para as próximas variações
            categoria_atual = str(row.get('Categorias')).strip().lower()
            descricao = str(row.get('Descrição')).strip().lower()
            continue

        if tipo == 'variation':
            # Verifica se a variação corresponde aos filtros
            estoque = row.get('Em estoque?', 0)
            atributos = {
                str(row.get('Nome do atributo 1')).strip().lower(): str(row.get('Valores do atributo 1')).strip().lower(),
                str(row.get('Nome do atributo 2')).strip().lower(): str(row.get('Valores do atributo 2')).strip().lower()
            }

            cor = atributos.get('cor')
            tamanho = atributos.get('tamanho')
            tags =  str(row.get('Tags')).strip().lower()
            nome = str(row.get('Nome')).strip().lower()
            row['Descrição'] = descricao

            

            if estoque and float(estoque) > 0:
                if categoria_filtro is None or categoria_atual == categoria_filtro.lower():
                    if cor_filtro is None or (cor is not None and cor_filtro.lower() in cor.lower()):
                        if tamanho_filtro is None or tamanho == tamanho_filtro.lower():
                            if tag_filtro is None or tag_filtro == tags:
                                if nome_filtro is None or (nome is not None and nome_filtro.lower() in nome.lower()):
                                    if descricao_filtro is None or (descricao is not None and descricao_filtro.lower() in descricao.lower()):
                                        resultados.append(row)

    itens = []
    for item in resultados:
        itens.append({'Nome' :  item['Nome'],
        'Descrição' : item['Descrição'],
        'Imagens': item['Imagens'],
        'Preço': item['Preço'],
        'Imagens_extras' : item['Metadado: rtwpvg_images']})
    
    config.produtos_interesse = itens

    return pd.DataFrame(itens)

            