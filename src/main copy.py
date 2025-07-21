from operator import itemgetter
from src.memoria import get_session_history, trimmer
from chains.meu_chain_classifica import chain_de_roteamento

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from chains import chain_loja, chain_conversa, chain_imagem, chain_nao_sabe_responder, chain_pagamento
from chains.chain_produto import roteamento_produto
import os
from loguru import logger

EVOLUTION_TEXT_URL = os.getenv('EVOLUTION_TEXT_URL')
EVOLUTION_MEDIA_URL = os.getenv('EVOLUTION_MEDIA_URL')

# =====================================================================================
# Lógica de Roteamento (substituindo o if/elif e a variável global)
# =====================================================================================

def get_routing_chain(opcao: int):
    """Retorna a chain apropriada com base na opção de roteamento."""
    
    # Mapeamento de opções para as chains correspondentes
    routing_map = {
        1: ("Informações ou orientações sobre a loja", chain_loja.chain),
        2: ("Conversa normal", chain_conversa.chain),
        3: ("Informação sobre produto", roteamento_produto.chain_principal_produto),
        4: ("Pedindo uma imagem", chain_imagem.chain),
        5: ("Pagamento", chain_pagamento.chain),
        6: ("Não sei o que fazer", chain_nao_sabe_responder.chain),
    }
    
    description, chain = routing_map.get(opcao, (None, None))
    
    if chain:
        logger.info(f">> Roteamento para Opção {opcao}: {description}")
        # Retorna uma sub-chain que processa a entrada e o histórico
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain
    else:
        logger.warning(f"Opção de roteamento não mapeada: {opcao}")
        # Retorna uma chain padrão ou de erro, se necessário
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_nao_sabe_responder.chain

def route_request(entrada: dict):
    """
    Determina a rota e executa a chain correspondente.
    Retorna tanto o resultado da chain quanto a opção de roteamento.
    """
    opcao = entrada["resposta_pydantic"].opcao
    selected_chain = get_routing_chain(opcao)
    
    # Executa a chain e anexa a opção ao resultado final
    return RunnableParallel(
        result=selected_chain,
        opcao=RunnableLambda(lambda x: opcao)
    )

# =====================================================================================
# Lógica de Formatação de Payload (para a Evolution API)
# =====================================================================================

def format_payload(result_data: dict, sender: str):
    """Formata o payload de resposta para a Evolution API."""
    result = result_data.get("result")
    opcao = result_data.get("opcao")
    
    if opcao == 4:  # Resposta com imagem
        payload = {
            "number": sender,
            "mediatype": "image",
            "caption": "Veja o produto!",
            "media": result
        }
        url = EVOLUTION_MEDIA_URL
    elif opcao == 6:  # Resposta para humano (fallback)
        payload = {
            "number": '557181238313@s.whatsapp.net',
            "text": result,
        }
        url = EVOLUTION_TEXT_URL
    else:  # Resposta de texto padrão
        payload = {
            "number": sender,
            "text": result,
        }
        url = EVOLUTION_TEXT_URL
        
    return payload, url

# =====================================================================================
# Construção da Chain Principal do LangChain
# =====================================================================================

# A chain agora passa a resposta_pydantic para a função de roteamento
chain_principal = (
    RunnableParallel({
        "input": itemgetter("input"),
        "history": itemgetter("history"),
        "resposta_pydantic": chain_de_roteamento
    })
    | RunnableLambda(route_request)
)

# Encapsulando a chain com gerenciamento de histórico
chain_principal_com_trimming = (
    RunnablePassthrough.assign(history=itemgetter("history") | trimmer)
    | chain_principal
)

runnable_with_history = RunnableWithMessageHistory(
    chain_principal_com_trimming,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# =====================================================================================
# Função Principal de Execução do Chatbot
# =====================================================================================

def run_chatbot(message: str, sender: str):
    """
    Executa a chain do chatbot e formata a resposta.
    """
    # Invoca a chain, que agora retorna um dicionário com 'result' e 'opcao'
    result_data = runnable_with_history.invoke(
        {"input": message},
        config={"configurable": {"session_id": sender}},
    )
    
    # Usa a função de formatação para criar o payload
    payload, url = format_payload(result_data, sender)
    
    return payload, url
