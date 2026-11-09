"""Gera monitoring/grafana/dashboards/bairrovivo.json (4 métricas de ouro)."""
import json
import pathlib

DS = {"type": "prometheus", "uid": "prometheus"}

def painel(pid, titulo, expr, x, y, w=8, h=8, unit="short", tipo="timeseries", legenda="", extra=None):
    p = {
        "id": pid, "title": titulo, "type": tipo, "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [{"refId": "A", "datasource": DS, "expr": expr, "legendFormat": legenda}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
    }
    if extra:
        p.update(extra)
    return p

stat_up = painel(
    1, "Status do MVP", 'min(up{job="bairrovivo"})', 0, 0, w=6, h=4, tipo="stat",
    extra={
        "options": {"colorMode": "background", "graphMode": "none", "reduceOptions": {"calcs": ["lastNotNull"]}},
        "fieldConfig": {"defaults": {
            "mappings": [{"type": "value", "options": {
                "0": {"text": "FORA DO AR", "color": "red"}, "1": {"text": "NO AR", "color": "green"}}}],
            "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]},
        }, "overrides": []},
    },
)
alertas = painel(
    2, "Alertas disparando agora", 'ALERTS{alertstate="firing"}', 6, 0, w=18, h=4, tipo="table",
    extra={"transformations": [{"id": "organize", "options": {"excludeByName": {"Time": True, "Value": True, "__name__": True}}}]},
)
paineis = [
    stat_up, alertas,
    painel(3, "1) Latência p95 (s)", 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_highr_seconds_bucket{job="bairrovivo"}[2m])))', 0, 4, unit="s", legenda="p95"),
    painel(4, "2) Tráfego (req/s)", 'sum(rate(http_requests_total{job="bairrovivo"}[1m]))', 8, 4, unit="reqps", legenda="req/s"),
    painel(5, "3) Erros 5xx (%)", '100 * (sum(rate(http_requests_total{job="bairrovivo",status="5xx"}[1m])) or vector(0)) / sum(rate(http_requests_total{job="bairrovivo"}[1m]))', 16, 4, unit="percent", legenda="% 5xx"),
    painel(6, "4a) Saturação: CPU do processo (%)", '100 * rate(process_cpu_seconds_total{job="bairrovivo"}[1m])', 0, 12, w=12, unit="percent", legenda="CPU"),
    painel(7, "4b) Saturação: memória (bytes)", 'process_resident_memory_bytes{job="bairrovivo"}', 12, 12, w=12, unit="bytes", legenda="RSS"),
]
dash = {
    "uid": "bairrovivo-golden", "title": "BairroVivo - 4 métricas de ouro", "tags": ["bairrovivo"],
    "timezone": "browser", "schemaVersion": 39, "version": 1, "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"}, "panels": paineis,
}
out = pathlib.Path(__file__).resolve().parent.parent / "monitoring/grafana/dashboards/bairrovivo.json"
out.write_text(json.dumps(dash, indent=2, ensure_ascii=False), encoding="utf-8")
print("gerado", out)
