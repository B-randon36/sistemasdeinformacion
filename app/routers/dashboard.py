from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Periodo, IndicadorKpi, ObjetivoEstrategico, IniciativaEstrategica
from app.services.bsc_engine import (
    recalcular_todo_el_bsc,
    obtener_indicadores_requieren_atencion,
    obtener_tendencia_historica,
    obtener_desempeno_por_modulo_odoo
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Ejecutivo"])

@router.get("/metrics")
def get_dashboard_metrics(
    periodo: Optional[str] = Query(None, description="Código de período, ej. 2026-10"),
    modulo: Optional[str] = Query(None, description="Filtro de módulo Odoo"),
    responsable: Optional[str] = Query(None, description="Filtro de responsable"),
    db: Session = Depends(get_db)
):
    # Determinar período activo si no se especificó
    periodo_obj = None
    if periodo:
        periodo_obj = db.query(Periodo).filter(Periodo.codigo == periodo).first()
    if not periodo_obj:
        periodo_obj = db.query(Periodo).filter(Periodo.activo == True).first()
    
    periodo_cod = periodo_obj.codigo if periodo_obj else "2026-10"

    # Ejecutar consolidación
    bsc_data = recalcular_todo_el_bsc(db, periodo_cod)

    # Filtrar KPIs si hay filtros opcionales
    kpis_query = db.query(IndicadorKpi)
    if modulo and modulo != "TODOS":
        kpis_query = kpis_query.filter(IndicadorKpi.modulo_odoo.ilike(f"%{modulo}%"))
    if responsable and responsable != "TODOS":
        kpis_query = kpis_query.filter(IndicadorKpi.responsable.ilike(f"%{responsable}%"))

    kpis_filtrados = kpis_query.all()
    total_kpis = len(kpis_filtrados)
    total_objetivos = db.query(ObjetivoEstrategico).count()
    total_iniciativas = db.query(IniciativaEstrategica).count()

    # Indicadores que requieren atención
    atencion = obtener_indicadores_requieren_atencion(db)
    if modulo and modulo != "TODOS":
        atencion = [a for a in atencion if modulo.lower() in a["modulo_odoo"].lower()]

    # Tendencias y Desempeño por módulo
    tendencia = obtener_tendencia_historica(db)
    desempeno_modulos = obtener_desempeno_por_modulo_odoo(db)

    return {
        "periodo_actual": periodo_cod,
        "total_objetivos": total_objetivos,
        "total_kpis": total_kpis,
        "total_iniciativas": total_iniciativas,
        "cumplimiento_global": bsc_data["cumplimiento_global"],
        "total_cumplidos": bsc_data["semaforos"]["cumplidos"],
        "total_alerta": bsc_data["semaforos"]["alerta"],
        "total_criticos": bsc_data["semaforos"]["criticos"],
        "total_sin_datos": bsc_data["semaforos"]["sin_datos"],
        "perspectivas": bsc_data["perspectivas"],
        "desempeno_modulos": desempeno_modulos,
        "indicadores_atencion": atencion,
        "historico_tendencia": tendencia
    }
