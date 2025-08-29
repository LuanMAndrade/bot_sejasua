import sqlite3
import pandas as pd
from pathlib import Path

def cria_estoque():
    BASE_DIR = Path(__file__).resolve().parent.parent
    documento = BASE_DIR/'data/estoque.csv'

    df = pd.read_csv(documento)
    df.sort_values(by="Nome")
    df = df.get(["ID", "Tipo", "Nome", "Categorias", "Nome do atributo 1", "Valores do atributo 1", "Nome do atributo 2", "Valores do atributo 2", "Descrição curta", "Preço", "Em estoque?", "Estoque", "Metadado: rtwpvg_images", "Imagens"])
    df['Nome do atributo 2'].fillna('Tamanho', inplace=True)
    df['Valores do atributo 2'].fillna('único', inplace=True)

    for index, row in df.iterrows():
        df.loc[index, "Valores do atributo 1"] = df.loc[index, "Valores do atributo 1"].lower()
        df.loc[index, "Valores do atributo 2"] = df.loc[index, "Valores do atributo 2"].lower()
        df.loc[index, "Nome"] = df.loc[index, "Nome"].lower()

        if row["Nome do atributo 1"] == "Tamanho":
            df.loc[index, "Nome do atributo 1"] = "Cor"
            df.loc[index, "Nome do atributo 2"] = "Tamanho"
            x = df.loc[index, "Valores do atributo 1"]
            df.loc[index, "Valores do atributo 1"] = df.loc[index, "Valores do atributo 2"]
            df.loc[index, "Valores do atributo 2"] = x

    conn = sqlite3.connect("data_base.db")

    df.to_sql("estoque", conn, if_exists="replace", index=False)

    conn.close()

if __name__ == '__main__':
    cria_estoque()