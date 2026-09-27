# Exercicio 8 - classificador de risco servido por API. Entrada do modelo tambem
# e entrada de usuario, entao valido antes de prever.

import os
from datetime import datetime
import numpy as np
from flask import Flask, request, jsonify
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from pymongo import MongoClient

app = Flask(__name__)

# features: [falhas_login, portas_distintas, bytes_saida, hora_do_dia]
N_FEATURES = 4


def conectar_mongo():
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return cli["seguranca"]


def gerar_dados():
    rng = np.random.RandomState(42)
    baixo = np.column_stack([
        rng.randint(0, 3, 150),
        rng.randint(1, 3, 150),
        rng.randint(500, 3000, 150),
        rng.randint(8, 19, 150),
    ])
    alto = np.column_stack([
        rng.randint(8, 20, 150),
        rng.randint(5, 15, 150),
        rng.randint(50000, 120000, 150),
        rng.randint(0, 6, 150),
    ])
    X = np.vstack([baixo, alto])
    y = np.array([0] * 150 + [1] * 150)   # 0 baixo, 1 alto
    return X, y


X, y = gerar_dados()
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42)
modelo = RandomForestClassifier(random_state=42)
modelo.fit(X_tr, y_tr)


def validar_features(corpo):
    if not corpo or "features" not in corpo:
        return None, "corpo invalido: envie 'features'"
    feats = corpo["features"]
    if not isinstance(feats, list):
        return None, "features deve ser uma lista"
    if len(feats) != N_FEATURES:
        return None, f"esperadas {N_FEATURES} features, recebidas {len(feats)}"
    for f in feats:
        if isinstance(f, bool) or not isinstance(f, (int, float)):
            return None, "features devem ser numericas"
    return feats, None


@app.route("/api/triagem", methods=["POST"])
def triagem():
    corpo = request.get_json(silent=True)
    feats, erro = validar_features(corpo)
    if erro:
        return jsonify({"erro": erro}), 400

    entrada = np.array([feats])
    pred = int(modelo.predict(entrada)[0])
    confianca = float(modelo.predict_proba(entrada)[0].max())
    risco = "alto" if pred == 1 else "baixo"

    # guarda a previsao pra auditar o modelo depois
    conectar_mongo().previsoes.insert_one({
        "entrada": feats,
        "risco": risco,
        "confianca": round(confianca, 2),
        "timestamp": datetime.now(),
    })

    return jsonify({"risco": risco, "confianca": round(confianca, 2)}), 200


@app.route("/api/modelo/metricas")
def metricas():
    pred = modelo.predict(X_te)
    return jsonify({
        "precisao": round(float(precision_score(y_te, pred)), 2),
        "recall": round(float(recall_score(y_te, pred)), 2),
        "f1": round(float(f1_score(y_te, pred)), 2),
        "matriz": confusion_matrix(y_te, pred).tolist(),
        "aviso": "acuracia foi omitida de proposito: com classe desbalanceada ela "
                 "engana, o que importa aqui e o recall (nao deixar risco alto passar).",
    }), 200


if __name__ == "__main__":
    conectar_mongo().previsoes.drop()
    app.run(port=5003)
