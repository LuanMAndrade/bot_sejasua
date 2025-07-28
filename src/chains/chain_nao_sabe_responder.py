from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
#model = ChatOpenAI(model="gpt-4o")

sys_prompt = """Você sempre responde assim: "Eu não consegui entender a mensagem {input} do {nome}." Exatamente assim, sem mudar nada"""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    ('human', "{input}")
                                                    ])


chain = prompt_template | model | StrOutputParser()