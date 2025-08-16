from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
import asyncio
import sqlite3
from graph import chat_graph
from langchain_core.messages import HumanMessage
from message_history import init_db
import redis.asyncio as redis
from process_message import process_message
from qdrant import cria_colecao
from qdrant_client import QdrantClient


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

SERVER_IP = os.getenv("SERVER_IP")
QDRANT_URL_TEMPLATE = os.getenv("QDRANT_URL")
QDRANT_URL = QDRANT_URL_TEMPLATE.format(SERVER_IP=SERVER_IP)


LOCK_TTL = 300   # segundos

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6380)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)


#___________________________________________________________________________________________________________________

app = FastAPI()

@app.post("/webhook")
async def webhook_receiver(request: Request):
    try:
        data = await request.json()
        print(data, flush= True)
    except Exception:
        body = await request.body()
        print("Conteúdo bruto recebido:", body.decode())
        return {"status": "erro", "mensagem": "Corpo não é JSON válido"}
    
    if 'event' in data:
        return await whatsapp(data)
    elif 'id' in data:
        return await woocommerce(data)
    else:
        print('MENSAGEM NÃO VEIO DO WHATSAPP NEM DO WEBHOOK')
    


# WEBHOOK WOOCOMMERCE PARA ATUALIZAÇÃO DO ESTOQUE

async def woocommerce(data): 
    print(data)
    id = data.get("id")
    nome = data.get("name")
    tipo = data.get("type")
    preco = data.get("price")
    estoque = data.get("stock_quantity")
    tamanho = None
    cor = None
    em_estoque = data.get("stock_status")
    em_estoque = 1 if em_estoque == "instock" else 0
    for item in data["attributes"]:
        if item["name"] == "Tamanho":
            tamanho = item.get("option")
        if item["name"] == "Cor":
            cor = item.get("option")
    imagem = data.get("src")
    descricao =data.get("short_description")
    print(f"ID: {id}, Nome: {nome} Tipo: {tipo}, Preço: {preco}, Estoque: {estoque}, Tamanho: {tamanho}, Cor: {cor}, Imagem: {imagem}, Descrição: {descricao}, ")

    conn = sqlite3.connect('data_base.db')
    cursor = conn.cursor()

    if tipo == "variable":
        cursor.execute("""UPDATE estoque SET Estoque = ?, Preço = ?, "Valores do atributo 1" = ?, "Valores do atributo 2" = ?, "Descrição curta"= ?, Imagens = ?, "Em estoque?" = ?  WHERE id = ? """, (estoque, preco, cor, tamanho, descricao, imagem, em_estoque, id)) 
    else:
        cursor.execute("""UPDATE estoque SET Estoque = ?, Preço = ?, "Metadado: rtwpvg_images" = ?,  "Em estoque?" = ?  WHERE id = ? """, (estoque, preco, imagem, em_estoque, id)) 
    conn.commit()
    conn.close()
    client = QdrantClient(url=QDRANT_URL)
    client.delete_collection("estoque_vetorial")
    cria_colecao("estoque_vetorial")

    return {"ok": True}



# Webhook Whatsapp 
async def whatsapp(data):
    print(data)
    
    message_id = data["data"]["key"]["id"]
    lock_key = f"lock:{message_id}"
    if await redis_client.exists(lock_key):
        print(f"Mensagem {message_id} já processada. Ignorando.")
        return {"status": "ok"}

    await redis_client.setex(lock_key, LOCK_TTL, 1)
    # Cria tarefa assíncrona
    print("cheguei aqui")
    asyncio.create_task(process_message(data, redis_client))

    # Retorna imediatamente para evitar eco
    return {"status": "ok"}
