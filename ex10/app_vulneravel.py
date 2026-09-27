# app_vulneravel.py - so pra laboratorio, nao usar de verdade
import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)
SENHA_MESTRA = "exemplo-nao-use"


def db():
    return mysql.connector.connect(
        host="localhost", user="root",
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database="seguranca")


@app.route("/api/usuarios/buscar")
def buscar():
    nome = request.args.get("nome", "")
    con = db()
    cur = con.cursor(dictionary=True)
    # concatena a entrada direto na query -> da pra injetar sql
    cur.execute(f"SELECT * FROM usuarios WHERE nome LIKE '%{nome}%'")
    return jsonify(cur.fetchall())


@app.route("/perfil")
def perfil():
    # devolve o que veio sem escapar -> xss
    return f"<h1>Bem-vindo, {request.args.get('u','')}</h1>"


@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
def remover(uid):
    # nao pede nenhuma credencial pra deletar
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
    con.commit()
    return jsonify({"removido": uid})


@app.route("/api/relatorio")
def relatorio():
    # erro de banco vaza o traceback com debug ligado
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM tabela_inexistente")
    return jsonify(cur.fetchall())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
