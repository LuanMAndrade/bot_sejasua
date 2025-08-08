from langchain_core.tools import tool
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

INSTANCIA_EVOLUTION_API = os.getenv("INSTANCIA_EVOLUTION_API")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
PORTA = os.getenv("PORTA")

NUMERO_BACKUP = os.getenv('NUMERO_BACKUP')

# Link para texto
EVOLUTION_TEXT_URL_TEMPLATE = os.getenv("EVOLUTION_TEXT_URL")
EVOLUTION_TEXT_URL = EVOLUTION_TEXT_URL_TEMPLATE.format(INSTANCIA=INSTANCIA_EVOLUTION_API, PORTA=PORTA)

@tool
async def nao_entendi():
    """Avisa à uma atendente que não entendeu a solicitação da cliente."""
    
    payload = {"number": f'{NUMERO_BACKUP}@s.whatsapp.net',
               "text": "Não entendi a solicitação da cliente."
               }
    headers = {
                "Content-Type": "application/json",
                "apikey": EVOLUTION_API_KEY
                }
    url = EVOLUTION_TEXT_URL
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    return response