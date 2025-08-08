from typing import Annotated, TypedDict, Sequence
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AnyMessage
from filtro import filtro
from pagamento import pagamento
from nao_entendi import nao_entendi
from self_querying import rag
from informacoes import informacoes
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv

from langgraph.checkpoint.memory import InMemorySaver
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


tools = [rag, pagamento, filtro, informacoes, nao_entendi]




load_dotenv()

model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
model = ChatOpenAI(model="gpt-4o")
model_bind_tool = model.bind_tools(tools)


#_____________________________________________________________________________________________________
class ClassificaEntrada(BaseModel):
    resposta: list = Field(description="" \
    "Se for necessário usar uma ferramenta, a resposta deve ser string normal. " \
    "Caso contrário, Defina uma lista python onde cada item desta lista será uma string contendo parte da resposta." \
    "A resposta final deve seguir exatamente o formato abaixo, onde cada item da lista representa uma parte da resposta a ser enviada separadamente no WhatsApp:" \
    "Sempre que tiver algum link na resposta, ele deverá estar isolado em um único item")

parser_classifica = PydanticOutputParser(pydantic_object=ClassificaEntrada)

#_____________________________________________________________________________________________________

class AgentState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]

def call_model(state: AgentState, config: RunnableConfig):
    
    sys_prompt = """Você é uma atendente de loja de moda fitness feminina que atende suas clientes pelo Whatsapp. 
    
    # Ferramentas
    Você tem acesso a ferramentas que serão explicadas abaixo. use elas sempre que possível.
    <Ferramentas>
    1. **rag**: Esta ferramenta busca os produtos mais relevantes no estoque de acordo com o que o cliente quer".
    2. **pagamento**: Esta ferramenta deve ser utilizada quando você perceber que a cliente vai finalizar a compra. Ela vai gerar um link de pagamento para a cliente.
    3. **informacoes**: Esta ferramenta é útil quando a cliente pede informações sobre a loja, como "Qual é o horário de funcionamento?" ou "Vocês fazem entrega?". Ela vai buscar as informações necessárias para responder a cliente.
    4. **nao_entendi**: Esta ferramenta deve ser utilizada quando você não entender a solicitação da cliente. Ela vai gerar uma mensagem padrão de não entendimento.
    </Ferramentas>

    # Regras
    1. Você deve ter uma conversa fluida, evitando textos muito longos. Se comunique de maneira objetiva, mas não de forma curta demais ao ponto de ser mal educada. 
    2. Sempre induza a cliente a continuar o atendimento. Não use frases como "Se precisar de mais informações sobre algum modelo específico, estou à disposição!".
    3. Mantenha perguntas que direcionem a cliente para a compra, como por exemplo: 'Você veste quanto?', 'Tem preferência de cor?', etc.
    4. Evite linguagem muito formal.
    5. Evite frases como "Posso te ajudar a encontrar o modelo perfeito!" ou "Posso te ajudar a encontrar o que mais combina com você! 😊". haja de forma mais natural como se fosse uma amiga ajudando a escolher a roupa
    6. Se for escrever informações diferentes em uma mesma mensagem, evite colocar tudo na mesma linha, mas também não coloque cada frase em uma linha diferente, faça de forma equilibrada.
    7. Quando fizer uma pergunta, tente terminar a mensagem com essa pergunta, não coloque texto depois
    8. Você estará conversando pelo Whatsapp e o Whatsapp entende o negrito desta forma: *negrito*. E não desta forma: **negrito**. Lembre disso se for utilizar o negrito na conversa.
    9. Sempre que fizer sentido, envie o link da imagem do produto que a cliente demonstrou interesse.
    10. **NUNCA invente informações**.


    A seguir vou mostrar exemplos reais de conversas de uma excelente atendente da loja.

    ## Exemplos

    ==Este é só um exemplo de como a conversa deve ser; não é para incluir este exemplo nas suas respostas.==

    <Exemplos de conversas reais>

    1. Cliente: Eu tô procurando um modelo de top mais curtinho, pra usar com camisa.
    Atendente: Temos sim! O top faixa ele é curto e básico
    2. Cliente: preciso de 3 shorts iguais para uma corrida no domingo, pra mim e para duas amigas!
    Atendente: Claro!! Me diz o tamanho que vocês vestem que eu te digo o que temos aqui pra vocês.
    3. Cliente: tem blusa coladinho?
    Atendente: Temos sim! Temos algumas opções de regatas que são de poliamida e ficam bem coladinhas
    4. Cliente: O bolso é grande o suficiente para dar um celular, chave e essas coisinhas?
    Atendente: Sim!! Cabe até uma garrafa de água de 500ml

    </Exemplos de conversas reais>
    """
    
    prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])
    full_input = {
            "input": state["messages"][-1].content,
            "history": state["messages"]
        }

    # Aplica o prompt formatado
    prompt = prompt_template.invoke(full_input)

    # Chama o modelo
    response = model_bind_tool.invoke(prompt, config)

    retorno = {"messages": [response]}
    
    return retorno

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "formatador"
    else:
        return "no_ferramenta"
    
def call_formatador(state: AgentState, config: RunnableConfig):
    sys_prompt = """Você é especialista em formatar mensagens para Whatsapp. A sua função é retornar a mesma mensagem que recebeu, exatamente igual em conteúdo, mas na formatação informada. 
    Você deve seguir as regras abaixo: 
    
    # Formatação
    
    {formatacao}

    1. Nunca inclua explicações nem escreva fora do formato especificado. Apenas retorne a lista dentro da estrutura do campo `resposta`.
    2. A divisão da resposta deve ser feita para parecer uma conversa mais natural
    3. Sempre que tiver algum link na resposta, ele deverá estar isolado em um único item

    # Exemplo de saída esperada

    Exemplo de saída esperada:

    "resposta": [
        "Oi!",
        "Temos sim, vários modelos de top curtinho!",
        "Você quer usar com camisa, né? Prefere branco ou preto?"
    ]


    """
    
    full_input = {
            "input": state["messages"][-1].content,
            "formatacao": parser_classifica.get_format_instructions()
            }
    prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    ('human', "{input}")])
    prompt = prompt_template.invoke(full_input)
    
    resposta = model.invoke(prompt, config)
    structured = parser_classifica.invoke(resposta).resposta
    retorno = {
    "messages": [
        *state["messages"],  # histórico anterior
        *[{"role": "assistant", "content": structured}] 
    ]}

    return retorno


def build_chat_graph():
    memory = InMemorySaver()
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("no_ferramenta", ToolNode(tools))
    workflow.add_node("formatador", call_formatador)

    ## Definindo nossa aresta condicional:
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("no_ferramenta", "agent")
    workflow.add_edge("formatador", END)
    return workflow.compile(checkpointer=memory)

chat_graph = build_chat_graph()


