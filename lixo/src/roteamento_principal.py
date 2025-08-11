from operator import itemgetter
from src.memoria import get_session_history, trimmer
from src.chain_classifica_principal import chain_de_roteamento
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from src.chains import chain_conversa, chain_nao_sabe_responder, chain_pagamento, chain_produto
import os
from loguru import logger
import psycopg2

POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

conn = psycopg2.connect(
    host="localhost", 
    port=5432,
    dbname="evolution",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()
cur.execute("""SELECT * FROM "Message" ORDER BY "messageTimestamp" DESC LIMIT 1;
""")
rows = cur.fetchall()
for row in rows:
    print(row)
cur.close()
conn.close()

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
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_produto.chain
    elif entrada["resposta_pydantic"].opcao == 3:
        logger.info(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Pagamento")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history'], "nome":x['nome']}) | chain_pagamento.chain
    elif entrada["resposta_pydantic"].opcao == 4:
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
chain_principal_com_trimming = (RunnablePassthrough.assign(history=itemgetter("history") | trimmer)
    | chain_principal
)

runnable_with_history = RunnableWithMessageHistory(
    chain_principal_com_trimming,
    get_session_history,
    output_messages_key="history_output" ,
    input_messages_key="input",
    history_messages_key="history"
)

def run_chatbot(message, sender, nome):
    result = runnable_with_history.invoke(
                {"input": message,
                 "nome": nome},
                config={"configurable": {"session_id": sender}},
            )
    
    return result, opcao