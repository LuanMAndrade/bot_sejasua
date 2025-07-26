import os
import sqlite3
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import json

def rag(query):
    
    # 0. Definir diretório onde será salvo o banco vetorial
    PERSIST_DIR = "chroma_db"

    # 1. Configurar o modelo de embeddings do Google
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")


    # 2. Verificar se o banco vetorial já existe
    if os.path.exists(PERSIST_DIR):
        print("📦 Banco vetorial já existe, carregando do disco...")
        chroma_db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embedding_model)
    else:
        print("📦 Banco vetorial não encontrado, criando a partir do SQLite...")

        # Conectar ao SQLite
        conn = sqlite3.connect("estoque.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT 
        ID,
        Nome, 
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
        linhas = cursor.fetchall()

        # Criar documentos do LangChain
        documentos = []
        for id_, nome, nome_do_atributo_1, valores_do_atributo_1, nome_do_atributo_2, valores_do_atributo_2, descricao, preco, estoque, imagens, imagem_principal, tipo in linhas:
            if tipo == "variable":
                conteudo = {'Nome': nome, 'Descrição': descricao, 'Link das imagens gerais': imagem_principal , 'Variações': []}
                documento_atual = Document(page_content=json.dumps(conteudo, ensure_ascii=False), metadata={"id": id_})
                documentos.append(documento_atual)
            elif tipo == "variation":
                variacao = f"{nome_do_atributo_1}: {valores_do_atributo_1}, {nome_do_atributo_2}: {valores_do_atributo_2},Estoque: {estoque}, Preço: {preco} Links das imagens da variação: {imagens}"
                conteudo_dict = json.loads(documento_atual.page_content)
                conteudo_dict['Variações'].append(variacao)
                documento_atual.page_content = json.dumps(conteudo_dict, ensure_ascii=False)
            else:
                print("Algo de errado aconteceu")

        # Criar banco vetorial com Chroma
        chroma_db = Chroma.from_documents(documents=documentos, embedding=embedding_model, persist_directory=PERSIST_DIR)
        chroma_db.persist()
        print("✅ Banco vetorial criado e salvo em disco.")

    # 3. Realizar consulta
    resultados = chroma_db.similarity_search(query, k=7)
    produtos = []

    # 4. Exibir resultados
    for i, doc in enumerate(resultados):
        produtos.append(doc.page_content)
        print(f"\n🔹 Resultado {i}:")
        print(doc.page_content)
        print(f"📎 Metadata: {doc.metadata}")
    return produtos

      

     

