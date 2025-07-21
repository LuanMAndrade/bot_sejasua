from operator import itemgetter
from .chain_classifica_produto import chain_de_roteamento
from langchain_core.runnables import RunnableLambda, RunnableParallel
from . import chain_cor, chain_nada, chain_tamanho

def executa_roteamento_produto(entrada: dict):
    global opcao
    opcao = entrada["resposta_pydantic"].opcao
    entrada["resposta_pydantic"].opcao
    if entrada["resposta_pydantic"].opcao == 1:
        print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} (Ainda não falou nada)")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_nada.chain
    elif entrada["resposta_pydantic"].opcao == 2:
        print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} (Definiu alguma caracteristica nova)")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_cor.chain
    elif entrada["resposta_pydantic"].opcao == 3:
        print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Já definiu alguma caracteristica e continua a conversa")
        return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_tamanho.chain
    # elif entrada["resposta_pydantic"].opcao == 4:
    #     print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Final")
    #     return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_final.chain
    else:
        print("Opção escolhida pelo LLM não mapeada.")



# Cria a cadeia final usando LangChain Expression Language (LCEL)
chain_principal_produto = (RunnableParallel({"input": itemgetter("input"),
                                     "history": itemgetter("history"),
                                     "resposta_pydantic": chain_de_roteamento
                                     })
                   | RunnableLambda(executa_roteamento_produto))