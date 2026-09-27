# Exercicio 3 - coleccao eventos com indice TTL e falhas por hora

import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient


def conectar_mongo():
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return cli["seguranca"]


def popular(db):
    db.eventos.drop()
    # TTL de 7 dias, o mongo apaga sozinho o que passar disso
    db.eventos.create_index("timestamp", expireAfterSeconds=604800)

    agora = datetime.now()
    docs = []
    for _ in range(200):
        minutos = random.randint(0, 24 * 60)
        docs.append({
            "tipo": "FALHA_LOGIN",
            "timestamp": agora - timedelta(minutes=minutos),
        })
    db.eventos.insert_many(docs)


def falhas_por_hora(db):
    pipeline = [
        {"$group": {"_id": {"$hour": "$timestamp"}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return list(db.eventos.aggregate(pipeline))


def main():
    db = conectar_mongo()
    popular(db)
    resultado = falhas_por_hora(db)

    print("=== Falhas por hora (ultimas 24h) ===")
    pico = max(resultado, key=lambda r: r["total"])
    for r in resultado:
        barra = "#" * (r["total"] // 3)
        marca = "   <- pico" if r is pico else ""
        print(f"{r['_id']:02d}h | {barra} {r['total']}{marca}")

    print(f"Hora de pico: {pico['_id']:02d}h ({pico['total']} falhas)")
    print("Indice TTL ativo: eventos com mais de 7 dias sao removidos automaticamente.")
    # o TTL e decisao de seguranca: define por quanto tempo ainda existe prova pra investigar


if __name__ == "__main__":
    main()
