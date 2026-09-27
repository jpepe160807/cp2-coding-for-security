# Exercicio 7 - XSS dentro de atributo. Jinja2 escapa por padrao e segura os dois payloads.
# (exercicio defensivo, os payloads rodam so contra a app local)

import os
from flask import Flask, render_template_string
from pymongo import MongoClient

app = Flask(__name__)


def conectar_mongo():
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return cli["seguranca"]


def semear(db):
    db.incidentes.drop()
    db.incidentes.insert_many([
        {"titulo": "<script>alert('xss1')</script>", "ativo": "SRV-01"},
        {"titulo": "phishing", "ativo": 'x" onerror="alert(\'xss2\')'},
    ])


TEMPLATE_SEGURO = """
<!doctype html>
<html><body>
<h1>Dashboard (seguro)</h1>
<table border="1">
  <tr><th>Titulo</th><th>Ativo</th></tr>
  {% for inc in incidentes %}
  <tr>
    <td>{{ inc.titulo }}</td>
    <td><img src="/icone.png" alt="{{ inc.ativo }}"> {{ inc.ativo }}</td>
  </tr>
  {% endfor %}
</table>
</body></html>
"""

# so pra comparar - com |safe o escape sai e o payload volta a rodar
TEMPLATE_INSEGURO = """
<!doctype html>
<html><body>
<h1>Dashboard (INSEGURO - so para comparacao)</h1>
<table border="1">
  <tr><th>Titulo</th><th>Ativo</th></tr>
  {% for inc in incidentes %}
  <tr>
    <td>{{ inc.titulo | safe }}</td>
    <td><img src="/icone.png" alt="{{ inc.ativo | safe }}"></td>
  </tr>
  {% endfor %}
</table>
</body></html>
"""


@app.after_request
def csp(resp):
    resp.headers["Content-Security-Policy"] = "default-src 'self'"
    return resp


@app.route("/dashboard")
def dashboard():
    db = conectar_mongo()
    incidentes = list(db.incidentes.find())
    # o {{ }} do jinja escapa sozinho, entao o payload vira texto.
    # se eu por |safe aqui o html cru vai pro navegador e o XSS volta.
    return render_template_string(TEMPLATE_SEGURO, incidentes=incidentes)


@app.route("/dashboard-inseguro")
def dashboard_inseguro():
    db = conectar_mongo()
    incidentes = list(db.incidentes.find())
    return render_template_string(TEMPLATE_INSEGURO, incidentes=incidentes)


@app.route("/seed")
def seed():
    semear(conectar_mongo())
    return "ok"


if __name__ == "__main__":
    semear(conectar_mongo())
    app.run(port=5002)
