from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
from src.main import run_chatbot
import asyncio

load_dotenv()

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

pausas = {}

app = FastAPI()

@app.post("/webhook")
async def webhook_receiver(request: Request):
    data = await request.json()
    print(f'Dados recebidos: {data}')
    
    sender = data["data"]["key"]["remoteJid"]
    message_data = data["data"].get("message", {})

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

        if sender == '5521980330995@s.whatsapp.net':

            payload, url = run_chatbot(message, sender)

            headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                print("Resposta enviada:", response.status_code, response.text)

            return {"status": "ok"}