import requests
import os
from dotenv import load_dotenv

load_dotenv()

WC_API_KEY = os.getenv("WC_API_KEY")
WC_API_SECRET = os.getenv("WC_API_SECRET")




def limpa_produtos():
    url = "https://sejasuamodafit.com.br/wp-json/wc/v3/products?per_page=100&page=1"

    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.get(url, auth=(WC_API_KEY, WC_API_SECRET), headers=headers)
    lista_produtos = []
    for produto in response.json():
        produto_limpo = ({
            'id':produto['id'],
            'name' : produto['name'],
            'preco' : produto['price'],
            'estoque' : produto['stock_quantity'],
            'categoria' : produto['categories'][0]['slug'],
            'images' : ([imagem['src'] for imagem in produto['images']] if produto['images'] else None),
            'tamanhos' : next((atributo['options'] for atributo in produto['attributes'] if atributo['name'] == 'Tamanho'), None),
            'cores' : next((atributo['options'] for atributo in produto['attributes'] if atributo['name'] == 'Cor'), None),
            'variations' : produto['variations'],
            'related_ids' : produto['related_ids'],
            'stock_status' : produto['stock_status'],
            'link' : produto['permalink']})
        lista_produtos.append(produto_limpo)
    print(response.json())

    return lista_produtos



def filtro(categoria_filtro, cor_filtro):

    lista_produtos = limpa_produtos()
    lista = []
    lista_final = []
    for produto in lista_produtos:
        if categoria_filtro == produto['categoria'] and produto['stock_status'] == 'instock':
            lista.append(produto)
    for produto in lista:
        if produto['cores']:
            for cor in produto['cores']:
                if cor == cor_filtro:
                    lista_final.append(produto)
    return lista_final

        
resposta = filtro('tops', 'Nude')

#print(resposta)