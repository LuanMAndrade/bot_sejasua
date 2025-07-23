from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_openai import ChatOpenAI

# Carregar as chaves APIs presentes no arquivo .env
load_dotenv()
# --------------------------------------------------------------------------------

# Instanciar um chatmodel para comunicarmos com os modelos LLMs
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature = 0)
model = ChatOpenAI(model="gpt-4o", temperature = 0)

# --------------------------------------------------------------------------------
# Criando o classificador da pergunta de entrada do usuário:
class ClassificaEntrada(BaseModel):
    opcao: int = Field(description="Defina 1 se a pergunta do usuário solicitar informações/orientações sobre a loja ou se for uma conversa normal.\
Defina 2 se for solicitação de informação sobre produto.\
Defina 3 se estiver pedindo uma imagem.\
Defina 4 se for qualquer coisa relacionada a pagamento.\
Defina 5 se for qualquer outra coisa não relacionada anteriormente.")

# Criando o parser estruturado
parser_classifica = PydanticOutputParser(pydantic_object=ClassificaEntrada)

# Criando o ChatPromptTemplate que solicitará ao LLM que ele classifique a entrada do usuário:
sys_prompt_rota = """Você é um especialista em classificação. Você receberá perguntas do usuário e precisará classificá-las \
da melhor forma entre as opções estabelecidas.
Também preste atenção ao histórico da conversa quando você for realizar a classificação, pois durante um cadastro de \
ocorrência pode ser solicitado novas informações do usuário e a classificação pode ser com base no contexto histórico. 

\n{format_instructions}\n

Pergunta Usuário: {input}

## Historico da conversa:
{history}
"""



rota_prompt_template = ChatPromptTemplate.from_messages([
    ('system', sys_prompt_rota),
    ('human', "{input}")
]).partial(
    format_instructions=parser_classifica.get_format_instructions()
)


# Criando a Chain que vai classificar a entrada do usuário:
chain_de_roteamento = rota_prompt_template | model | parser_classifica