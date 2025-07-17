from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from memoria import get_session_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

sys_prompt = """Você informa a dona da loja, Ana Clara a solicitação de uma cliente e que você não sabe como responder."""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


chain = prompt_template | model | StrOutputParser()