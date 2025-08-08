import pandas as pd
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Annotated


# @tool
def filtro(categoria_filtro: Annotated[str, "Filtra pela categoria do produto"] = None,
           cor_filtro: Annotated[str, "Filtra pela cor do produto"] = None,
           tamanho_filtro: Annotated[str, "Filtra pelo tamanho do produto"] = None):
    """Realiza uma busca no estoque filtrando por categoria, cor, tamanho e tipo do produto.
    Retorna um DataFrame com os produtos filtrados."""
    
    
    # Lê o CSV
    df = pd.read_csv('C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\data\\estoque.csv')

    # Preenche valores ausentes com NaN padrão do pandas
    df.fillna(value=pd.NA, inplace=True)

    # Inicializa resultado
    resultados = []

    # Variável para guardar a categoria atual do produto pai (tipo variable)
    categoria_atual = None

    # Itera linha a linha
    for _, row in df.iterrows():
        tipo = str(row.get('Tipo')).strip().lower()

        if tipo == 'variable':
            # Armazena a categoria para as próximas variações
            categoria_atual = str(row.get('Categorias')).strip().lower()
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

            if estoque and float(estoque) > 0:
                if categoria_filtro is None or categoria_atual == categoria_filtro.lower():
                    if cor_filtro is None or (cor is not None and cor_filtro.lower() in cor.lower()):
                        if tamanho_filtro is None or tamanho == tamanho_filtro.lower():
                            resultados.append(row)


    print(f'resultados: {resultados}')
    itens = []
    for item in resultados:
        itens.append({'Nome' :  item['Nome'],
        'Descrição' : item['Descrição'],
        'Imagens': item['Imagens']})

    return pd.DataFrame(itens)
