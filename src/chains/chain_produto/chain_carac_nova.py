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

# Carregar as chaves APIs presentes no arquivo .env
load_dotenv()
# --------------------------------------------------------------------------------

# Instanciar um chatmodel para comunicarmos com os modelos LLMs
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature = 0)
model = ChatOpenAI(model="gpt-4o", temperature=0)
# --------------------------------------------------------------------------------

# Criando o classificador da pergunta de entrada do usuário:
class ClassificaEntrada(BaseModel):
    opcao: dict = Field(description="""Defina um dicionário python onde as chaves serão 'categoria', 'cor', 'tamanho', 'nome', 'descricao' e 'tag' e os valores devem estar
dentre os listados a seguir:
                        
cores: Amarelo, Vinho, Azul, Azul Claro, Azul Marinho, Vermelho, Branca, Rosê, Lavanda, Verde, Azul Piscina, Bege, Café, Caramelo, Chumbo, Cinza, Creme, Laranja, Lavanda, Lilás, Preto, Marrom, Rosa, Mostarda, Nude, Rosa Claro, Roxo, Terra Cota, Verde Militar, Verde Neon, Neon
tamanhos: 'P', 'M', 'G', 'Único'
categorias: 'Shorts', 'Top's', 'Calças', 'Conjuntos', 'Blusas', 'Casaco', 'Moda Praia', 'Macaquinho'
tags: 'Corrida
nomes: 'GARRA', 'GEOMÉTRICO', 'REFLETIVO', 'SNAKE', 'TRAINING', 'LEGGING', 'EVOLUTION', 'JULIANA', 'LANA', 'NARA', 'TERRA','3D', 'ATHLETIC', 'GEOMÉTRICO', 'FREE', 'GARRA', 'MOVIMENTO', 'RECORTES', 'SNAKE', 'TULE', 'FAIXA', 'BRUNA', 'ROCKBOX', 'RUNNER', 'MOVIMENTO', 'NARA', 'FUT', 'RECORTES', 'ALESSANDRA', 'NINA', 'ADRIANA', 'CAROLINA', 'AGNE', 'CLEAN', 'ENVOLVE', 'GLAMOUR', 'GLAMOUR', 'HOT', 'BASIC', 'FITA', 'CARIBE', 'CARIBE', 'SLIM', 'ATHLETIC', 'TRIATHLON', 'CLAUDINHA', 'PRISCILA', 'AUDAZ', 'DRIKA', 'OUSADIA', 'ÚNICA', 'LIBERDADE', 'ARO', 'ÁGUA', 'ATLANTA', 'SHINE', 'EVOLUTION', 'FERNANDA', 'SOUL', 'STARFIT', 'ATOMIC', 'LANA', 'Fit', 'JAÍNNE', 'OUSADIA', 'DRIKA', 'SPEED', 'PACE', 'ROCKBOX', 'Audaz' 
              
Caso somente tenha sido informado algumas características, mesmo que somente uma, retorne apenas as opções referentes às caracteristicas que foram informadas.
na chave 'descricao' o valor será qualquer descrição que for identificada que a cliente deu a peça, mas somente a palavra mais importante dessa descrição""")



# Criando o parser estruturado
parser_classifica = PydanticOutputParser(pydantic_object=ClassificaEntrada)


# Criando o ChatPromptTemplate que solicitará ao LLM que ele classifique a entrada do usuário:
sys_prompt_rota = """Você é um especialista em identificar quais as características do produto que a cliente tem interesse.
preste atenção ao histórico da conversa quando você for realizar a identificação,
pois ela pode ser com base no contexto histórico. 
Você presta atenção se a cliente dá alguma descrição do que procura na peça, ou fala um nome específico de uma peça, caso isso aconteça, você acrescenta o que foi dito como valor no dicionário python.

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
É interessante que você passe as informações mais importantes que estiverem na descrição, caso haja.
Se não houver opções que correspondem ao produto que a cliente quer, responda educadamente que não tem as opções que ela quer em estoque
e pergunte se não há alguma outra coisa que ela deseja. 
Além disso, você sempre envia somente no final da mensagem, todos os links, separados, que estiverem em Imagens e Imagens_extras"""

prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}"),
                                                    ('system', "{link}")
                                                    ])


def monta_input(x):
    categoria = x.opcao.get("categoria", None)
    cor = x.opcao.get("cor", None)
    tamanho = x.opcao.get("tamanho", None)
    tag = x.opcao.get("tag", None)
    nome = x.opcao.get("nome", None)
    descricao = x.opcao.get("descricao", None)

    print(f'Categoria: {categoria}, Cor: {cor}, Tamanho: {tamanho}, Tag: {tag}, Nome: {nome}, Descrição {descricao}')

    retorno_produto = filtrar_variacoes(categoria_filtro = categoria, cor_filtro=cor, tamanho_filtro= tamanho, tag_filtro= tag, nome_filtro=nome, descricao_filtro=descricao)

    return {
        "input": f"Quero ver as opções de produtos",
        "history": [],
        "filtro": retorno_produto}

classificacao_chain = RunnableLambda(lambda x : {**x, "informacoes": informacoes}) | rota_prompt_template | model | parser_classifica
filtro_crm = RunnableLambda(monta_input)
resposta_chain = RunnableLambda(lambda x : {'link': (item['Imagens'] for item in x['filtro'] ), 'input': x['input'], 'history': x['history'], 'filtro': x['filtro'] }) | prompt_template | model | StrOutputParser()
chain = classificacao_chain | filtro_crm | resposta_chain
