from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
from src.roteamento_principal import run_chatbot
import asyncio
import sqlite3

load_dotenv()

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
WC_WEBHOOK_SECRET = os.getenv("WC_WEBHOOK_SECRET")
EVOLUTION_TEXT_URL= os.getenv('EVOLUTION_TEXT_URL')
EVOLUTION_MEDIA_URL= os.getenv('EVOLUTION_MEDIA_URL')
EVOLUTION_PRESENCE_URL= os.getenv('EVOLUTION_PRESENCE_URL')

pausas = {}

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

ram = {}

async def whatsapp(data):
    global ram

    print(f'Dados recebidos: {data}')
    
    sender = data["data"]["key"]["remoteJid"]
    message_data = data["data"].get("message", {})
    nome = data["data"]["pushName"]

    if data["data"]["key"]["fromMe"] == True and data['data']['source'] == 'ios':  
        pausas[sender] = asyncio.get_event_loop().time() + 7200
        print(f"PAUSA ativada para {sender} por {7200} segundos")
        return {"status": f"chatbot pausado para {sender}"}
    
    agora = asyncio.get_event_loop().time()
    if sender in pausas:
        if agora < pausas[sender]:
            print(f"{sender} ainda em pausa. Ignorando chatbot.")
            return {"status": f"em pausa até {pausas[sender] - agora:.1f}s"}
        else:
            del pausas[sender]  # tempo expirou

    if "conversation" in message_data:
        message = message_data["conversation"]
        if ram.get(sender):
            ram[sender] += f'\n{message}'
        else:
            ram[sender] = message
        messages_antes = ram[sender]
        
        await asyncio.sleep(10)
        
        if ram[sender] == messages_antes:
            message = ram[sender]
            ram.pop(sender, None)
        else:
            return

        if sender == '557181238313@s.whatsapp.net':
            print(message)
            

            respostas, opcao = run_chatbot(message, sender, nome)

            headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }

            async with httpx.AsyncClient() as client:
                typing_payload = {
                    "number": sender,
                    'delay':5000,
                    'presence':'composing'}
                
                typing_url = EVOLUTION_PRESENCE_URL  # mesma URL para texto

                for parte in respostas['lista_respostas']:
                    await client.post(typing_url, json=typing_payload, headers=headers, timeout=10)
                    if 'http' in parte:
                        payload = {
                            "number": sender,
                            "mediatype": "image",
                            "caption": "",
                            "media": parte
                            }
                        url = EVOLUTION_MEDIA_URL
                    elif opcao == 4 or opcao == 5:
                        payload = {
                            "number": '557181238313@s.whatsapp.net',
                            "text": parte
                            }
                        url = EVOLUTION_TEXT_URL

                    else:
                        payload = {
                            "number": sender,
                            "text": parte
                            }
                        url = EVOLUTION_TEXT_URL


                    response = await client.post(url, json=payload, headers=headers)
                    print("Resposta enviada:", parte, "-", response.status_code)
                    
                    await asyncio.sleep(2.5)  # espera entre mensagens