from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Cria índice de texto para o campo "Nome" na coleção "teste"
client.create_payload_index(
    collection_name="teste1",
    field_name="Nome",
    field_schema=rest.PayloadSchemaType.TEXT
)

print("Índice de texto criado com sucesso no campo 'Nome'.")
