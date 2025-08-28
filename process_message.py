from congelamento import congelamento
from message_history import init_db
import redis.asyncio as redis
from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from graph import chat_graph
from langchain_core.messages import HumanMessage
import base64
from openai import OpenAI
import random

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

BUFFER_TTL = 1  # segundos

async def process_message(data, redis_client):
    print(f'Dados recebidos: {data}', flush= True)
    init_db()

    if "@lid" in data["data"]["key"]["remoteJid"]:
       sender = data["data"]["key"]["senderPn"]
    else:
       sender = data["data"]["key"]["remoteJid"]

    message_data = data["data"].get("message", {})
    nome = data["data"].get("pushName", "")

    # _________________________________________________________________________
    # # Pausa no atendimento caso o humano assuma

    pausou = congelamento(data, sender)
    if pausou:
        return pausou
    
    #__________________________________________________________________________
    # Delay no recebimento para juntar mensagens fracionadas do cliente
    if "audioMessage" in message_data:
        base64_audio = data["data"]["message"].get("base64")
        with open("audio.ogg", "wb") as f:
            f.write(base64.b64decode(base64_audio))

        client = OpenAI()
        audio_file= open("/root/chatbots/bot_sejasua/Chatbot/audio.ogg", "rb")

        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=audio_file
        )

        message = transcription.text

    elif "conversation" in message_data:

        message = message_data["conversation"]

    else:
        return None

    # 2️⃣ Adiciona mensagem no buffer
    buffer_key = f"ram:{sender}"
    current_text = await redis_client.get(buffer_key) or ""
    new_text = f"{current_text}\n{message}".strip()
    await redis_client.setex(buffer_key, BUFFER_TTL+1, new_text)
    

    # 3️⃣ Espera o tempo do buffer para ver se chegam mais mensagens
    await asyncio.sleep(BUFFER_TTL)

    final_text = await redis_client.get(buffer_key)

    if final_text == new_text:
        # ninguém enviou mais nada -> processa
        await redis_client.delete(buffer_key)
    else:
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
            elif tempo < 1:
                tempo = 1

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
                    "type": "text",
                    "text": parte
                    }
                url = EVOLUTION_TEXT_URL


            response = await client.post(url, json=payload, headers=headers, timeout=30)
            print("Resposta enviada:", parte, "-", response.status_code, flush= True)
            tempo = random.randint(1, 3)
            await asyncio.sleep(tempo)