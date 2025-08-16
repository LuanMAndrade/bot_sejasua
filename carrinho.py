from langchain_core.tools import tool
from typing import Annotated


@tool
def add_to_cart(user_id:Annotated[str, "Número de identificação do usuário"], product_id: Annotated[str, "id do produto"], quantity: Annotated[int, "Quantidade do produto"]):
    """Adiciona um produto ao carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        product_id INT,
        quantity INT
    )
    """)
    # Verifica se já existe o produto no carrinho
    cur.execute("SELECT quantity FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE cart SET quantity = ? WHERE user_id=? AND product_id=?",
                    (quantity, user_id, product_id))
    else:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (user_id, product_id, quantity))
    conn.commit()
    conn.close()
    return f"Produto {product_id} adicionado (qtd {quantity})."


@tool
def remove_from_cart(user_id: str, product_id: str):
    """Remove um produto do carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
    conn.commit()
    conn.close()
    return f"Produto {product_id} removido do carrinho."


@tool
def view_cart(user_id: str):
    """Mostra os itens atuais do carrinho do usuário."""
    conn = sqlite3.connect("data_base.db")
    cur = conn.cursor()
    cur.execute("SELECT product_id, quantity FROM cart WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    
    if not rows:
        return "Seu carrinho está vazio."
    
    itens_id = [row['product_id'] for row in rows]
    cur.execute("SELECT * FROM estoque WHERE id =?", (itens_id))
    itens = cur.fetchall()
    conn.close()
    return itens