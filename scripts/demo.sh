#!/usr/bin/env bash
set -uo pipefail

if [ "$#" -ne 1 ]; then
  echo "Uso: $0 <nombre-instancia>"
  echo "Ejemplo: $0 demo-good"
  exit 64
fi

INSTANCE="$1"
CONFIG="configs/${INSTANCE}.yaml"
OUTPUT="outputs/${INSTANCE}"
ASSESSMENT="${OUTPUT}/assessment_summary.json"
SUMMARY="${OUTPUT}/summary.json"
DD_REPORT="${OUTPUT}/due_diligence_report.md"
ERROR_LOG="${OUTPUT}/error_log.txt"

print_line() {
  echo "================================================"
}

print_line
echo "ADVENTURE CAPITAL — Sistema de Valorización"
echo "Instancia: ${INSTANCE}"
print_line

echo "[1/2] Optimizando plan de crecimiento acelerado..."
uv run adventure-capital run --config "${CONFIG}" --output "${OUTPUT}"
RUN_STATUS=$?

if [ "${RUN_STATUS}" -ne 0 ]; then
  echo "❌ Falló la optimización de la instancia ${INSTANCE}."
  if [ -f "${ERROR_LOG}" ]; then
    echo "Contenido de ${ERROR_LOG}:"
    cat "${ERROR_LOG}"
  else
    echo "No se encontró ${ERROR_LOG}."
  fi
  exit "${RUN_STATUS}"
fi

if [ ! -f "${ASSESSMENT}" ]; then
  echo "❌ No se encontró ${ASSESSMENT}."
  exit 1
fi

VERDICT=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("due_diligence",{}).get("verdict") or d.get("verdict") or "N/A")' "${ASSESSMENT}")
VALUATION_MODE=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("due_diligence",{}).get("valuation_mode") or d.get("valuation_mode") or "N/A")' "${ASSESSMENT}")

if [ -f "${SUMMARY}" ]; then
  VAN=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); v=d.get("key_metrics",{}).get("van", d.get("van", "N/A")); print(f"USD {float(v):,.0f}" if isinstance(v,(int,float)) else v)' "${SUMMARY}")
else
  VAN="N/A"
fi

print_line
echo "RESULTADO DEL DIAGNÓSTICO"
echo "------------------------------------------------"
printf "Veredicto DD:     %s\n" "${VERDICT}"
printf "Modo valoración:  %s\n" "${VALUATION_MODE}"
printf "VAN determinista: %s\n" "${VAN}"
print_line

if [ "${VERDICT}" = "rejected_for_valuation" ] || [ "${VERDICT}" = "rejected_for_stochastic" ]; then
  echo "❌ Instancia rechazada — no se genera informe."
  if [ -f "${DD_REPORT}" ]; then
    head -30 "${DD_REPORT}"
  else
    echo "No se encontró ${DD_REPORT}."
  fi
  exit 0
fi

echo "[2/2] Generando informe de valorización..."
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
uv run adventure-capital report \
  --input "${OUTPUT}" \
  --document reports/valuation-base.yaml \
  --config "${CONFIG}" \
  --gate warn-ok --pdf
REPORT_STATUS=$?

if [ "${REPORT_STATUS}" -ne 0 ]; then
  echo "❌ Falló la generación del informe."
  exit "${REPORT_STATUS}"
fi

open "${OUTPUT}/report.html"

print_line
echo "✅ Listo. Informe disponible en:"
echo "   ${OUTPUT}/report.html"
print_line
