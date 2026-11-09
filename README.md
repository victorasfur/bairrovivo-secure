# BairroVivo — MVP de zeladoria urbana (Secure DevOps & Cloud Computing)

Plataforma CitizenTech para registrar e acompanhar problemas do bairro (buraco, iluminação, descarte irregular, calçada, mobiliário).
Este repositório é a entrega da disciplina **Secure DevOps Tools & Cloud Computing — "Deploy Blindado"** (FIAP Global Solution 2026.2).

> ⚠️ **Dados 100% fictícios.** O MVP nasce com 40 ocorrências sintéticas (marcadas como "fictício" na tela). Não há fotos nem dados pessoais reais.

**URL pública do MVP:** http://172.173.103.106  ·  **Repositório:** https://github.com/victorasfur/bairrovivo-secure

---

## Ficha Técnica do MVP

| Item | Descrição |
|---|---|
| Nome | BairroVivo |
| Objetivo | Registrar, visualizar em mapa e acompanhar ocorrências de zeladoria urbana |
| Funcionalidades | Mapa + lista com filtros, registro de ocorrência, indicadores (total/abertas/resolvidas/categorias), API REST |
| Stack | Python 3.12 · FastAPI · SQLAlchemy · PostgreSQL 16 · HTML/JS + Leaflet |
| Container | Dockerfile multi-stage, usuário não-root, `read_only`, `cap_drop: ALL`, healthcheck |
| IaC | Terraform (Azure, região `centralus`): Resource Group, VNet, NSG, IP público, VM Ubuntu 24.04 (Standard_D2s_v3) |
| CI/CD | GitHub Actions: ruff + pytest → Gitleaks + Semgrep → build + Trivy + teste do compose → publica no GHCR → deploy |
| Observabilidade | Prometheus + Grafana (4 métricas de ouro) + alertas; logs JSON; `/health` |
| Segurança | Sem segredos no repo/imagem; segredos em GitHub Secrets e `.env` só na VM; SSH só do IP do admin; `/metrics` com token |
| Dados | Sintéticos (seed determinístico). Escopo do MVP: sem upload de fotos, sem login |
| Limitações | HTTP sem TLS (sem domínio); 1 VM sem alta disponibilidade; IA/CV/RPA/Big Data são de outras disciplinas |

## Endpoints

| Rota | Descrição |
|---|---|
| `GET /` | Interface web |
| `GET /health` | Health check (`status` + versão = SHA do commit) |
| `GET /api/ocorrencias?categoria=&status=` | Lista ocorrências |
| `POST /api/ocorrencias` | Cria ocorrência (validada com Pydantic) |
| `GET /api/resumo` | Totais por categoria/status |
| `GET /metrics` | Métricas Prometheus (exige `Authorization: Bearer <METRICS_TOKEN>`) |

## Rodar localmente

```bash
cp .env.example .env          # edite a senha e o token
docker compose up -d --build  # sobe app + Postgres
open http://localhost:8000
docker compose down           # (-v apaga também o banco)
```

Sem Docker (SQLite local): `pip install -r requirements-dev.txt && uvicorn app.main:app --reload` · testes: `pytest -q` · lint: `ruff check .`

## Pipeline (GitHub Actions)

`.github/workflows/ci-cd.yml` roda a cada push:

1. **test** — `ruff` + `pytest`
2. **security** — **Gitleaks** (segredos, histórico completo) e **Semgrep** (código)
3. **build** — build da imagem, **Trivy** (CRITICAL/HIGH), teste de subida com `docker compose up --wait`
4. **publicação** (só `main`) — imagem no GHCR (`:latest` e `:<sha>`)
5. **deploy** — a VM Azure puxa a imagem nova (cron de 1 min criado pelo Terraform) e o job confirma que o **SHA do commit** está respondendo em `/health`

**GitHub Secrets / Variables** (Settings → Secrets and variables → Actions):

| Nome | Tipo | Para quê |
|---|---|---|
| `METRICS_TOKEN` | Secret | Smoke test do `/metrics` protegido |
| `APP_URL` | Variable | `http://<IP-DA-VM>`, usada para confirmar o deploy |

> **Decisão de segurança:** o deploy é *pull* (a VM busca a imagem). Assim **não é preciso abrir a porta 22 para a internet** só para o GitHub entrar na VM.

Demonstração "barrado → corrigido": `./scripts/demo_segredo.sh barrar` e depois `./scripts/demo_segredo.sh corrigir`.

## Infraestrutura (Terraform / Azure)

```bash
az login
cd infra
cp terraform.tfvars.example terraform.tfvars   # preencha (arquivo ignorado pelo Git)
terraform init
terraform plan
terraform apply
terraform output app_url
```

- `terraform.tfvars`, `*.tfstate` e `.terraform/` **nunca** vão para o Git (`.gitignore`).
- O NSG libera só **80 (público)** e **22 apenas para `admin_cidr`**. A variável rejeita `0.0.0.0/0`.
- Destruir tudo: `terraform destroy` (para não gastar crédito).

## Observabilidade (Prometheus + Grafana)

```bash
cd monitoring
cp metrics_token.example metrics_token     # coloque o MESMO METRICS_TOKEN da VM
# edite prometheus.yml: troque SEU_IP_PUBLICO_DA_VM pelo IP da VM
docker compose up -d
```

- Grafana: <http://localhost:3000> (admin/admin) → dashboard **BairroVivo — 4 métricas de ouro**
- Prometheus: <http://localhost:9090> → *Alerts*
- Gerar tráfego: `./scripts/gerar_trafego.sh http://<IP>` · gerar erros: `./scripts/gerar_trafego.sh http://<IP> erros`
- Alertas: `BairroVivoForaDoAr`, `BairroVivoMuitosErros5xx`, `BairroVivoLatenciaAlta`

| Métrica de ouro | Consulta |
|---|---|
| Latência | `histogram_quantile(0.95, …http_request_duration_highr_seconds_bucket…)` |
| Tráfego | `sum(rate(http_requests_total[1m]))` |
| Erros | taxa de `status="5xx"` |
| Saturação | `process_cpu_seconds_total` e `process_resident_memory_bytes` |

## Backup, restore e recuperação

```bash
# backup (na VM)
docker exec bairrovivo-db-1 pg_dump -U bairrovivo bairrovivo > backup.sql
# restore
cat backup.sql | docker exec -i bairrovivo-db-1 psql -U bairrovivo bairrovivo
# recuperação total: terraform apply (recria a VM) -> cloud-init reinstala tudo -> o seed fictício é recarregado
```

Retenção: os dados são fictícios; backups de demonstração podem ser apagados ao fim da avaliação.

## Estrutura

```
app/            código da aplicação (FastAPI + front estático)
tests/          testes automatizados
Dockerfile      imagem multi-stage, não-root
docker-compose.yml
infra/          Terraform (Azure) + cloud-init
monitoring/     Prometheus, alertas e Grafana (dashboard provisionado)
scripts/        geração de tráfego, demo do Gitleaks, gerador do dashboard
docs/           arquitetura, LGPD, custo e modelo do relatório
.github/workflows/ci-cd.yml
```
