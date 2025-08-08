from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import OpenAIEmbeddings
from langchain.callbacks.tracers import ConsoleCallbackHandler
from langchain_community.vectorstores import Qdrant
from langchain_openai import ChatOpenAI
from qdrant import chama_qdrant, busca_produtos
from langchain_core.tools import tool
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()


@tool
def rag(query: Annotated[str, "Utiliza a demanda da cliente para buscar produtos relevantes no estoque"]):
    """Realiza uma busca no estoque e retorna os produtos mais relevantes de acordo com a demanda da cliente."""
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    vectorstore = chama_qdrant("teste")


    metadata_field_info = [
        AttributeInfo(
            name="Cor",
            description="Filtra pela cor da peça",
            type="string",
        ),
        AttributeInfo(
            name="Tamanho",
            description="Filtra pelo tamanho da peça",
            type="string",
        ),
        AttributeInfo(
            name="Preço",
            description="Filtra pelo preço da peça",
            type="float",
        ),
        AttributeInfo(
            name="id",
            description="Filtra pelo ID da peça",
            type="integer",
        ),
        AttributeInfo(
            name="Nome",
            description="Filtra pelo nome da peça",
            type="string",
        ),
        AttributeInfo(
            name="Tipo",
            description="Filtra pelo tipo da peça (variação ou variável)",
            type="string",
        ),
        AttributeInfo(
            name="Link das imagens",
            description="Filtra pelo link das imagens da peça",
            type="string",
        ),
        AttributeInfo(
            name="Estoque",
            description="Filtra pela quantidade em estoque da peça",
            type="integer",
        ),
        AttributeInfo(
            name="Categoria",
            description="Filtra pela categoria da peça",
            type="string",
        ),
    ]

    document_content_description = "Breve descrição da peça"
    retriever = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        document_content_description,
        metadata_field_info
    )

    response = retriever.invoke("query")

    return response