# Exercicio 9 - rate limit por anomalia. Grava cada acesso, agrega por IP e usa
# IsolationForest pra decidir quem toma 429.

import os
from datetime import datetime
from flask import Flask, request, jsonify, g
import numpy as np
from sklearn.ensemble import IsolationForest
from pymongo import MongoClient

app = Flask(__name__)

BLOQUEADOS = set()


def conectar_mongo():
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return cli["seguranca"]


@app.before_request
def registrar_entrada():
    ip = request.remote_addr or "0.0.0.0"

    if ip in BLOQUEADOS and request.path != "/analisar":
        resp = jsonify({"erro": "muitas requisicoes"})
        resp.status_code = 429
        resp.headers["Retry-After"] = "60"
        return resp

    g.registro_id = conectar_mongo().acessos.insert_one({
        "ip": ip,
        "rota": request.path,
        "metodo": request.method,
        "timestamp": datetime.now(),
        "status": None,
    }).inserted_id


@app.after_request
def registrar_status(resp):
    rid = getattr(g, "registro_id", None)
    if rid is not None:
        conectar_mongo().acessos.update_one(
            {"_id": rid}, {"$set": {"status": resp.status_code}})
    return resp


def features_por_ip(db):
    # agrega no banco: total, quantos 4xx e quantas rotas distintas por IP
    pipeline = [
        {"$group": {
            "_id": "$ip",
            "total": {"$sum": 1},
            "erros_4xx": {"$sum": {"$cond": [
                {"$and": [{"$gte": ["$status", 400]}, {"$lt": ["$status", 500]}]},
                1, 0]}},
            "rotas": {"$addToSet": "$rota"},
            "inicio": {"$min": "$timestamp"},
            "fim": {"$max": "$timestamp"},
        }},
    ]
    dados = []
    for r in db.acessos.aggregate(pipeline):
        segundos = max((r["fim"] - r["inicio"]).total_seconds(), 1)
        req_por_min = r["total"] / (segundos / 60)
        taxa_4xx = r["erros_4xx"] / r["total"]
        dados.append({
            "ip": r["_id"],
            "features": [req_por_min, taxa_4xx, len(r["rotas"])],
        })
    return dados


@app.route("/analisar")
def analisar():
    db = conectar_mongo()
    dados = features_por_ip(db)
    if len(dados) < 2:
        return jsonify({"erro": "poucos dados para analisar"}), 400

    X = np.array([d["features"] for d in dados])
    modelo = IsolationForest(contamination=0.2, random_state=42)
    pred = modelo.fit_predict(X)   # -1 anomalia, 1 normal

    print("=== Analise de acessos ===")
    BLOQUEADOS.clear()
    for d, p in zip(dados, pred):
        rpm, t4xx, rotas = d["features"]
        rotulo = "normal"
        if p == -1:
            rotulo = "ANOMALIA -> bloqueado"
            BLOQUEADOS.add(d["ip"])
        print(f"{d['ip']:15} [ {rpm:5.1f} req/min | 4xx {t4xx:.2f} | {int(rotas)} rotas]  -> {rotulo}")

    return jsonify({"bloqueados": list(BLOQUEADOS)}), 200


@app.route("/api/ping")
def ping():
    return jsonify({"ok": True}), 200


# risco de bloquear por anomalia em vez de regra fixa: um falso positivo derruba
# usuario legitimo, por isso uso 429 com Retry-After e nao um ban permanente.

if __name__ == "__main__":
    conectar_mongo().acessos.drop()
    app.run(port=5004)
