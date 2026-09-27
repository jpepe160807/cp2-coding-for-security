# CP2 Cumulativo - 2 semestre (Coding for Security)

Resolucao dos 10 exercicios.

## Dependencias

```bash
pip install pymongo mysql-connector-python scikit-learn numpy flask requests
```

Bancos rodando via Docker (mongo-lab e mysql-lab). A senha do banco vem de
variavel de ambiente:

```bash
$env:MYSQL_PASSWORD="suasenha"     # PowerShell
set MYSQL_PASSWORD=suasenha         # cmd
```

## Rodando

| Ex | Arquivo | Obs |
|----|---------|-----|
| 1 | ex01_recomendar.py | roda sozinho, sem banco |
| 2 | ex02_migracao.py | MySQL + Mongo |
| 3 | ex03_ttl_janela.py | Mongo |
| 4 | ex04_transacao_auditoria.py | MySQL + Mongo |
| 5 | ex05_order_by.py | Flask porta 5000, tabela eventos |
| 6 | ex06_controle_acesso.py | Flask porta 5001 |
| 7 | ex07_xss_atributo.py | Flask porta 5002, Mongo |
| 8 | ex08_ml_api.py | Flask porta 5003, Mongo |
| 9 | ex09_rate_limit.py | Flask porta 5004, Mongo (chamar /analisar) |
| 10 | ex10/ | app_vulneravel, app_seguro, exploit, auditoria |

### Exercicio 10

Sobe uma das apps e roda o exploit contra ela:

```bash
python ex10/app_vulneravel.py     # porta 5000
python ex10/exploit.py http://127.0.0.1:5000

python ex10/app_seguro.py         # porta 5005
python ex10/exploit.py http://127.0.0.1:5005
```

O exploit roda so contra a copia local (Lei 12.737/2012).
