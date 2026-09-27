# Exercicio 4 - alterar nivel dentro de transacao e auditar toda tentativa no mongo

import os
from datetime import datetime
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


def preparar(con):
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios")
    cur.execute("""
        CREATE TABLE usuarios (
            id INT PRIMARY KEY,
            nome VARCHAR(50),
            email VARCHAR(80),
            nivel_acesso INT
        )""")
    usuarios = [(1, "ana", "ana@x.com", 5),
                (2, "bruno", "bruno@x.com", 2),
                (3, "caio", "caio@x.com", 1)]
    cur.executemany("INSERT INTO usuarios VALUES (%s,%s,%s,%s)", usuarios)
    con.commit()
    cur.close()


def registrar_auditoria(db, quem, alvo, nivel_ant, nivel_novo, resultado):
    db.auditoria.insert_one({
        "quem": quem,
        "alvo": alvo,
        "nivel_anterior": nivel_ant,
        "nivel_novo": nivel_novo,
        "resultado": resultado,
        "timestamp": datetime.now(),
    })


def buscar_nivel(cur, uid):
    cur.execute("SELECT nivel_acesso FROM usuarios WHERE id = %s", (uid,))
    row = cur.fetchone()
    return row[0] if row else None


def alterar_nivel(admin_id, alvo_id, novo_nivel):
    con = conectar_mysql()
    db = conectar_mongo()
    cur = con.cursor()

    nivel_admin = buscar_nivel(cur, admin_id)
    nivel_alvo = buscar_nivel(cur, alvo_id)

    # ninguem se auto-promove
    if admin_id == alvo_id:
        con.rollback()
        registrar_auditoria(db, admin_id, alvo_id, nivel_alvo, novo_nivel, "RECUSADO")
        cur.close(); con.close()
        return "RECUSADO (auto-promocao)"

    # so nivel >= 5 pode alterar
    if nivel_admin is None or nivel_admin < 5:
        con.rollback()
        registrar_auditoria(db, admin_id, alvo_id, nivel_alvo, novo_nivel, "RECUSADO")
        cur.close(); con.close()
        return "RECUSADO (admin sem privilegio)"

    if nivel_alvo is None:
        con.rollback()
        registrar_auditoria(db, admin_id, alvo_id, None, novo_nivel, "RECUSADO")
        cur.close(); con.close()
        return "RECUSADO (alvo inexistente)"

    try:
        cur.execute("UPDATE usuarios SET nivel_acesso = %s WHERE id = %s",
                    (novo_nivel, alvo_id))
        con.commit()
        registrar_auditoria(db, admin_id, alvo_id, nivel_alvo, novo_nivel, "SUCESSO")
        cur.close(); con.close()
        return f"OK. commit. alvo {alvo_id}: {nivel_alvo} -> {novo_nivel}"
    except Exception:
        con.rollback()
        registrar_auditoria(db, admin_id, alvo_id, nivel_alvo, novo_nivel, "RECUSADO")
        cur.close(); con.close()
        return "RECUSADO (erro na transacao)"


def main():
    con = conectar_mysql()
    preparar(con)
    con.close()

    db = conectar_mongo()
    db.auditoria.drop()

    print(alterar_nivel(1, 2, 4))
    print(alterar_nivel(2, 3, 5))
    print(alterar_nivel(1, 1, 9))
    print(alterar_nivel(1, 99, 3))

    total = db.auditoria.count_documents({})
    recusas = db.auditoria.count_documents({"resultado": "RECUSADO"})
    print(f"Trilha de auditoria: {total} documentos ({total - recusas} sucesso, {recusas} recusas)")


if __name__ == "__main__":
    main()
