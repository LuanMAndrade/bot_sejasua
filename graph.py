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
from sqlite import save_message, get_history
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from langgraph.managed.is_last_step import RemainingSteps


tools = [rag, pagamento, informacoes, nao_entendi]

load_dotenv()

MODEL = os.getenv("MODEL")

model = ChatOpenAI(model=MODEL)
model_bind_tool = model.bind_tools(tools)



class AgentState(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    remaining_steps: RemainingSteps

def call_model(state: AgentState, config: RunnableConfig):
    conversation_id = config.get("configurable", {}).get("conversation_id", "default") ##
    history = get_history(conversation_id) ##
    
    sys_prompt = """Você é uma atendente de loja de moda fitness feminina que atende suas clientes pelo Whatsapp. 
    
    # Ferramentas
    Você tem acesso a ferramentas que serão explicadas abaixo. use elas sempre que necessário.
    <Ferramentas>
    1. **rag**: Esta ferramenta busca os produtos mais relevantes no estoque de acordo com o que o cliente quer.
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
    11. **NUNCA fale que vai fazer algo que você não consegue, por exemplo, tirar uma foto**

    ## Exemplos

    A seguir vou mostrar exemplos reais de conversas de uma excelente atendente da loja.

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
    
    # Formatação
    
    1. A resposta final deve vir separada em mensagens fracionadas, de forma a parecer ao máximo uma conversa natural.
    2. O simbolo para demonstrar a separação deverá ser o seguinte: '$%&$'
    3. Esse simbolo deve ser inserido ao final de cada fração de mensagem, demonstrando que após ele será iniciada uma nova fração de mensagem.
    4. Sempre que tiver algum link na resposta, ele deverá estar isolado em uma única fração de mensagem

    # Exemplo de saída esperada

    Input:
    Oi!

    Exemplo de saída esperada:
    Oi!$%&$Tudo bem?$%&$Como posso te ajudar hoje?

    """
    
    prompt_template = ChatPromptTemplate.from_messages([
    ('system', sys_prompt),
    MessagesPlaceholder(variable_name='history'),
    MessagesPlaceholder(variable_name='current_messages'),
])


    full_input = {
    "history": history,  # mensagens antigas
    "current_messages": state["messages"]  # mensagens novas
}


    # Aplica o prompt formatado
    prompt = prompt_template.invoke(full_input)

    # Chama o modelo
    response = model_bind_tool.invoke(prompt, config)
    
    return {"messages": [response]}

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls or state["remaining_steps"] <=18:
        return "save"
    else:
        return "no_ferramenta"
    
def save(state, config):
    conversation_id = config.get("configurable", {}).get("conversation_id", "default")
    save_message(conversation_id, state["messages"])


def build_chat_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("no_ferramenta", ToolNode(tools))
    workflow.add_node("save", save)

    # Fluxo de início → agent
    workflow.add_edge(START, "agent")

    # Se o agent não chamar ferramenta, encerra; senão, vai para no_ferramenta
    workflow.add_conditional_edges("agent", should_continue)

    # Depois da ferramenta, volta para agent
    workflow.add_edge("no_ferramenta", "agent")

    workflow.add_edge("save", END)

    # Compila sem checkpointer
    return workflow.compile()


chat_graph = build_chat_graph()


