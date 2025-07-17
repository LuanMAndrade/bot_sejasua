from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from memoria import get_session_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

sys_prompt = """Você é uma atendente virtual que só responde um link, sem texto nenhum adicional, nem antes do link, nem depois dele. O link é esse:\"https://anexos.tiny.com.br/erp/NzcwOTMwMjE1/1fa6d2e8d4310b33c9a11e786a999ed0.jpeg\""""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


chain = prompt_template | model | StrOutputParser()