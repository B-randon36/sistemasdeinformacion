from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IndicadorKpi, MedicionKpi, ObjetivoEstrategico
from app.schemas import KpiCreate, KpiUpdate, KpiResponse
from app.services.bsc_engine import recalcular_kpi, recalcular_objetivo, recalcular_todo_el_bsc

router = APIRouter(prefix="/kpis", tags=["Indicadores KPI"])

@router.get("", response_model=List[KpiResponse])
def get_kpis(
    objetivo_id: Optional[int] = Query(None),
    perspectiva: Optional[str] = Query(None),
    modulo_odoo: Optional[str] = Query(None),
    semaforo: Optional[str] = Query(None),
    sentido: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(IndicadorKpi)

    if objetivo_id:
        query = query.filter(IndicadorKpi.objetivo_id == objetivo_id)
    if perspectiva and perspectiva != "TODAS":
        query = query.join(ObjetivoEstrategico).filter(ObjetivoEstrategico.perspectiva == perspectiva)
    if modulo_odoo and modulo_odoo != "TODOS":
        query = query.filter(IndicadorKpi.modulo_odoo.ilike(f"%{modulo_odoo}%"))
    if semaforo and semaforo != "TODOS":
        query = query.filter(IndicadorKpi.semaforo == semaforo)
    if sentido and sentido != "TODOS":
        query = query.filter(IndicadorKpi.sentido == sentido)
    if search:
        query = query.filter(
            (IndicadorKpi.nombre.ilike(f"%{search}%")) |
            (IndicadorKpi.codigo.ilike(f"%{search}%")) |
            (IndicadorKpi.modelo_odoo.ilike(f"%{search}%")) |
            (IndicadorKpi.responsable.ilike(f"%{search}%"))
        )

    kpis = query.all()
    resultado = []
    for k in kpis:
        resultado.append({
            "id": k.id,
            "codigo": k.codigo,
            "nombre": k.nombre,
            "descripcion": k.descripcion,
            "formula": k.formula,
            "unidad": k.unidad,
            "objetivo_id": k.objetivo_id,
            "modulo_odoo": k.modulo_odoo,
            "modelo_odoo": k.modelo_odoo,
            "responsable": k.responsable,
            "frecuencia": k.frecuencia,
            "linea_base": k.linea_base,
            "meta": k.meta,
            "sentido": k.sentido,
            "rango_min": k.rango_min,
            "rango_max": k.rango_max,
            "umbral_verde": k.umbral_verde,
            "umbral_amarillo": k.umbral_amarillo,
            "valor_actual": k.valor_actual,
            "porcentaje_cumplimiento": k.porcentaje_cumplimiento,
            "semaforo": k.semaforo,
            "mediciones_count": len(k.mediciones),
            "perspectiva": k.objetivo_rel.perspectiva if k.objetivo_rel else None,
            "objetivo_nombre": k.objetivo_rel.nombre if k.objetivo_rel else None
        })
    return resultado

@router.get("/{id}", response_model=KpiResponse)
def get_kpi_by_id(id: int, db: Session = Depends(get_db)):
    k = db.query(IndicadorKpi).filter(IndicadorKpi.id == id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Indicador KPI no encontrado.")

    return {
        "id": k.id,
        "codigo": k.codigo,
        "nombre": k.nombre,
        "descripcion": k.descripcion,
        "formula": k.formula,
        "unidad": k.unidad,
        "objetivo_id": k.objetivo_id,
        "modulo_odoo": k.modulo_odoo,
        "modelo_odoo": k.modelo_odoo,
        "responsable": k.responsable,
        "frecuencia": k.frecuencia,
        "linea_base": k.linea_base,
        "meta": k.meta,
        "sentido": k.sentido,
        "rango_min": k.rango_min,
        "rango_max": k.rango_max,
        "umbral_verde": k.umbral_verde,
        "umbral_amarillo": k.umbral_amarillo,
        "valor_actual": k.valor_actual,
        "porcentaje_cumplimiento": k.porcentaje_cumplimiento,
        "semaforo": k.semaforo,
        "mediciones_count": len(k.mediciones),
        "perspectiva": k.objetivo_rel.perspectiva if k.objetivo_rel else None,
        "objetivo_nombre": k.objetivo_rel.nombre if k.objetivo_rel else None
    }

@router.get("/{id}/historial")
def get_kpi_historial(id: int, db: Session = Depends(get_db)):
    k = db.query(IndicadorKpi).filter(IndicadorKpi.id == id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Indicador KPI no encontrado.")

    mediciones = (
        db.query(MedicionKpi)
        .filter(MedicionKpi.kpi_id == id)
        .order_by(MedicionKpi.fecha.asc())
        .all()
    )

    puntos = []
    for m in mediciones:
        puntos.append({
            "id": m.id,
            "periodo": m.periodo,
            "fecha": m.fecha,
            "valor_obtenido": m.valor_obtenido,
            "observaciones": m.observaciones,
            "responsable": m.responsable,
            "origen": m.origen,
            "meta": k.meta,
            "unidad": k.unidad
        })

    return {
        "kpi_id": k.id,
        "codigo": k.codigo,
        "nombre": k.nombre,
        "unidad": k.unidad,
        "meta": k.meta,
        "linea_base": k.linea_base,
        "sentido": k.sentido,
        "rango_min": k.rango_min,
        "rango_max": k.rango_max,
        "umbral_verde": k.umbral_verde,
        "umbral_amarillo": k.umbral_amarillo,
        "modulo_odoo": k.modulo_odoo,
        "modelo_odoo": k.modelo_odoo,
        "mediciones": puntos
    }

@router.post("", response_model=KpiResponse, status_code=status.HTTP_201_CREATED)
def create_kpi(data: KpiCreate, db: Session = Depends(get_db)):
    existente = db.query(IndicadorKpi).filter(IndicadorKpi.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"El código {data.codigo} ya está en uso.")

    if data.umbral_verde < data.umbral_amarillo:
        raise HTTPException(status_code=400, detail="El umbral verde debe ser mayor o igual al umbral amarillo.")

    kpi = IndicadorKpi(**data.model_dump())
    db.add(kpi)
    db.commit()
    db.refresh(kpi)

    recalcular_kpi(db, kpi)
    if kpi.objetivo_rel:
        recalcular_objetivo(db, kpi.objetivo_rel)
    recalcular_todo_el_bsc(db)

    return get_kpi_by_id(kpi.id, db)

@router.put("/{id}", response_model=KpiResponse)
def update_kpi(id: int, data: KpiUpdate, db: Session = Depends(get_db)):
    kpi = db.query(IndicadorKpi).filter(IndicadorKpi.id == id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="Indicador KPI no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(kpi, field, value)

    db.add(kpi)
    db.commit()
    db.refresh(kpi)

    recalcular_kpi(db, kpi)
    if kpi.objetivo_rel:
        recalcular_objetivo(db, kpi.objetivo_rel)
    recalcular_todo_el_bsc(db)

    return get_kpi_by_id(kpi.id, db)

@router.delete("/{id}")
def delete_kpi(id: int, db: Session = Depends(get_db)):
    kpi = db.query(IndicadorKpi).filter(IndicadorKpi.id == id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="Indicador KPI no encontrado.")

    obj_id = kpi.objetivo_id
    db.delete(kpi)
    db.commit()

    obj = db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.id == obj_id).first()
    if obj:
        recalcular_objetivo(db, obj)
    recalcular_todo_el_bsc(db)

    return {"mensaje": f"KPI {kpi.codigo} eliminado exitosamente."}
