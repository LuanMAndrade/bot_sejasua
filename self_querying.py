from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from qdrant import chama_qdrant
from langchain_core.tools import tool
from typing import Annotated
from dotenv import load_dotenv
import json
import os
from produtos import busca_atributos




load_dotenv()

MODEL = os.getenv("MODEL")

nomes, categorias, cores, tamanhos = busca_atributos()

@tool
def rag(query: Annotated[str, "Utiliza a query da cliente para buscar produtos relevantes no estoque."]):
    """Realiza uma busca híbrida, utilizando busca direta e busca por contexto e retorna os produtos mais relevantes de acordo com a demanda da cliente."""
    llm = ChatOpenAI(model=MODEL)
    vectorstore = chama_qdrant("teste1")
    metadata_field_info = [
        AttributeInfo(
            name="Cor",
            description=f"Cor do produto. Um dentre estes: {cores}. Use sempre busca parcial (contém) para este campo.",
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
            description=f"Nome do produto. Um dentre estes: {nomes}. Use sempre busca parcial (contém) para este campo. ",
            type="string",
        ),
        AttributeInfo(
            name="Tipo",
            description="Tipo do produto: variation ou variable. Use variation quando a cliente estiver procurando uma variação específica. Use variable se ela estiver querendo informações gerais, por exemplo: Quais cores tem?",
            type="string",
        ),
        AttributeInfo(
            name="Link das imagens",
            description="links das imagens do produto",
            type="string",
        ),
        AttributeInfo(
            name="Estoque",
            description="Quantidade em estoque do produto. Sempre filtre por maior que 0, a não ser que alguém fale o nome específico de um produto",
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