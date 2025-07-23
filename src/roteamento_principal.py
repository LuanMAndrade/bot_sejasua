from operator import itemgetter
from src.memoria import get_session_history, trimmer
from src.chain_classifica_principal import chain_de_roteamento

from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from src.chains.chains_principais import chain_conversa, chain_imagem, chain_nao_sabe_responder, chain_pagamento
from src.chains.chains_principais import roteamento_produto
import os
from loguru import logger

EVOLUTION_TEXT_URL= os.getenv('EVOLUTION_TEXT_URL')
EVOLUTION_MEDIA_URL= os.getenv('EVOLUTION_MEDIA_URL')

def executa_roteamento(entrada: dict):
    global opcao
    opcao = entrada["resposta_pydantic"].opcao

    entrada["resposta_pydantic"].opcao
    if entrada["resposta_pydantic"].opcao == 1:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Conversa normal")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_conversa.chain
    elif entrada["resposta_pydantic"].opcao == 2:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Informação sobre produto ")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | roteamento_produto.chain_principal_produto
    elif entrada["resposta_pydantic"].opcao == 3:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Pedindo uma imagem")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_imagem.chain
    elif entrada["resposta_pydantic"].opcao == 4:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Pagamento")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history'], "nome":x['nome']}) | chain_pagamento.chain
    elif entrada["resposta_pydantic"].opcao == 5:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Não sei o que fazer")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history'], "nome":x['nome']}) | chain_nao_sabe_responder.chain
    
    else:
        logger.info("Opção escolhida pelo LLM não mapeada.")



# Cria a cadeia final usando LangChain Expression Language (LCEL)
chain_principal = (RunnableParallel({"input": itemgetter("input"),
                                     "history": itemgetter("history"),
                                     "nome": itemgetter("nome"),
                                     "resposta_pydantic": chain_de_roteamento
                                     })
                   | RunnableLambda(executa_roteamento))



## Encapsulando nossa chain com a classe de gestão de mensagens de histórico
chain_principal_com_trimming = (
    RunnablePassthrough.assign(history=itemgetter("history") | trimmer)
    | chain_principal
)

runnable_with_history = RunnableWithMessageHistory(
    chain_principal_com_trimming,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

def run_chatbot(message, sender, nome):
    result = runnable_with_history.invoke(
                {"input": message,
                 "nome": nome},
                config={"configurable": {"session_id": sender}},
            )
    
    # if 'http' in result:
    #     partes = result.split('http', 1)
    #     texto = partes[0].strip()
    #     resto = 'http' + partes[1].strip()

    #     for extensao in ['.jpg', '.png', '.jpeg', '.webp']:
    #         if extensao in resto:
    #             link = resto.split(extensao)[0] + extensao
    #             break
    #     else:
    #         link = resto  # se não achar nenhuma extensão de imagem

    #     print("Texto:", texto)
    #     print("Link:", link)
    #     payload = {
    #             "number": sender,
    #             "mediatype": "image",
    #             "caption": texto,
    #             "media": link
    #         }
    #     url = EVOLUTION_MEDIA_URL
    
    if opcao == 3:
        payload = {
                "number": sender,
                "mediatype": "image",
                "caption": "Veja o produto!",
                "media": result
            }
        url = EVOLUTION_MEDIA_URL
    elif opcao == 5 or opcao == 4:
        payload = {
                "number": '557181238313@s.whatsapp.net',
                "text": result,
            }
        url = EVOLUTION_TEXT_URL
    else:
        payload = {
                "number": sender,
                "text": result,
            }
        url = EVOLUTION_TEXT_URL
    
    
    return payload , url