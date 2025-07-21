from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.memoria import get_session_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Verifica se a mensagem é uma solicitação de imagem criando um outro modelo que só le a ultima mensagem dita, ao inves de todo o histórico
def e_imagem(message, model):
    response = model.invoke([SystemMessage(content="Você é um assistente de IA verifica se estão te pedindo uma imagem, foto ou algo correlato, e responde unica e exclusivamente com 'TRUE' ou 'FALSE'."),
                             HumanMessage(content=message)])
    if response.content == 'TRUE':
        return True
    else:
        return False

# def chatbot_response(input,sender, model):
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
 
sys_prompt = """Você é uma atendente de loja de roupas de moda fitness feminina. Se alguém te pedir uma imagem, foto ou algo correlato, de um dos produtos da loja,
    responda exatamente este link: \"https://anexos.tiny.com.br/erp/NzcwOTMwMjE1/1fa6d2e8d4310b33c9a11e786a999ed0.jpeg\",
    sem nenhum texto anterior ou posterior."""


prompt_template = ChatPromptTemplate.from_messages([('system', sys_prompt),
                                                    MessagesPlaceholder(variable_name='history'),
                                                    ('human', "{input}")
                                                    ])

contexto = 'A loja abre às 10:00 e fecha às 18:00, de segunda a sexta-feira. No sábado, abre às 10:00 e fecha às 14:00.'

chain_teste = prompt_template | model | StrOutputParser()

    # runnable_with_history = RunnableWithMessageHistory(
    #     chain,
    #     get_session_history, 
    #     input_messages_key='input', 
    #     history_messages_key='history',
    #     )

    # result = runnable_with_history.invoke({'input': input,
    #                                        'contexto': contexto},
    #                                     config={'configurable':{'session_id': sender}})

    # is_image = e_imagem(input, model)

    # # Se for solicitado uma imagem, retorna o payload com a URL da imagem
    # # Se não, retorna o payload com o texto
    # if is_image:
    #     payload = {
    #             "number": sender,
    #             "mediatype": "image",
    #             "caption": "Veja o produto!",
    #             "media": result
    #         }
    # else:
        
    #     payload = {
    #             "number": sender,
    #             "text": result,
    #         }
    

    # return chain

