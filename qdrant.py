from langchain_qdrant import QdrantVectorStore
from langchain_openai.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import sqlite3
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import json
from qdrant_client import QdrantClient

load_dotenv()


SERVER_IP = os.getenv("SERVER_IP")
QDRANT_URL_TEMPLATE = os.getenv("QDRANT_URL")
QDRANT_URL = QDRANT_URL_TEMPLATE.format(SERVER_IP=SERVER_IP)

print(QDRANT_URL)

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


def busca_db():
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
    ID,
    Nome,
    Categorias,
    "Nome do atributo 1", 
    "Valores do atributo 1", 
    "Nome do atributo 2", 
    "Valores do atributo 2",               
    "Descrição curta", 
    Preço, 
    Estoque,
    "Metadado: rtwpvg_images",
    Imagens,
    Tipo
    FROM estoque

    """)
    print("Buscou no banco de dados de estoque")
    return cursor.fetchall()

def cria_documento(linhas):
    documentos = []
    descricao_geral = ""
    counter = False
    variacoes = []
    for id_, nome, categoria, nome_do_atributo_1, valores_do_atributo_1, nome_do_atributo_2, valores_do_atributo_2, descricao, preco, estoque, imagens, imagem_principal, tipo in linhas:
        if tipo == "variable":
            if counter == True:
                texto = ""
                for variacao in variacoes:
                    texto += f"\n{variacao}"
                conteudo = {'Descrição': (descricao_geral if descricao_geral else "") + "variações:" + texto}
                documento_atual = Document(page_content=json.dumps(conteudo, ensure_ascii=False), metadata={'Tipo': tipo, 'Nome': nome_geral, 'Categoria': categoria_geral,'Preço': preco, 'Link das imagens': imagem_principal_geral})
                documentos.append(documento_atual)
                variacoes = []
        if nome:
            nome = nome.lower()
        if valores_do_atributo_1:
            valores_do_atributo_1 = valores_do_atributo_1.lower()
        if valores_do_atributo_2:
            valores_do_atributo_2 = valores_do_atributo_2.lower()
        if categoria:
            categoria = categoria.lower()
        if tipo == "variable":
            descricao_geral = descricao
            categoria_geral = categoria
            nome_geral = nome
            imagem_principal_geral = imagem_principal
            counter = True
        elif tipo == "variation":
            conteudo = {'Descrição': descricao_geral}
            nome = nome.split("-")[0].strip()
            documento_atual = Document(page_content=json.dumps(conteudo, ensure_ascii=False), metadata={"id": id_,'Tipo': tipo, 'Nome': nome, 'Categoria': categoria_geral, f'{nome_do_atributo_1}': valores_do_atributo_1, f'{nome_do_atributo_2}': valores_do_atributo_2, 'Estoque': estoque, 'Preço': preco, 'Links das imagens': imagens})
            documentos.append(documento_atual)
            variacoes.append(f"({nome_do_atributo_1}: {valores_do_atributo_1}, {nome_do_atributo_2}: {valores_do_atributo_2}, Estoque: {estoque})")
        else:
            print("Algo de errado aconteceu")

    print("Criou docs")
    
    return documentos

def cria_colecao(nome_colecao: str):
    linhas = busca_db()
    documentos = cria_documento(linhas)
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    QdrantVectorStore.from_documents(
        documents=documentos,
        embedding=embedding_model,
        url=QDRANT_URL,
        collection_name=nome_colecao,
    )
    print("Coleção criada com sucesso!")

def chama_qdrant(nome_colecao: str):
    try:
        db = QdrantVectorStore.from_existing_collection(
            collection_name=nome_colecao,
            url= QDRANT_URL,
            embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        )
    except Exception as e:
        print(f"Erro ao conectar com Qdrant: {e}")
        return None
    return db

if __name__ == '__main__':
    if chama_qdrant("estoque_vetorial"):
        bv = chama_qdrant("estoque_vetorial")
    else:
        cria_colecao("estoque_vetorial")
        bv = chama_qdrant("estoque_vetorial")