import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import CATEGORIAS, STATUS, Ocorrencia
from .seed import popular_se_vazio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION = os.getenv("GIT_SHA", "local")

# Logs estruturados (uma linha JSON por requisição) -> facilitam busca/observabilidade
logger = logging.getLogger("bairrovivo")
logging.basicConfig(level=logging.INFO, format="%(message)s")

Categoria = Literal["buraco", "iluminacao", "descarte", "calcada", "mobiliario"]


class OcorrenciaIn(BaseModel):
    titulo: str = Field(min_length=5, max_length=120)
    descricao: str = Field(default="", max_length=1000)
    categoria: Categoria
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    alias: str = Field(default="anônimo", max_length=40)


class OcorrenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str
    categoria: str
    status: str
    latitude: float
    longitude: float
    alias: str
    origem: str
    criado_em: datetime


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        criadas = popular_se_vazio(db)
    logger.info(json.dumps({"event": "startup", "version": VERSION, "seed": criadas}))
    yield


app = FastAPI(title="BairroVivo (MVP acadêmico)", version=VERSION, lifespan=lifespan)

Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app)

CSP = (
    "default-src 'self'; "
    "script-src 'self' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://unpkg.com; "
    "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
    "connect-src 'self'"
)


@app.middleware("http")
async def log_e_cabecalhos(request: Request, call_next):
    inicio = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - inicio) * 1000, 1)
    if request.url.path not in ("/health", "/metrics"):
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "ms": ms,
                }
            )
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = CSP
    return response


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "version": VERSION}


@app.get("/metrics", include_in_schema=False)
def metrics(authorization: str | None = Header(default=None)):
    token = os.getenv("METRICS_TOKEN", "")
    if token and not hmac.compare_digest(authorization or "", f"Bearer {token}"):
        raise HTTPException(status_code=401, detail="não autorizado")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/ocorrencias", response_model=list[OcorrenciaOut])
def listar(
    categoria: Categoria | None = None,
    status: str | None = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
):
    q = select(Ocorrencia).order_by(Ocorrencia.criado_em.desc()).limit(500)
    if categoria:
        q = q.where(Ocorrencia.categoria == categoria)
    if status:
        q = q.where(Ocorrencia.status == status)
    return db.scalars(q).all()


@app.post("/api/ocorrencias", response_model=OcorrenciaOut, status_code=201)
def criar(dados: OcorrenciaIn, db: Session = Depends(get_db)):
    oc = Ocorrencia(**dados.model_dump(), status="recebida", origem="cidadao")
    db.add(oc)
    db.commit()
    return oc


@app.get("/api/resumo")
def resumo(db: Session = Depends(get_db)):
    por_cat = dict(db.execute(select(Ocorrencia.categoria, func.count()).group_by(Ocorrencia.categoria)).all())
    por_status = dict(db.execute(select(Ocorrencia.status, func.count()).group_by(Ocorrencia.status)).all())
    total = sum(por_cat.values())
    return {
        "total": total,
        "por_categoria": {c: por_cat.get(c, 0) for c in CATEGORIAS},
        "por_status": {s: por_status.get(s, 0) for s in STATUS},
        "aviso": "Dados de demonstração fictícios - projeto acadêmico FIAP.",
    }


@app.get("/api/demo/erro", include_in_schema=False)
def gerar_erro():
    """Gera um HTTP 500 de propósito para demonstrar o alerta de erros (só com DEMO_MODE=1)."""
    if os.getenv("DEMO_MODE") != "1":
        raise HTTPException(status_code=404)
    raise HTTPException(status_code=500, detail="erro de demonstração")


app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))
