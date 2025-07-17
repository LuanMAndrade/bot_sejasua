from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from main import run_chatbot

load_dotenv()

EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")


app = FastAPI()
conversas = {}
@app.post("/webhook")
async def webhook_receiver(request: Request):
    data = await request.json()
    print(f'Dados recebidos: {data}')
    sender = data["data"]["key"]["remoteJid"]
    message = data["data"]["message"]["conversation"]

    if sender == '5521980330995@s.whatsapp.net':

        # Chatbot recebe a mensagem e o remetente e devolve se está sendo solicitada uma imagem e a resposta em JSON
        payload, url = run_chatbot(message, sender)

        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            print("Resposta enviada:", response.status_code, response.text)

        return {"status": "ok"}