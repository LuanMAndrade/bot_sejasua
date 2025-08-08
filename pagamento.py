from langchain_core.tools import tool
from typing import Annotated


@tool
def pagamento():
    """Retorna um link de pagamento para a cliente."""
    return "https://example.com/pagamento"