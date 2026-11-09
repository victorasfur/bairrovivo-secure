import os

os.environ["DATABASE_URL"] = "sqlite://"  # banco em memória nos testes
os.environ["METRICS_TOKEN"] = "token-de-teste"
os.environ["DEMO_MODE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_e_seed():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        resumo = c.get("/api/resumo").json()
        assert resumo["total"] >= 40  # dados fictícios carregados
        assert "fictícios" in resumo["aviso"]


def test_criar_e_filtrar_ocorrencia():
    with TestClient(app) as c:
        payload = {
            "titulo": "Poste apagado na rua teste",
            "categoria": "iluminacao",
            "latitude": -23.59,
            "longitude": -46.63,
        }
        r = c.post("/api/ocorrencias", json=payload)
        assert r.status_code == 201
        assert r.json()["status"] == "recebida"
        assert r.json()["origem"] == "cidadao"
        lista = c.get("/api/ocorrencias", params={"categoria": "iluminacao"}).json()
        assert any(o["titulo"] == payload["titulo"] for o in lista)


def test_validacao_rejeita_dados_invalidos():
    with TestClient(app) as c:
        ruim = {"titulo": "x", "categoria": "invalida", "latitude": 999, "longitude": 0}
        assert c.post("/api/ocorrencias", json=ruim).status_code == 422


def test_metrics_exige_token():
    with TestClient(app) as c:
        assert c.get("/metrics").status_code == 401
        r = c.get("/metrics", headers={"Authorization": "Bearer token-de-teste"})
        assert r.status_code == 200
        assert "http_requests_total" in r.text


def test_endpoint_de_erro_demo_gera_500():
    with TestClient(app) as c:
        assert c.get("/api/demo/erro").status_code == 500
