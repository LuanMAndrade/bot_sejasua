from langchain_qdrant import QdrantVectorStore
from langchain_openai.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import sqlite3
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import json

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def busca_db():
    conn = sqlite3.connect("estoque.db")
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
    for id_, nome, categoria, nome_do_atributo_1, valores_do_atributo_1, nome_do_atributo_2, valores_do_atributo_2, descricao, preco, estoque, imagens, imagem_principal, tipo in linhas:
        if tipo == "variable":
            descricao_geral = descricao
            categoria_geral = categoria
            conteudo = {'Descrição': descricao_geral}
            documento_atual = Document(page_content=json.dumps(conteudo, ensure_ascii=False), metadata={"id": id_,'Tipo': tipo, 'Nome': nome, 'Categoria': categoria_geral, f'{nome_do_atributo_1}': valores_do_atributo_1, f'{nome_do_atributo_2}': valores_do_atributo_2, 'Estoque': estoque, 'Preço': preco, 'Link das imagens': imagem_principal})
            documentos.append(documento_atual)
        elif tipo == "variation":
            conteudo = {'Descrição': descricao_geral}
            nome = nome.split("-")[0].strip()
            documento_atual = Document(page_content=json.dumps(conteudo, ensure_ascii=False), metadata={"id": id_,'Tipo': tipo, 'Nome': nome, 'Categoria': categoria_geral, f'{nome_do_atributo_1}': valores_do_atributo_1, f'{nome_do_atributo_2}': valores_do_atributo_2, 'Estoque': estoque, 'Preço': preco, 'Links das imagens': imagens})
            documentos.append(documento_atual)
        else:
            print("Algo de errado aconteceu")

    print("Criou docs")
    
    return documentos

def cria_colecao(nome_colecao: str,documentos):
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    
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
            embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        )
    except Exception as e:
        print(f"Erro ao conectar com Qdrant: {e}")
        return None
    return db

def busca_produtos(query, qdrant_bv):
    resultados = qdrant_bv.similarity_search(query, k=1)
    produtos = []
    for i, doc in enumerate(resultados):
        produtos.append(doc.page_content)
        print(f"\n🔹 Resultado {i}:")
        print(doc.page_content)
        print(f"📎 Metadata: {doc.metadata}")
    return produtos


if __name__ == '__main__':
    linhas = busca_db()
    documentos = cria_documento(linhas)
    if chama_qdrant("teste"):
        bv = chama_qdrant("teste")
    else:
        cria_colecao("teste", documentos)
        bv = chama_qdrant("teste")
    query = "camisa preta tamanho M"
    produtos = busca_produtos(query, bv)
    print(produtos)