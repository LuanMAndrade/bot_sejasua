from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import trim_messages
import pandas as pd
import sqlite3


# Instancia o encapuslamento do modelo de IA para ter a database de mensagens
def get_session_history(session_id):
    return SQLChatMessageHistory(session_id=session_id, connection='sqlite:///chat_history.db')


trimmer = trim_messages(strategy="last", max_tokens=30, token_counter= len)

def create_estoque(path):

    df = pd.read_csv(path)

    conn = sqlite3.connect('estoque.db')

    df.to_sql('estoque', conn, if_exists='replace', index=False)

    conn.close()

create_estoque('/root/chatbots/bot_sejasua/Chatbot/data/estoque.csv')