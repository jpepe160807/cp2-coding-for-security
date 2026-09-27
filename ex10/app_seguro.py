# app_seguro.py - versao corrigida do app_vulneravel
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# usada nas operacoes que apagam dados, vem do ambiente
API_KEY = os.environ.get("API_KEY", "chave-de-teste-local")

import mysql.connector


def db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DB", "seguranca"),
    )


@app.after_request
def headers_seguranca(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = "default-src 'self'"
    return resp


@app.route("/api/usuarios/buscar")
def buscar():
    nome = request.args.get("nome", "")
    con = db()
    cur = con.cursor(dictionary=True)
    # query parametrizada, o LIKE recebe o dado como parametro
    cur.execute("SELECT id, nome, email FROM usuarios WHERE nome LIKE %s",
                (f"%{nome}%",))
    linhas = cur.fetchall()
    cur.close(); con.close()
    # nao devolve a coluna senha
    return jsonify(linhas)


@app.route("/perfil")
def perfil():
    from markupsafe import escape
    u = escape(request.args.get("u", ""))
    return f"<h1>Bem-vindo, {u}</h1>"


@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
def remover(uid):
    chave = request.headers.get("X-API-Key")
    if not chave:
        return jsonify({"erro": "nao autenticado"}), 401
    if chave != API_KEY:
        return jsonify({"erro": "acesso negado"}), 403

    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
    con.commit()
    cur.close(); con.close()
    return jsonify({"removido": uid})


@app.route("/api/relatorio")
def relatorio():
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM tabela_inexistente")
        dados = cur.fetchall()
        cur.close(); con.close()
        return jsonify(dados)
    except Exception:
        # erro generico, sem traceback nem nome de tabela
        return jsonify({"erro": "erro interno"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5005)
