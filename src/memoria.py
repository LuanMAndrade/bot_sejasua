from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import trim_messages
import pandas as pd
import sqlite3


# Instancia o encapuslamento do modelo de IA para ter a database de mensagens
def get_session_history(session_id):
    return SQLChatMessageHistory(session_id=session_id, connection='sqlite:///chat_history.db')


trimmer = trim_messages(strategy="last", max_tokens=100, token_counter= len)

def create_estoque(path):

    df = pd.read_csv(path)

    conn = sqlite3.connect('estoque.db')

    df.to_sql('estoque', conn, if_exists='replace', index=False)

    conn.close()

create_estoque('C:\\Users\\Luan\\Desktop\\VScode Projetos\\Chatbot\\data\\estoque.csv')

# conn = sqlite3.connect("estoque.db")
# cursor = conn.cursor()

# # Pega todas as linhas ordenadas pelo ID (ou pela ordem que fizer sentido no seu caso)
# cursor.execute("SELECT ID, tipo, Descrição FROM estoque ORDER BY ID")
# linhas = cursor.fetchall()

# descricao_atual = None

# for id_, tipo, descricao in linhas:
#     if tipo == "variable":
#         # Armazena a descrição atual
#         descricao_atual = descricao
#     elif tipo == "variation" and descricao_atual is not None:
#         # Atualiza a linha com a descrição herdada
#         cursor.execute("UPDATE estoque SET Descrição = ? WHERE ID = ?", (descricao_atual, id_))

# # Salva alterações no banco
# conn.commit()
# conn.close()

# print("✅ Descrições copiadas com sucesso!")