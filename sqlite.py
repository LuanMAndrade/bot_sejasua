import sqlite3
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT, -- 'human' ou 'ai'
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

import json
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def save_message(conversation_id, messages):
    import json
    import sqlite3
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()

    for message in messages:

        if isinstance(message, HumanMessage):
            role = "human"
            content_str = str(message.content)
        elif isinstance(message, AIMessage):
            role = "ai"
            # AIMessage geralmente tem content string simples
            content_str = str(message.content)
        elif isinstance(message, ToolMessage):
            role = "tool"
            # Salva campos necessários para reconstrução
            content_str = json.dumps({
                "content": message.content,
                "name": message.name,
                "tool_call_id": message.tool_call_id
            }, ensure_ascii=False)
        else:
            role = "unknown"
            content_str = str(message.content)

        c.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, content_str))

        c.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
            AND id NOT IN (
                SELECT id FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT 10
            )
        """, (conversation_id, conversation_id))

    conn.commit()
    conn.close()



def get_history(conversation_id):
    import json
    import sqlite3
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
              (conversation_id,))
    rows = c.fetchall()
    conn.close()

    history = []
    for role, content_str in rows:
        if role == "human":
            history.append(HumanMessage(content=content_str))
        elif role == "tool":
            data = json.loads(content_str)
            # Reconstrói ToolMessage, mas para passar ao modelo vamos transformar em AIMessage
            # porque OpenAI não aceita 'tool' no role
            # Então converta ToolMessage para AIMessage com o mesmo conteúdo:
            history.append(AIMessage(content=data["content"]))
        elif role == "ai":
            history.append(AIMessage(content=content_str))
        else:
            history.append(HumanMessage(content=content_str))
    return history