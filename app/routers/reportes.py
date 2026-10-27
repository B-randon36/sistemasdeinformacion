import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IndicadorKpi, ObjetivoEstrategico, IniciativaEstrategica, ModuloOdooArea, Periodo
from app.services.bsc_engine import recalcular_todo_el_bsc

router = APIRouter(prefix="/reportes", tags=["Reportes Ejecutivos BSC"])

@router.get("/consolidado")
def get_reporte_consolidado(
    periodo: Optional[str] = Query(None),
    perspectiva: Optional[str] = Query(None),
    modulo_odoo: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not periodo:
        p_act = db.query(Periodo).filter(Periodo.activo == True).first()
        periodo = p_act.codigo if p_act else "2026-10"

    bsc = recalcular_todo_el_bsc(db, periodo)

    # Filtrar indicadores
    kpis_q = db.query(IndicadorKpi)
    if perspectiva and perspectiva != "TODAS":
        kpis_q = kpis_q.join(ObjetivoEstrategico).filter(ObjetivoEstrategico.perspectiva == perspectiva)
    if modulo_odoo and modulo_odoo != "TODOS":
        kpis_q = kpis_q.filter(IndicadorKpi.modulo_odoo.ilike(f"%{modulo_odoo}%"))

    kpis = kpis_q.all()

    # Objetivos
    objs_q = db.query(ObjetivoEstrategico)
    if perspectiva and perspectiva != "TODAS":
        objs_q = objs_q.filter(ObjetivoEstrategico.perspectiva == perspectiva)
    objs = objs_q.all()

    # Iniciativas
    iniciativas = db.query(IniciativaEstrategica).all()

    return {
        "periodo": periodo,
        "resumen_ejecutivo": bsc,
        "total_kpis": len(kpis),
        "total_objetivos": len(objs),
        "kpis": [
            {
                "codigo": k.codigo,
                "nombre": k.nombre,
                "perspectiva": k.objetivo_rel.perspectiva if k.objetivo_rel else None,
                "objetivo": k.objetivo_rel.nombre if k.objetivo_rel else None,
                "modulo_odoo": k.modulo_odoo,
                "modelo_odoo": k.modelo_odoo,
                "meta": k.meta,
                "valor_actual": k.valor_actual,
                "unidad": k.unidad,
                "sentido": k.sentido,
                "porcentaje_cumplimiento": k.porcentaje_cumplimiento,
                "semaforo": k.semaforo,
                "responsable": k.responsable
            }
            for k in kpis
        ],
        "objetivos": [
            {
                "codigo": o.codigo,
                "nombre": o.nombre,
                "perspectiva": o.perspectiva,
                "modulo": o.modulo_rel.nombre_modulo_odoo if o.modulo_rel else None,
                "avance": o.avance_calculado,
                "prioridad": o.prioridad,
                "ponderacion": o.ponderacion,
                "responsable": o.responsable
            }
            for o in objs
        ],
        "iniciativas": [
            {
                "codigo": i.codigo,
                "nombre": i.nombre,
                "modulo": i.modulo_odoo,
                "presupuesto": i.presupuesto,
                "avance": i.porcentaje_avance,
                "estado": i.estado,
                "responsable": i.responsable
            }
            for i in iniciativas
        ]
    }

@router.get("/export-csv")
def exportar_csv(
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not periodo:
        p_act = db.query(Periodo).filter(Periodo.activo == True).first()
        periodo = p_act.codigo if p_act else "2026-10"

    recalcular_todo_el_bsc(db, periodo)
    kpis = db.query(IndicadorKpi).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=",")

    # Header
    writer.writerow([
        "Código KPI",
        "Nombre Indicador",
        "Perspectiva BSC",
        "Objetivo Estratégico",
        "Módulo Odoo 17",
        "Modelo Técnico Odoo",
        "Línea Base",
        "Meta",
        "Valor Obtenido",
        "Unidad",
        "Sentido",
        "% Cumplimiento",
        "Semáforo",
        "Responsable"
    ])

    for k in kpis:
        writer.writerow([
            k.codigo,
            k.nombre,
            k.objetivo_rel.perspectiva if k.objetivo_rel else "",
            k.objetivo_rel.nombre if k.objetivo_rel else "",
            k.modulo_odoo,
            k.modelo_odoo,
            k.linea_base,
            k.meta,
            k.valor_actual if k.valor_actual is not None else "SIN DATOS",
            k.unidad,
            k.sentido,
            f"{k.porcentaje_cumplimiento}%" if k.porcentaje_cumplimiento is not None else "N/A",
            k.semaforo,
            k.responsable
        ])

    csv_data = output.getvalue().encode("utf-8-sig")
    filename = f"BSC_AgroPeruvianFoods_{periodo}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
