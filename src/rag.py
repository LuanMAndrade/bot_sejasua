from langchain.document_loaders import PyPDFLoader, CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os
from langchain_community.document_loaders import TextLoader


embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
documento_teste = "C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\data\\inf_loja.txt"
documento_teste2 = "C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\data\\estoque.csv"

lista_documentos = [documento_teste, documento_teste2]


def divide_texto(documentos, tamanho_maximo=500):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho_maximo, length_function=len, chunk_overlap=0)
    lista = []
    for documento in documentos:
        splitado = text_splitter.split_documents(documento)
        lista.extend(splitado)
    return lista

def banco_vetorial(documents):
    Chroma.from_documents(
        documents,
        collection_name='banco_vetorial',
        embedding=embedding_model,
        persist_directory="./meu_banco_vetorial"
    )


def ler_docs(documentos):
    lista = []
    for documento in documentos:
        if documento.endswith(".txt"):
            loaded = TextLoader(documento, encoding='utf-8').load()
            lista.append(loaded)
        elif documento.endswith(".csv"):
            loaded = CSVLoader(file_path=documento).load()
            lista.append(loaded)
        else:
            loaded = PyPDFLoader(documento).load()
            lista.append(loaded)
    return lista
    

def connect_bv():
    vector_store = Chroma(
        collection_name='banco_vetorial',
        embedding_function=embedding_model,
        persist_directory="./meu_banco_vetorial"
    )
    return vector_store

if not os.path.exists("./meu_banco_vetorial"):
    print ("O diretório './meu_banco_vetorial' não existe... realizando a indexação")
    texto_completo_lido= ler_docs(lista_documentos)
    divide_texto = divide_texto(texto_completo_lido)
    banco_vetorial(divide_texto)
else:
    print ("O diretório './meu_banco_vetorial' já existe. Pulando a criação do banco vetorial.")

db = connect_bv()

query = "Qual o preço do top faixa de cor preto e tamanho M?"

retorno = db.similarity_search(query, k=1)

print(retorno)


