from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from utils import config

load_dotenv()


model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature = 0)
model = ChatOpenAI(model="gpt-4o", temperature=0)


sys_prompt = """Você é uma atendente de loja de roupas de moda fitness feminina. Você NUNCA inventa informação. 
Caso a cliente pergunte algo que você não saiba, você pede para ela detalhar melhor o que quer.
Você responde ela baseada nos produtos de interesse dela, que são {produtos}.
Se for enviar algum link, você sempre envia no final da mensagem"""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


def print_produtos(x):
    print(config.produtos_interesse)
    return x

chain =  RunnableLambda(lambda x : {**x, "produtos": config.produtos_interesse})|RunnableLambda(print_produtos) | prompt_template | model | StrOutputParser()