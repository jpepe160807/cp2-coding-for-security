# Exercicio 2 - migra ativos/alertas do MySQL pro Mongo (ativo aninhado no alerta)

import os
import mysql.connector
from pymongo import MongoClient


def conectar_mysql():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DB", "seguranca"),
    )


def conectar_mongo():
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return cli["seguranca"]


def criar_e_popular(con):
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS alertas")
    cur.execute("DROP TABLE IF EXISTS ativos")
    cur.execute("""
        CREATE TABLE ativos (
            id INT PRIMARY KEY,
            nome VARCHAR(50),
            ip VARCHAR(20) UNIQUE,
            criticidade ENUM('baixa','media','alta')
        )""")
    cur.execute("""
        CREATE TABLE alertas (
            id INT PRIMARY KEY,
            ativo_id INT,
            tipo VARCHAR(50),
            severidade VARCHAR(20),
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ativo_id) REFERENCES ativos(id)
        )""")

    ativos = [(1, "SRV-WEB01", "192.168.1.10", "alta"),
              (2, "PC-RH03", "192.168.1.45", "baixa")]
    alertas = [(1, 1, "BRUTE_FORCE", "critica"),
               (2, 1, "PORT_SCAN", "alta"),
               (3, 2, "XSS", "media")]

    cur.executemany("INSERT INTO ativos VALUES (%s,%s,%s,%s)", ativos)
    cur.executemany(
        "INSERT INTO alertas (id, ativo_id, tipo, severidade) VALUES (%s,%s,%s,%s)",
        alertas,
    )
    con.commit()
    cur.close()


def ler_com_join(con):
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT al.tipo, al.severidade, at.nome, at.ip, at.criticidade
        FROM alertas al
        JOIN ativos at ON at.id = al.ativo_id
        WHERE at.criticidade IN (%s, %s, %s)
    """, ("baixa", "media", "alta"))
    linhas = cur.fetchall()
    cur.close()
    return linhas


def montar_documentos(linhas):
    docs = []
    for l in linhas:
        docs.append({
            "tipo": l["tipo"],
            "severidade": l["severidade"],
            "ativo": {
                "nome": l["nome"],
                "ip": l["ip"],
                "criticidade": l["criticidade"],
            },
        })
    return docs


def main():
    con = conectar_mysql()
    db = conectar_mongo()

    criar_e_popular(con)
    linhas = ler_com_join(con)
    docs = montar_documentos(linhas)

    db.alertas.drop()
    db.alertas.insert_many(docs)

    # confere se veio a mesma quantidade dos dois lados
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM alertas")
    total_mysql = cur.fetchone()[0]
    cur.close()
    total_mongo = db.alertas.count_documents({})

    integra = "MIGRACAO INTEGRA" if total_mysql == total_mongo else "DIVERGENTE!"
    print(f"MySQL: {total_mysql} alertas | MongoDB: {total_mongo} documentos -> {integra}")

    n = db.alertas.count_documents({"ativo.criticidade": "alta"})
    print(f'Consulta sem JOIN: db.alertas.find({{"ativo.criticidade":"alta"}}) -> {n} documentos')

    # ganho: le sem JOIN, o ativo ja vem junto
    # perda: dado duplicado, renomear um ativo obriga update_many em todos os alertas

    con.close()


if __name__ == "__main__":
    main()
