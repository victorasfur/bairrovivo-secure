#!/usr/bin/env bash
# Prepara a demonstração "pipeline barrado" -> "pipeline corrigido" (print do ❌ e do ✅).
# 1) ./scripts/demo_segredo.sh barrar    cria branch com segredo FALSO e faz push (o Gitleaks deve falhar)
# 2) ./scripts/demo_segredo.sh corrigir  remove o commit com o segredo e faz push forçado (pipeline verde)
set -euo pipefail
BR=demo/segredo-vazado
case "${1:-}" in
  barrar)
    git checkout -b "$BR"
    P1="xK9mQ2vL8pR4tN7w"; P2="Z3yB6cD1fG5hJ0sA"
    printf 'api_key = "%s%s"\n' "$P1" "$P2" > config_demo.py
    git add config_demo.py
    git commit -m "demo: commit com segredo falso (deve ser barrado)"
    git push -u origin "$BR"
    echo "Abra Actions > job 'security' e tire print do ❌"
    ;;
  corrigir)
    git reset --hard HEAD~1
    git push --force origin "$BR"
    echo "Abra Actions > job 'security' e tire print do ✅ (histórico limpo)"
    ;;
  *) echo "uso: $0 barrar|corrigir"; exit 1 ;;
esac
