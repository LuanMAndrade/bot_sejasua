from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from graph import chat_graph
from langchain_core.messages import HumanMessage
from sqlite import init_db
import redis.asyncio as redis


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



redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6380)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

BUFFER_TTL = 30  # segundos
LOCK_TTL = 300   # segundos


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
async def process_message(data):
    init_db()
    print(f'Dados recebidos: {data}')

    if "@lid" in data["data"]["key"]["remoteJid"]:
       sender = data["data"]["key"]["senderPn"]
    else:
       sender = data["data"]["key"]["remoteJid"]

    message_data = data["data"].get("message", {})
    nome = data["data"].get("pushName", "")

    if sender == '557181238313@s.whatsapp.net':
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
            # message_id = data["data"]["key"]["id"]
            # lock_key = f"lock:{sender}:{message_id}"
            # print(f"Lock key: {lock_key}")
            # if await redis_client.exists(lock_key):
            #     print(f"Mensagem {message_id} já processada. Ignorando.")
            #     return {"status": "duplicada"}
            # await redis_client.setex(lock_key, LOCK_TTL, 1)
            

            # 2️⃣ Adiciona mensagem no buffer
            buffer_key = f"ram:{sender}"
            current_text = await redis_client.get(buffer_key) or ""
            new_text = f"{current_text}\n{message}".strip()
            await redis_client.setex(buffer_key, BUFFER_TTL+1, new_text)
            print(1)
            

            # 3️⃣ Espera o tempo do buffer para ver se chegam mais mensagens
            await asyncio.sleep(BUFFER_TTL)
            print("Aqui está o problema")

            final_text = await redis_client.get(buffer_key)
            print("Ou aqui??")
            print(f"Final text: {final_text}\n New text: {new_text}")
            if final_text == new_text:
                # ninguém enviou mais nada -> processa
                await redis_client.delete(buffer_key)
                print(f"Processando mensagem final: {final_text}")
            else:
                print("Ainda recebendo partes da mensagem, aguardando.")
                return {"status": "aguardando"}

        #__________________________________________________________________________

            config = {"configurable": {"conversation_id": sender}}
            respostas = chat_graph.invoke({"messages": [HumanMessage(content=final_text)],}, config=config)
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
                    
                # Loop para que as repostas saiam separadas
                for parte in lista_de_mensagens:
                    parte = parte.strip()

                     # configurando o "Digitando..."
                
                    typing_url = EVOLUTION_PRESENCE_URL 
                    tempo = len(parte)*1000/17
                    if tempo > 10:
                        tempo = 10
                    print(f"LEN {len(parte)}")

                    typing_payload = {
                        "number": sender,
                        'delay':tempo,
                        'presence':'composing'}

                    # "Digitando..."
                    await client.post(typing_url, json=typing_payload, headers=headers, timeout=30)

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
                    await asyncio.sleep(2)



async def whatsapp(data):
    message_id = data["data"]["key"]["id"]
    lock_key = f"lock:{message_id}"
    if await redis_client.exists(lock_key):
        print(f"Mensagem {message_id} já processada. Ignorando.")
        return {"status": "ok"}
    
    await redis_client.setex(lock_key, LOCK_TTL, 1)
    # Cria tarefa assíncrona
    asyncio.create_task(process_message(data))

    # Retorna imediatamente para evitar eco
    return {"status": "ok"}
    