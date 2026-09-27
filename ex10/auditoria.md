# Auditoria do app_vulneravel.py

Uma linha por falha (codigo OWASP 2025, impacto e correcao):

| # | Falha | OWASP | Impacto | Correcao |
|---|-------|-------|---------|----------|
| 1 | SQL injection na busca (query concatenada) | A03 | vaza/altera a tabela toda | query parametrizada com %s |
| 2 | XSS refletido no /perfil | A03 | roda script no navegador da vitima | escapar a entrada (markupsafe.escape) |
| 3 | DELETE sem autenticacao | A01 | qualquer um apaga usuarios | exigir X-API-Key (401/403) |
| 4 | debug=True vaza traceback e nome da tabela | A05 | da o mapa do banco pro atacante | debug=False + erro generico |
| 5 | resposta traz a coluna senha | A02 | expoe credenciais | selecionar so as colunas necessarias |
| 6 | sem headers de seguranca (ausencia) | A05 | sem CSP nem anti-clickjacking | adicionar headers no after_request |
| 7 | senha escrita no codigo (SENHA_MESTRA) | A07 | segredo vaza no git | ler de variavel de ambiente |
| 8 | nenhum log das requisicoes (ausencia) | A09 | ataque nao deixa rastro | registrar as requisicoes |

As duas ausencias sao a 6 (headers) e a 8 (logging): nao estao escritas em lugar
nenhum do arquivo, e e por nao existirem que sao falhas.
