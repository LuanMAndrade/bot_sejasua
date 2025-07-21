from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from src.filtros_crm import filtrar_variacoes

# Carregar as chaves APIs presentes no arquivo .env
load_dotenv()
# --------------------------------------------------------------------------------

# Instanciar um chatmodel para comunicarmos com os modelos LLMs
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

# --------------------------------------------------------------------------------
# Criando o classificador da pergunta de entrada do usuário:
class ClassificaEntrada(BaseModel):
    opcao: dict = Field(description="""Defina um dicionário python onde as chaves serão 'categoria', 'cor', 'tamanho' e os valores devem ser somente um item dentre os listados a seguir
categoria: (Shorts, Top's, Calças, Conjuntos, Blusas, Casaco, Moda Praia, Macaquinho)
cor: (Amarelo, Vinho, Azul, Azul Claro, Azul Marinho, Vermelho, Branca, Rosê, Lavanda, Verde, Azul Piscina, Bege, Café, Caramelo, Chumbo, Cinza, Creme, Laranja, Lavanda, Lilás, Preto, Marrom, Rosa, Mostarda, Nude, Rosa Claro, Roxo, Terra Cota, Verde Militar, Verde Neon, Neon).
tamanho: (P, M, G, Único).

O valor deve ser escrito exatamente igual a escrita do item escolhido                        
Caso somente tenha sido informado algumas características, mesmo que somente uma, retorne apenas as opções referentes às caracteristicas que foram informadas""")



# Criando o parser estruturado
parser_classifica = PydanticOutputParser(pydantic_object=ClassificaEntrada)


# Criando o ChatPromptTemplate que solicitará ao LLM que ele classifique a entrada do usuário:
sys_prompt_rota = """Você é um especialista em identificar quais as características do produto que a cliente tem interesse.
preste atenção ao histórico da conversa quando você for realizar a identificação,
pois ela pode ser com base no contexto histórico. 

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


sys_prompt = """Você é uma atendente de loja de roupas de moda fitness feminina e moda praia.
As opções que correspondem ao produto que a cliente quer são: {filtro}.
É interessante que você passe as informações mais importantes que estiverem na descrição, caso haja"""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])


def monta_input(x):
    categoria = x.opcao.get("categoria", None)
    cor = x.opcao.get("cor", None)
    tamanho = x.opcao.get("tamanho", None)
    tipo = x.opcao.get("detalhe", None)

    print(f'Categoria: {categoria}, Cor: {cor}, Tamanho: {tamanho}, tipo {tipo}')

    retorno_produto = filtrar_variacoes(categoria_filtro = categoria, cor_filtro=cor, tamanho_filtro= tamanho, tipo_filtro= tipo)
    print(f'retorno_produto: {retorno_produto}')

    return {
        "input": f"Quero ver as opções de produtos",
        "history": [],
        "filtro": retorno_produto
    }




classificacao_chain = rota_prompt_template | model | parser_classifica
filtro_crm = RunnableLambda(monta_input)
resposta_chain = prompt_template | model | StrOutputParser()
chain = classificacao_chain | filtro_crm | resposta_chain
