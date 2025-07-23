from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
from src.roteamento_principal import run_chatbot
import asyncio
import sqlite3

load_dotenv()

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
WC_WEBHOOK_SECRET = "J~}Q%f^B#.@:J<mt]7a^=c4d_NVU]o0.0c(RI{8=,bPptHm[!@"

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


async def whatsapp(data):
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

        if sender == '557183532189@s.whatsapp.net':

            payload, url = run_chatbot(message, sender, nome)

            headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                print("Resposta enviada:", response.status_code, response.text)

            return {"status": "ok"}