from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from graph import chat_graph
from langchain_core.messages import HumanMessage
from sqlite import init_db

load_dotenv()

INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
WC_WEBHOOK_SECRET = os.getenv("WC_WEBHOOK_SECRET")
PORTA = os.getenv("PORTA")

NUMERO_BACKUP = os.getenv('NUMERO_BACKUP')

# Link para texto
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

# Link para o "digitando..."
EVOLUTION_PRESENCE_URL_TEMPLATE = os.getenv("EVOLUTION_PRESENCE_URL")
EVOLUTION_PRESENCE_URL = EVOLUTION_PRESENCE_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

# Link para midia
EVOLUTION_MEDIA_URL_TEMPLATE = os.getenv("EVOLUTION_MEDIA_URL")
EVOLUTION_MEDIA_URL = EVOLUTION_MEDIA_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

#Conversas pausadas pelo atendimento humano
pausas = {}

# Memória para juntar as mensagens fracionadas do cliente
ram = {}

#___________________________________________________________________________________________________________________

app = FastAPI()
@app.post("/webhook")
async def webhook_receiver(request: Request):
    data = await request.json()

    if 'event' in data:
        return await whatsapp(data)
    elif 'id' in data:
        return await woocommerce(data)
    else:
        print('MENSAGEM NÃO VEIO DO WHATSAPP NEM DO WEBHOOK')
    


# WEBHOOK WOOCOMMERCE PARA ATUALIZAÇÃO DO ESTOQUE

async def woocommerce(data): 
    id = data.get("id")
    estoque = data.get("stock_quantity")

    conn = sqlite3.connect('banco_dados.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET estoque = ? WHERE id = ? ", (estoque, id)) 
    conn.commit()
    conn.close()

    print(f'Atualização de estoque. Produto: {id}. Estoque:{estoque}')
    return {"ok": True}


# Webhook Whatsapp 

async def whatsapp(data):
    init_db()

    print(f'Dados recebidos: {data}')

    if "@lid" in data["data"]["key"]["remoteJid"]:
       sender = data["data"]["key"]["senderPn"]
    else:
       sender = data["data"]["key"]["remoteJid"]

    message_data = data["data"].get("message", {})
    nome = data["data"].get("pushName", "")

    if sender == '5521980330995@s.whatsapp.net':
        # _________________________________________________________________________
        # # Pausa no atendimento caso o humano assuma

        # if data["data"]["key"]["fromMe"] == True and data['data']['source'] == 'ios':  
        #     pausas[sender] = asyncio.get_event_loop().time() + 3600
        #     print(f"PAUSA ativada para {sender} por {3600} segundos")
        #     return {"status": f"chatbot pausado para {sender}"}
        
        # agora = asyncio.get_event_loop().time()
        # if sender in pausas:
        #     if agora < pausas[sender]:
        #         print(f"{sender} ainda em pausa. Ignorando chatbot.")
        #         return {"status": f"em pausa até {pausas[sender] - agora:.1f}s"}
        #     else:
        #         del pausas[sender]  # tempo expirou
        #__________________________________________________________________________
        # Delay no recebimento para juntar mensagens fracionadas do cliente

        if "conversation" in message_data:
            message = message_data["conversation"]
            if ram.get(sender):
                ram[sender] += f'\n{message}'
            else:
                ram[sender] = message
            messages_antes = ram[sender]
            
            await asyncio.sleep(1)
            
            if ram[sender] == messages_antes:
                message = ram[sender]
                ram.pop(sender, None)
            else:
                return {"status": "mensagem fracionada, aguardando mais partes"}

        #__________________________________________________________________________

            config = {"configurable": {"conversation_id": sender}}
            respostas = chat_graph.invoke({"messages": [HumanMessage(content=message)],}, config=config)
            mensagens = respostas["messages"]
            ultima_resposta = mensagens[-1]  # AIMessage
            lista_de_mensagens = ultima_resposta.content
            lista_de_mensagens = lista_de_mensagens.split("$%&$")
            opcao = 1

            headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }

            async with httpx.AsyncClient() as client:
                
                # configurando o "Digitando..."
                typing_payload = {
                    "number": sender,
                    'delay':500,
                    'presence':'composing'}
                
                typing_url = EVOLUTION_PRESENCE_URL 
                
                # Loop para que as repostas saiam separadas
                for parte in lista_de_mensagens:
                    parte = parte.strip()
                    
                    # "Digitando..."
                    await client.post(typing_url, json=typing_payload, headers=headers, timeout=10)

                    # Se for link de imagem vai nesse payload
                    if any(ext in parte for ext in ['.png', '.jpg', '.jpeg', 'webp']):
                        payload = {
                            "number": sender,
                            "mediatype": "image",
                            "caption": "",
                            "media": parte
                            }
                        url = EVOLUTION_MEDIA_URL
                    
                    # Se não entendeu o cliente ou for pagamento vai nesse payload
                    elif opcao == 4 or opcao == 3:
                        payload = {
                            "number": f'{NUMERO_BACKUP}@s.whatsapp.net',
                            "text": parte
                            }
                        url = EVOLUTION_TEXT_URL
                    
                    # Atendimento normal com texto vai nesse payload
                    else:
                        payload = {
                            "number": sender,
                            "text": parte
                            }
                        url = EVOLUTION_TEXT_URL


                    response = await client.post(url, json=payload, headers=headers)
                    print("Resposta enviada:", parte, "-", response.status_code)
                    await asyncio.sleep(1)