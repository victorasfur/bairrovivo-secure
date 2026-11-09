"""Dados 100% FICTÍCIOS para demonstração (bairro de exemplo: Vila Mariana, SP)."""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Ocorrencia

CENTRO = (-23.5894, -46.6342)

MODELOS = {
    "buraco": [
        ("Buraco na faixa da direita", "Buraco profundo que atrapalha o trânsito."),
        ("Pavimento afundado", "Asfalto cedeu após a chuva."),
    ],
    "iluminacao": [
        ("Poste apagado", "Rua escura à noite, poste sem funcionar."),
        ("Lâmpada piscando", "Iluminação instável na esquina."),
    ],
    "descarte": [
        ("Entulho na calçada", "Sacos de entulho acumulados há dias."),
        ("Lixo descartado em terreno", "Descarte irregular de móveis e lixo."),
    ],
    "calcada": [
        ("Calçada quebrada", "Pedaço de calçada solto, risco de queda."),
        ("Obstrução na calçada", "Passagem bloqueada para cadeirantes."),
    ],
    "mobiliario": [
        ("Banco de praça quebrado", "Banco com ripas soltas."),
        ("Placa de rua caída", "Placa de sinalização no chão."),
    ],
}
PESOS_STATUS = [
    ("recebida", 6),
    ("em_analise", 5),
    ("encaminhada", 4),
    ("em_atendimento", 3),
    ("resolvida", 8),
    ("nao_procedente", 1),
]


def popular_se_vazio(db: Session, quantidade: int = 40) -> int:
    if db.scalar(select(func.count()).select_from(Ocorrencia)):
        return 0
    rng = random.Random(42)  # determinístico: mesmo resultado em todo ambiente
    agora = datetime.now(timezone.utc)
    status_pool = [s for s, p in PESOS_STATUS for _ in range(p)]
    for i in range(quantidade):
        cat = rng.choice(list(MODELOS))
        titulo, desc = rng.choice(MODELOS[cat])
        db.add(
            Ocorrencia(
                titulo=titulo,
                descricao=desc,
                categoria=cat,
                status=rng.choice(status_pool),
                latitude=CENTRO[0] + rng.uniform(-0.012, 0.012),
                longitude=CENTRO[1] + rng.uniform(-0.012, 0.012),
                alias=f"morador{i % 9 + 1}",
                origem="sintetico",
                criado_em=agora - timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 23)),
            )
        )
    db.commit()
    return quantidade
