from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from qdrant import chama_qdrant
from langchain_core.tools import tool
from typing import Annotated
from dotenv import load_dotenv
import json
import os

load_dotenv()

MODEL = os.getenv("MODEL")
cores = os.getenv("CORES")
tamanhos = os.getenv("TAMANHOS")
categorias = os.getenv("CATEGORIAS")
nomes = os.getenv("NOMES")



@tool

def rag(query: Annotated[str, "Utiliza a query da cliente para buscar produtos relevantes no estoque."]):
    """Realiza uma busca híbrida, utilizando busca direta e busca por contexto e retorna os produtos mais relevantes de acordo com a demanda da cliente."""
    llm = ChatOpenAI(model=MODEL)
    vectorstore = chama_qdrant("teste")
    metadata_field_info = [
        AttributeInfo(
            name="Cor",
            description=f"Cor do produto. Um dentre estes: {cores}",
            type="string",
        ),
        AttributeInfo(
            name="Tamanho",
            description=f"Tamanho do produto. Um dentre estes: {tamanhos}",
            type="string",
        ),
        AttributeInfo(
            name="Preço",
            description="Preço do produto",
            type="integer",
        ),
        AttributeInfo(
            name="id",
            description="ID do produto",
            type="integer",
        ),
        AttributeInfo(
            name="Nome",
            description=f"Nome do produto. Use sempre busca parcial (contém) para este campo. Um dentre estes: {nomes}",
            type="string",
        ),
        AttributeInfo(
            name="Tipo",
            description="tipo do produto: variation ou variable",
            type="string",
        ),
        AttributeInfo(
            name="Link das imagens",
            description="links das imagens do produto",
            type="string",
        ),
        AttributeInfo(
            name="Estoque",
            description="quantidade em estoque do produto",
            type="integer",
        ),
        AttributeInfo(
            name="Categoria",
            description=f"Categoria do produto. Um dentre esses: {categorias}",
            type="string",
        ),
    ]

    document_content_description = "Breve descrição do produto"
    retriever = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        document_content_description,
        metadata_field_info
    )

    response = retriever.invoke(query)
    lista_respostas = []

    for doc in response:
        metadados = doc.metadata
        descricao_json = json.loads(doc.page_content)
        descricao = descricao_json.get("Descrição", "")
        resposta = f"Nome: {metadados.get("Nome")}\n'Categoria': {metadados.get("Categoria")}, Tamanho: {metadados.get('Tamanho')} Cor: {metadados.get("Cor")}, Estoque: {metadados.get("Estoque")}, Links das imagens:{metadados.get("Links das imagens")} Preço: {metadados.get("Preço")}\nDescrição: {descricao}"
        lista_respostas.append(resposta)
        print(resposta)


    return lista_respostas