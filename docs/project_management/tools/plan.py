"""Reproducible planning model. Standard library only; no production imports.

Run from any directory: python3 docs/project_management/tools/plan.py
Generates plan_data.json and evidence/plan_validation.json. Durations are working
days, intervals [ES, EF), effort is uniformly spread within each task.
Resource links are explicit FS constraints added only when capacity requires it.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = {
    "AP": {
        "name": "Alonso Peña",
        "role": "Responsable científico e integración",
        "capacity": 32,
        "rate": 0,
    },
    "AM": {
        "name": "Alejandro Maureira",
        "role": "Dirección y validación comercial",
        "capacity": 8,
        "rate": 15000,
    },
    "BE": {
        "name": "Empresa · backend",
        "role": "Arquitectura, datos, API y trabajos",
        "capacity": 32,
        "rate": 25000,
    },
    "FE": {
        "name": "Empresa · frontend",
        "role": "Interfaz y accesibilidad",
        "capacity": 32,
        "rate": 25000,
    },
    "UX": {
        "name": "Empresa · UX",
        "role": "Investigación y diseño",
        "capacity": 16,
        "rate": 25000,
    },
    "QA": {
        "name": "Empresa · QA",
        "role": "Pruebas independientes y aceptación",
        "capacity": 24,
        "rate": 25000,
    },
    "OP": {
        "name": "Empresa · operación",
        "role": "Despliegue, seguridad y respaldos",
        "capacity": 16,
        "rate": 25000,
    },
}
TASKS = []


def task(
    id,
    phase,
    module,
    title,
    days,
    effort,
    preds,
    deliverable,
    acceptance,
    priority="P0",
):
    dependencies = []
    for p in preds.split():
        ident, kind = p.split(":") if ":" in p else (p, "T")
        dependencies.append({"id": ident, "type": kind})
    TASKS.append(
        dict(
            id=id,
            wbs=f"{phase}.{sum(t['phase'] == phase for t in TASKS) + 1:02}",
            phase=phase,
            module=module,
            title=title,
            duration=days,
            effort=effort,
            dependencies=dependencies,
            deliverable=deliverable,
            acceptance=acceptance,
            priority=priority,
            optimistic=max(1, round(days * 0.75)),
            conservative=round(days * 1.5),
            status="No iniciada",
            progress=0,
        )
    )


# T technical, V acceptance/validation, C contractual. R added by capacity leveling.
task(
    "T01",
    1,
    "Dirección",
    "Confirmar segmento y problema pagable",
    5,
    {"AM": 8, "AP": 8},
    "",
    "Ficha de producto y exclusiones",
    "Alejandro aprueba un comprador inicial y 3 problemas priorizados",
)
task(
    "T02",
    1,
    "Ciencia",
    "Reproducir fallos y congelar línea base",
    5,
    {"AP": 28},
    "",
    "Casos reproducibles y métricas",
    "Guardar commit, entorno, 3 casos de referencia y fallos sin ocultarlos",
)
task(
    "T03",
    1,
    "Proveedor",
    "Preparar encargo y evaluar proveedor",
    10,
    {"AM": 12, "AP": 12},
    "T01:V",
    "Encargo técnico y matriz de evaluación",
    "Comparar 2 propuestas por entregables; código, cuentas y datos de Adventure Capital",
)
task(
    "T04",
    1,
    "Proveedor",
    "Cerrar contrato y reservar equipo",
    5,
    {"AM": 8, "AP": 4},
    "T03:C",
    "Contrato e hitos de aceptación",
    "Perfiles nominados; QA distinto del autor; propiedad, salida y garantía acordadas",
)
task(
    "T05",
    1,
    "Producto",
    "Entrevistar usuarios y levantar recorrido",
    10,
    {"UX": 24, "AM": 8, "AP": 8},
    "T04:C",
    "5 entrevistas y mapa de uso",
    "Al menos 3 emprendedores y 2 consultores; registrar evidencia y fricciones",
)
task(
    "T06",
    1,
    "Arquitectura",
    "Diseñar contratos del motor y fronteras",
    10,
    {"BE": 40, "AP": 24, "OP": 8},
    "T04:C T02",
    "Contrato versionado y ADR propuesto",
    "Definir entrada, salida, estados solver, ownership y errores; revisión de Alonso",
)
task(
    "T07",
    1,
    "Producto",
    "Aprobar MVP y criterios de salida",
    3,
    {"AM": 4, "AP": 4, "UX": 4},
    "T05:V T06:V",
    "Backlog contractual aprobado",
    "Distinguir piloto asistido y SaaS; aprobar límites y objetivos medibles",
)
task(
    "T08",
    2,
    "Ciencia",
    "Definir rangos y unidades por variable",
    5,
    {"AP": 28},
    "T02",
    "Diccionario de validación",
    "Finitud, signos, tasas, periodicidad y supuestos con ejemplos válidos/ inválidos",
)
task(
    "T09",
    2,
    "Ciencia",
    "Cerrar brechas de validación de entradas",
    10,
    {"AP": 48},
    "T08",
    "Validador y pruebas negativas",
    "NaN, churn >1, alpha >1 y adquisición negativa rechazados o justificados",
)
task(
    "T10",
    2,
    "Ciencia",
    "Conciliar etapa fija y canales MILP",
    10,
    {"AP": 48},
    "T09",
    "Contrato de adquisición fija",
    "CAC y EBITDA meses 1–12 coinciden bajo mix fijo; decidir qué mix se optimiza",
)
task(
    "T11",
    2,
    "Ciencia",
    "Acordar caja, financiación y DCF",
    10,
    {"AP": 40, "AM": 8},
    "T08",
    "Nota metodológica aprobada",
    "Distinguir VAN/EV, suelo −VC, financiación mínima y FCFF; no prometer equivalencias",
)
task(
    "T12",
    2,
    "Ciencia",
    "Alinear valoración y unit economics",
    10,
    {"AP": 48},
    "T10 T11:V",
    "Métricas trazables y regresión",
    "Casos manuales multiservicio, terminal y horizonte parcial reconciliados",
)
task(
    "T13",
    2,
    "Ciencia",
    "Revisar paridad determinista y estocástica",
    10,
    {"AP": 48},
    "T12",
    "Matriz M1/M4 y límites de uso",
    "Escenario degenerado comparable; diferencias de decisión y objetivo declaradas",
)
task(
    "T14",
    2,
    "Ciencia",
    "Validar escenarios fuera de muestra",
    10,
    {"AP": 40},
    "T13",
    "Informe de estabilidad y tiempos",
    "Semillas separadas, CVaR y sensibilidad al tamaño muestral; sin afirmar garantía robusta",
)
task(
    "T15",
    2,
    "Ciencia",
    "Congelar versión científica para piloto",
    5,
    {"AP": 20, "QA": 12},
    "T12 T14:V",
    "Versión y conjunto de casos patrón",
    "3 casos patrón reproducibles; errores materiales cerrados o módulo excluido",
)
task(
    "T16",
    2,
    "Ciencia",
    "Diseñar comparación y negociación de supuestos",
    5,
    {"AP": 20, "AM": 4},
    "T12",
    "Contrato de escenarios",
    "Comparar versiones con mismas unidades, horizonte y método; rastrear cambios",
)
task(
    "T17",
    3,
    "UX",
    "Prototipar captura y explicación de resultados",
    10,
    {"UX": 32, "AP": 8},
    "T07:V",
    "Prototipo navegable",
    "Alta, datos, ejecutar, error, comparar y descargar cubiertos",
)
task(
    "T18",
    3,
    "UX",
    "Probar prototipo con cinco usuarios",
    5,
    {"UX": 12, "AM": 4, "AP": 4},
    "T17",
    "Registro de tareas y ajustes",
    "4/5 completan captura guiada sin ayuda crítica; registrar tiempo y errores",
)
task(
    "T19",
    3,
    "Infraestructura",
    "Preparar CI, entornos y secretos",
    10,
    {"OP": 28, "BE": 12},
    "T06",
    "Staging y pipeline de despliegue",
    "Instalación limpia, lock reproducible, escaneo dependencias y rollback básico",
)
task(
    "T20",
    3,
    "Backend",
    "Crear organizaciones, usuarios y permisos",
    10,
    {"BE": 56, "QA": 8},
    "T06 T07:V",
    "Modelo multiusuario y pruebas",
    "Administrador, analista y lector; acceso denegado entre organizaciones",
)
task(
    "T21",
    3,
    "Backend",
    "Persistir escenarios y versiones inmutables",
    10,
    {"BE": 56, "AP": 8},
    "T20 T16",
    "Persistencia y migración inicial",
    "Versión/hash del input y motor; trazabilidad de autor y sin sobrescribir ejecuciones",
)
task(
    "T22",
    3,
    "Backend",
    "Implementar cola y ciclo de trabajos",
    10,
    {"BE": 56, "OP": 12},
    "T20 T19",
    "Worker aislado y estados de ejecución",
    "Timeout, cancelación, reintento idempotente, pérdida de worker y recuperación probados",
)
task(
    "T23",
    3,
    "Backend",
    "Integrar motor y artefactos privados",
    10,
    {"BE": 48, "AP": 16, "OP": 8},
    "T21 T22 T15:V",
    "Ejecución completa desde API",
    "Cada job usa espacio aislado; solver status visible; descargas autorizadas",
)
task(
    "T24",
    3,
    "Frontend",
    "Implementar acceso y navegación por perfil",
    10,
    {"FE": 48, "UX": 8},
    "T18:V T20",
    "Interfaz autenticada",
    "Estados vacíos y errores; rol lector no edita ni ejecuta",
)
task(
    "T25",
    3,
    "Frontend",
    "Implementar formulario con validación guiada",
    10,
    {"FE": 56, "UX": 8, "AP": 12},
    "T24 T09",
    "Captura validada y ayudas",
    "Unidades explícitas, errores junto al campo, import/export no pierde valores",
)
task(
    "T26",
    3,
    "Frontend",
    "Integrar ejecución y seguimiento del trabajo",
    10,
    {"FE": 48, "BE": 8},
    "T25 T22",
    "Pantalla de ejecuciones",
    "Salir del navegador no pierde trabajo; progreso y errores accionables",
)
task(
    "T27",
    3,
    "Frontend",
    "Integrar resultados, informe y comparación",
    10,
    {"FE": 56, "AP": 12, "UX": 8},
    "T26 T23",
    "Recorrido financiero completo",
    "Comparar 2 escenarios; distinguir resultado factible y diagnóstico; exportar",
)
task(
    "T28",
    3,
    "Seguridad",
    "Sanear HTML, archivos y generación PDF",
    10,
    {"BE": 32, "OP": 16, "QA": 16},
    "T23",
    "Render aislado y validado",
    "Pruebas de escape, traversal, URLs remotas y límites de tamaño; sin fuga entre casos",
)
task(
    "T29",
    3,
    "Reportes",
    "Asegurar exportaciones y paridad de cifras",
    10,
    {"AP": 28, "QA": 24, "BE": 8},
    "T27 T28",
    "HTML/PDF/CSV/XLSX consistentes",
    "Mismos totales y unidades; backend PDF y dependencias en entorno limpio",
)
task(
    "T30",
    3,
    "Consumo",
    "Agregar límites y registro de consumo",
    5,
    {"BE": 24, "OP": 8},
    "T23",
    "Cuotas y ledger de uso",
    "Un trabajo idempotente se cuenta una vez; límite de concurrencia y de tamaño",
)
task(
    "T31",
    3,
    "Operación",
    "Respaldos, alertas y recuperación",
    10,
    {"OP": 28, "QA": 12},
    "T23 T19",
    "Runbook y restauración probada",
    "RPO 24h/RTO 8h como objetivo inicial; restaurar staging y registrar tiempo",
)
task(
    "T32",
    3,
    "Privacidad",
    "Definir datos, retención y consentimiento",
    10,
    {"AM": 8, "OP": 16, "BE": 8},
    "T07:V",
    "Política y contrato de tratamiento",
    "Inventario de datos; bajas/exportación; revisión jurídica externa requerida",
)
task(
    "T33",
    3,
    "Comercial",
    "Diseñar oferta, precio piloto y cobro manual",
    10,
    {"AM": 12, "AP": 4},
    "T07:V",
    "Oferta de piloto y criterios de conversión",
    "Definir comprador, servicio, límites, factura y soporte sin cobro API automático",
)
task(
    "T34",
    4,
    "QA",
    "Pruebas de integración y aislamiento",
    10,
    {"QA": 40, "BE": 16, "AP": 12},
    "T29 T30 T31 T32:V",
    "Informe QA y defectos",
    "Dos organizaciones, autorización por objeto y jobs concurrentes; sin defectos críticos",
)
task(
    "T35",
    4,
    "QA",
    "Pruebas de carga y presupuesto de ejecución",
    10,
    {"QA": 32, "OP": 20, "BE": 8},
    "T34",
    "Perfil CPU/RAM/tiempo y límites",
    "Medir 3 tamaños y 5 jobs; límites evitan OOM; cola mantiene API disponible",
)
task(
    "T36",
    4,
    "UX",
    "Validar accesibilidad y comprensión",
    10,
    {"UX": 24, "FE": 16, "AM": 4},
    "T27",
    "Prueba de uso y backlog corregido",
    "4/5 explican resultado y supuestos; teclado, contraste y textos revisados",
)
task(
    "T37",
    4,
    "Seguridad",
    "Revisión de seguridad previa al piloto",
    5,
    {"OP": 16, "QA": 16, "BE": 8},
    "T34 T28",
    "Checklist y revisión independiente",
    "Cero críticos/altos abiertos de aislamiento, secretos, archivos y autorización",
)
task(
    "T38",
    4,
    "Piloto",
    "Autorizar piloto con datos reales",
    2,
    {"AM": 2, "AP": 4, "QA": 4},
    "T35:V T36:V T37:V T33",
    "Acta go/no-go",
    "Condiciones contractuales y privacidad aceptadas; fallback a piloto asistido",
)
task(
    "T39",
    4,
    "Piloto",
    "Ejecutar primera ronda con tres organizaciones",
    10,
    {"AP": 24, "AM": 12, "UX": 12, "QA": 12},
    "T38:V",
    "3 casos completos y entrevistas",
    "Medir finalización, tiempo, exactitud y disposición a pagar; consentimiento documentado",
)
task(
    "T40",
    4,
    "Producto",
    "Corregir defectos del piloto",
    10,
    {"BE": 32, "FE": 32, "AP": 24, "QA": 24},
    "T39:V",
    "Versión corregida",
    "Todos los bloqueantes de captura, cálculo y exportación cerrados y retesteados",
)
task(
    "T41",
    4,
    "Piloto",
    "Repetir piloto y confirmar valor comercial",
    10,
    {"AP": 20, "AM": 12, "UX": 12, "QA": 12},
    "T40",
    "Resultados de segunda ronda",
    "3 organizaciones terminan; registrar aceptación y objeciones de compra",
)
task(
    "T42",
    5,
    "Comercial",
    "Preparar y negociar primera venta",
    10,
    {"AM": 16, "AP": 8},
    "T39:V T33",
    "Propuesta y negociación documentada",
    "Oferta enviada por Alejandro; objetivo 1 contrato pagado, sin garantizar decisión del cliente",
)
task(
    "T43",
    5,
    "Producto",
    "Resolver pendientes de experiencia y soporte",
    10,
    {"FE": 40, "UX": 16, "QA": 16},
    "T41:V",
    "Interfaz consolidada y ayuda",
    "Recorrido principal sin asistencia técnica; mensajes y soporte consistentes",
)
task(
    "T44",
    5,
    "Operación",
    "Transferir operación y mantenimiento",
    10,
    {"OP": 24, "BE": 16, "AP": 16},
    "T40 T31",
    "Runbooks, accesos y capacitación",
    "Alonso despliega y restaura sin proveedor; cuentas corporativas, SBOM y manual",
)
task(
    "T45",
    5,
    "QA",
    "Validar versión candidata y recuperación",
    5,
    {"QA": 24, "AP": 8, "OP": 8},
    "T43 T44 T37",
    "Informe final de calidad",
    "Suite, instalación limpia, migración, rollback y 3 casos patrón pasan",
)
task(
    "T46",
    5,
    "Comercial",
    "Aprobar lanzamiento y continuidad",
    3,
    {"AM": 4, "AP": 4, "OP": 4},
    "T45:V T42:V",
    "Acta de entrega comercial",
    "Alejandro acepta alcance, soporte, obligaciones y costos; registrar venta o causa de no conversión",
)
task(
    "T47",
    5,
    "Operación",
    "Acompañar primeras operaciones y cierre",
    10,
    {"OP": 16, "BE": 8, "AP": 16, "AM": 4, "QA": 8},
    "T46:V",
    "Cierre y backlog posterior",
    "Dos semanas de operación revisadas; dueño por incidente y mantenimiento contratado o asumido",
)


def cpm(tasks, ignore_resource=False, duration_key="duration"):
    ids = {t["id"] for t in tasks}
    if len(ids) != len(tasks):
        raise ValueError("Duplicate IDs")
    todo = {t["id"]: t for t in tasks}
    out, successors = {}, defaultdict(list)
    while todo:
        ready = [
            t
            for t in todo.values()
            if all(
                p["id"] in out
                for p in t["dependencies"]
                if not (ignore_resource and p["type"] == "R")
            )
        ]
        if not ready:
            raise ValueError("Cycle or unknown predecessor")
        for t in ready:
            deps = [
                p
                for p in t["dependencies"]
                if not (ignore_resource and p["type"] == "R")
            ]
            es = max([out[p["id"]]["ef"] for p in deps] or [0])
            out[t["id"]] = dict(es=es, ef=es + t[duration_key])
            for p in deps:
                successors[p["id"]].append(t["id"])
            del todo[t["id"]]
    finish = max(x["ef"] for x in out.values())
    by_id = {t["id"]: t for t in tasks}
    for ident in reversed(list(out)):
        row = out[ident]
        row["lf"] = min([out[s]["ls"] for s in successors[ident]] or [finish])
        row["ls"] = row["lf"] - by_id[ident][duration_key]
        row["float"] = row["ls"] - row["es"]
    return out, finish


def level(tasks):
    """Serial schedule generation; record actual resource conflicts as FS edges.

    Heuristic, not optimal RCPSP. Task order is a transparent priority decision.
    No task is split. Collaborator effort is included in the capacity check.
    """
    scheduled = {}
    remaining = list(tasks)
    while remaining:
        ready = [
            t for t in remaining if all(d["id"] in scheduled for d in t["dependencies"])
        ]
        if not ready:
            raise ValueError("Cycle/unknown predecessor")
        t = ready[0]
        for res, hours in t["effort"].items():
            assert hours / t["duration"] <= RESOURCES[res]["capacity"] / 5, (
                t["id"],
                res,
            )
        start = max([scheduled[d["id"]][1] for d in t["dependencies"]] or [0])
        while True:
            blocking = []
            for day in range(start, start + t["duration"]):
                for res, hours in t["effort"].items():
                    active = [
                        x
                        for x in tasks
                        if x["id"] in scheduled
                        and scheduled[x["id"]][0] <= day < scheduled[x["id"]][1]
                        and res in x["effort"]
                    ]
                    load = sum(x["effort"][res] / x["duration"] for x in active)
                    if (
                        load + hours / t["duration"]
                        > RESOURCES[res]["capacity"] / 5 + 1e-8
                    ):
                        blocking.extend(active)
            if not blocking:
                break
            blocker = min(blocking, key=lambda x: scheduled[x["id"]][1])
            if blocker["id"] not in [d["id"] for d in t["dependencies"]]:
                t["dependencies"].append({"id": blocker["id"], "type": "R"})
            start = max(start, scheduled[blocker["id"]][1])
        scheduled[t["id"]] = (start, start + t["duration"])
        remaining.remove(t)
    return scheduled


def main():
    # Peak reserved capacity, not a full-time retainer for every profile.
    for key, capacity in {
        "AP": 36,
        "AM": 10,
        "BE": 38,
        "FE": 40,
        "QA": 32,
        "OP": 24,
        "UX": 20,
    }.items():
        RESOURCES[key]["capacity"] = capacity
    # Integration uses agreed contracts/mocks before scientific sign-off. The
    # stochastic investigation does not gate the deterministic commercial MVP.
    changes = {
        "T01": {"effort": {"AM": 6, "AP": 4}},
        "T03": {"duration": 5, "effort": {"AM": 6, "AP": 6}},
        "T04": {"duration": 3, "effort": {"AM": 4, "AP": 2}},
        "T08": {"effort": {"AP": 24}},
        "T11": {"duration": 5, "effort": {"AP": 20, "AM": 4}},
        "T15": {"dependencies": [{"id": "T12", "type": "V"}]},
        "T16": {
            "dependencies": [{"id": "T06", "type": "T"}, {"id": "T08", "type": "T"}]
        },
        "T23": {
            "dependencies": [{"id": "T21", "type": "T"}, {"id": "T22", "type": "T"}]
        },
        "T28": {
            "dependencies": [{"id": "T06", "type": "T"}, {"id": "T19", "type": "T"}]
        },
        "T30": {"dependencies": [{"id": "T22", "type": "T"}]},
        "T31": {
            "dependencies": [{"id": "T21", "type": "T"}, {"id": "T19", "type": "T"}]
        },
        "T35": {"duration": 5, "effort": {"QA": 20, "OP": 12, "BE": 4}},
        "T34": {"duration": 8},
        "T39": {"duration": 5, "effort": {"AP": 24, "AM": 8, "UX": 12, "QA": 12}},
        "T41": {"duration": 5, "effort": {"AP": 20, "AM": 8, "UX": 12, "QA": 12}},
        "T37": {"effort": {"OP": 12, "QA": 12, "BE": 4}},
        "T38": {
            "dependencies": [
                {"id": p, "type": "V"} for p in ["T15", "T35", "T36", "T37", "T33"]
            ]
        },
        "T43": {"duration": 5, "effort": {"FE": 28, "UX": 8, "QA": 12}},
    }
    for t in TASKS:
        t.update(changes.get(t["id"], {}))
        t["optimistic"] = max(1, round(t["duration"] * 0.75))
        t["conservative"] = round(t["duration"] * 1.5)
    # Perform the non-gating stochastic work after scientific acceptance. It
    # remains important but cannot displace the contracts needed by the vendor.
    priority_order = [
        "T01",
        "T02",
        "T03",
        "T04",
        "T08",
        "T05",
        "T06",
        "T07",
        "T16",
        "T09",
        "T10",
        "T11",
        "T12",
        "T15",
    ]
    TASKS.sort(
        key=lambda t: (
            priority_order.index(t["id"])
            if t["id"] in priority_order
            else 100 + int(t["id"][1:])
        )
    )
    advanced = [t for t in TASKS if t["id"] in ["T13", "T14"]]
    TASKS[:] = [t for t in TASKS if t not in advanced] + advanced
    logical, logical_finish = cpm(TASKS)
    schedule = level(TASKS)
    network, finish = cpm(TASKS)
    for t in TASKS:
        t.update(network[t["id"]])
        assert (t["es"], t["ef"]) == schedule[t["id"]]
        t["hours"] = sum(t["effort"].values())
        t["owner"] = max(t["effort"], key=t["effort"].get)
    daily = {r: [0.0] * finish for r in RESOURCES}
    for t in TASKS:
        for r, h in t["effort"].items():
            for d in range(t["es"], t["ef"]):
                daily[r][d] += h / t["duration"]
    allocation = {
        r: dict(
            hours=round(sum(load), 2),
            peak_week=round(max(sum(load[i : i + 5]) for i in range(0, finish, 5)), 2),
            peak_day=round(max(load), 2),
        )
        for r, load in daily.items()
    }
    for r, a in allocation.items():
        assert a["peak_day"] <= RESOURCES[r]["capacity"] / 5 + 1e-6, (r, a)
    paths = []

    def trace(ident, path):
        t = next(x for x in TASKS if x["id"] == ident)
        critical_preds = [
            d["id"]
            for d in t["dependencies"]
            if network[d["id"]]["float"] == 0 and network[d["id"]]["ef"] == t["es"]
        ]
        if not critical_preds:
            paths.append([ident] + path)
        for p in critical_preds:
            trace(p, [ident] + path)

    for t in TASKS:
        if t["ef"] == finish and t["float"] == 0:
            trace(t["id"], [])
    totals = defaultdict(float)
    for t in TASKS:
        totals[t["module"]] += t["hours"]
    validation = dict(
        task_count=len(TASKS),
        logical_days=logical_finish,
        leveled_days=finish,
        optimistic_days=cpm(TASKS, duration_key="optimistic")[1],
        conservative_days=cpm(TASKS, duration_key="conservative")[1],
        critical_paths=paths,
        allocation=allocation,
        module_hours=totals,
        total_hours=sum(t["hours"] for t in TASKS),
        cycles=0,
        resource_links=sum(d["type"] == "R" for t in TASKS for d in t["dependencies"]),
        max_predecessors=max(len(t["dependencies"]) for t in TASKS),
    )
    data = dict(
        start_date="2026-11-02",
        months=8,
        resources=RESOURCES,
        tasks=TASKS,
        validation=validation,
    )
    ROOT.mkdir(exist_ok=True)
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "plan_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    (ROOT / "evidence" / "plan_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
