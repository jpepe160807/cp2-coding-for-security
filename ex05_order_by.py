# Exercicio 5 - ORDER BY nao da pra parametrizar com %s, entao uso whitelist

import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

COLUNAS = {"data": "criado_em", "sev": "severidade", "ip": "ip_origem"}
ORDEM = {"asc": "ASC", "desc": "DESC"}
TETO = 100


def db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DB", "seguranca"),
    )


@app.route("/api/eventos")
def eventos():
    ordenar_por = request.args.get("ordenar_por", "data")
    ordem = request.args.get("ordem", "asc")
    tamanho = request.args.get("tamanho", "10")

    if ordenar_por not in COLUNAS:
        return jsonify({"erro": "campo de ordenacao invalido"}), 400
    if ordem not in ORDEM:
        return jsonify({"erro": "ordem invalida"}), 400

    try:
        tamanho = int(tamanho)
    except ValueError:
        return jsonify({"erro": "tamanho deve ser inteiro"}), 400
    if tamanho > TETO:
        tamanho = TETO
    if tamanho < 1:
        tamanho = 1

    col = COLUNAS[ordenar_por]
    direcao = ORDEM[ordem]

    con = db()
    cur = con.cursor(dictionary=True)
    # col e direcao vem do dicionario, entao sao valores fixos e seguros
    cur.execute(f"SELECT * FROM eventos ORDER BY {col} {direcao} LIMIT %s", (tamanho,))
    linhas = cur.fetchall()
    cur.close(); con.close()
    return jsonify(linhas), 200


# LIMIT %s funciona porque LIMIT espera um dado (um numero), e o driver sabe mandar
# numero como parametro. ORDER BY %s nao funciona porque ali entra o nome da coluna,
# que faz parte da estrutura da query - identificador se protege com whitelist, dado com %s.

if __name__ == "__main__":
    app.run(port=5000)
