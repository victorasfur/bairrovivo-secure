from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

CATEGORIAS = ("buraco", "iluminacao", "descarte", "calcada", "mobiliario")
STATUS = (
    "recebida",
    "em_analise",
    "encaminhada",
    "em_atendimento",
    "resolvida",
    "nao_procedente",
)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text, default="")
    categoria: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="recebida", index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    alias: Mapped[str] = mapped_column(String(40), default="anônimo")
    # "sintetico" = dado fictício de demonstração; "cidadao" = registrado pela tela
    origem: Mapped[str] = mapped_column(String(12), default="cidadao")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
