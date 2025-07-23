from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
model = ChatOpenAI(model="gpt-4o")

documento = "C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\data\\inf_loja.txt"
informacoes = TextLoader(documento, encoding='utf-8').load()

sys_prompt = """Você é uma atendente de loja de roupas de moda fitness feminina. 
Caso te perguntem informações sobre a loja, responda baseada nessas informações {informacoes}"""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


chain = RunnableLambda(lambda x : {**x, "informacoes": informacoes}) |prompt_template | model | StrOutputParser()