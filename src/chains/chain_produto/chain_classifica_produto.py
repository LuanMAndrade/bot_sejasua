from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Carregar as chaves APIs presentes no arquivo .env
load_dotenv()
# --------------------------------------------------------------------------------

# Instanciar um chatmodel para comunicarmos com os modelos LLMs
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

# --------------------------------------------------------------------------------
# Criando o classificador da pergunta de entrada do usuário:
class ClassificaEntrada(BaseModel):
    opcao: int = Field(description="Defina 1 se a cliente ainda não falou qual tipo de produto ele quer, por exemplo: Tamanho, cor, categoria, finalidade, etc. \
Defina 2 se a cliente definiu algum tipo de característica do produto que a interessa, que ela ainda não tenha dito antes.\
Defina 3 se a cliente já definiu algum tipo de característica do produto que a interessa, mas na última mensagem não deu nenhuma característica nova.")

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

chain_de_roteamento = rota_prompt_template | model | parser_classifica