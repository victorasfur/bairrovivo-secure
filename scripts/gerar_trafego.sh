#!/usr/bin/env bash
# Gera tráfego para o dashboard ter dados. Uso: ./scripts/gerar_trafego.sh http://IP_DA_VM [erros]
# Com o 2º argumento "erros", também chama /api/demo/erro (precisa DEMO_MODE=1 na VM) -> dispara alerta de 5xx.
URL="${1:?uso: $0 http://IP_DA_VM [erros]}"
for i in $(seq 1 ${N:-300}); do
  curl -s -o /dev/null "$URL/api/ocorrencias"
  curl -s -o /dev/null "$URL/api/resumo"
  [ "${2:-}" = "erros" ] && curl -s -o /dev/null "$URL/api/demo/erro"
  sleep 0.2
done
echo "fim"
