import sqlite3
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from src.filtros_crm import filtrar_variacoes
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from data.inf_produtos import informacoes

load_dotenv()


model = ChatOpenAI(model="gpt-4o")

conn = sqlite3.connect("estoque.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
SELECT 
    Nome, 
    "Nome do atributo 1", 
    "Valores do atributo 1", 
    "Nome do atributo 2", 
    "Valores do atributo 2", 
    Descrição, 
    Preço, 
    Estoque 
FROM estoque
""")

dados = cursor.fetchall()

# Converte os dados para uma string organizada
estoque_str = ""
for row in dados:
    estoque_str += (
        f"- {row['Nome']} | "
        f"{row['Nome do atributo 1']}: {row['Valores do atributo 1']} | "
        f"{row['Nome do atributo 2']}: {row['Valores do atributo 2']} | "
        f"Descrição: {row['Descrição']} | "
        f"Preço: R${row['Preço']} | "
        f"Estoque: {row['Estoque']}\n"
    )

# Prompt para o modelo
system_prompt = f"""
Você é uma atendente de loja de moda fitness feminina. Abaixo estão as informações sobre os produtos. Só responda para a cliente informações sobre produtos em estoque.

{estoque_str}

Quando a cliente fizer uma pergunta sobre um item, responda com base nesses produtos. Não invente informações.
"""

prompt_template = ChatPromptTemplate.from_messages([('system', system_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


chain = RunnableLambda(lambda x : {**x, "informacoes": estoque_str}) |prompt_template | model | StrOutputParser()