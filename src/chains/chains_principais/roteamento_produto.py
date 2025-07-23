from operator import itemgetter
from ..chain_produto.chain_classifica_produto import chain_de_roteamento
from langchain_core.runnables import RunnableLambda, RunnableParallel
from ..chain_produto import chain_carac_definida, chain_carac_nova
import teste
def executa_roteamento_produto(entrada: dict):
    global opcao
    opcao = entrada["resposta_pydantic"].opcao
    entrada["resposta_pydantic"].opcao
    return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | teste.chain
    # if entrada["resposta_pydantic"].opcao == 1:
    #     print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Definiu alguma caracteristica nova")
    #     return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_carac_nova.chain
    # elif entrada["resposta_pydantic"].opcao == 2:
    #     print(f">> Opção classe Pydantic: {entrada['resposta_pydantic'].opcao} Não definiu característica nova")
    #     return RunnableLambda(lambda x: {"input": x['input'], "history": x['history']}) | chain_carac_definida.chain
    # else:
    #     print("Opção escolhida pelo LLM não mapeada.")



# Cria a cadeia final usando LangChain Expression Language (LCEL)
chain_principal_produto = (RunnableParallel({"input": itemgetter("input"),
                                     "history": itemgetter("history"),
                                     "resposta_pydantic": chain_de_roteamento
                                     })
                   | RunnableLambda(executa_roteamento_produto))