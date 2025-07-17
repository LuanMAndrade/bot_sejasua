from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os


embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
documento_teste = "C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\inf_loja.txt"


def divide_texto(documentos, tamanho_maximo=90):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho_maximo, length_function=len, chunk_overlap=0)
    documents = text_splitter.split_documents(documentos)
    return documents

def banco_vetorial(documents):
    Chroma.from_documents(
        documents,
        collection_name='banco_vetorial',
        embedding=embedding_model,
        persist_directory="./meu_banco_vetorial"
    )


def ler_docs(documentos):
    loader = TextLoader(documentos, encoding='utf-8')
    return loader.load()

def connect_bv():
    vector_store = Chroma(
        collection_name='banco_vetorial',
        embedding_function=embedding_model,
        persist_directory="./meu_banco_vetorial"
    )
    return vector_store

if not os.path.exists("./meu_banco_vetorial"):
    print ("O diretório './meu_banco_vetorial' não existe... realizando a indexação")
    texto_completo_lido= ler_docs(documento_teste)
    divide_texto = divide_texto(texto_completo_lido)
    banco_vetorial(divide_texto)
else:
    print ("O diretório './meu_banco_vetorial' já existe. Pulando a criação do banco vetorial.")

db = connect_bv()

query = "Qual o horário de funcionamento da loja?"

retorno = db.similarity_search(query, k=2)



