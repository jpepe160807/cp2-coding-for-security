# Exercicio 6 - cada analista so ve os seus incidentes, nivel >= 5 pode deletar
# 401 = nao sei quem voce e / 403 = sei quem e mas nao pode

import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)


def db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DB", "seguranca"),
    )


def autenticar():
    chave = request.headers.get("X-API-Key")
    if not chave:
        return None
    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT id, nome, nivel FROM analistas WHERE api_key = %s", (chave,))
    analista = cur.fetchone()
    cur.close(); con.close()
    return analista


def buscar_incidente(inc_id):
    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM incidentes WHERE id = %s", (inc_id,))
    inc = cur.fetchone()
    cur.close(); con.close()
    return inc


@app.route("/api/incidentes/<int:inc_id>")
def ver_incidente(inc_id):
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    inc = buscar_incidente(inc_id)
    if inc is None:
        return jsonify({"erro": "nao encontrado"}), 404
    if inc["dono_id"] != analista["id"]:
        # 403 sem dizer nada sobre o incidente
        return jsonify({"erro": "acesso negado"}), 403

    return jsonify(inc), 200


@app.route("/api/incidentes")
def listar_incidentes():
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM incidentes WHERE dono_id = %s", (analista["id"],))
    lista = cur.fetchall()
    cur.close(); con.close()
    return jsonify(lista), 200


@app.route("/api/incidentes/<int:inc_id>", methods=["DELETE"])
def remover_incidente(inc_id):
    analista = autenticar()
    if analista is None:
        return jsonify({"erro": "nao autenticado"}), 401

    if analista["nivel"] < 5:
        return jsonify({"erro": "acesso negado"}), 403

    inc = buscar_incidente(inc_id)
    if inc is None:
        return jsonify({"erro": "nao encontrado"}), 404

    con = db()
    cur = con.cursor()
    cur.execute("DELETE FROM incidentes WHERE id = %s", (inc_id,))
    con.commit()
    cur.close(); con.close()
    return jsonify({"removido": inc_id}), 200


if __name__ == "__main__":
    app.run(port=5001)
