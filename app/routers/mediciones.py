from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MedicionKpi, IndicadorKpi
from app.schemas import MedicionCreate, MedicionResponse
from app.services.bsc_engine import recalcular_kpi, recalcular_objetivo, recalcular_todo_el_bsc

router = APIRouter(prefix="/mediciones", tags=["Registro de Resultados (Mediciones)"])

@router.get("", response_model=List[MedicionResponse])
def get_mediciones(
    kpi_id: Optional[int] = Query(None),
    periodo: Optional[str] = Query(None),
    origen: Optional[str] = Query(None),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    query = db.query(MedicionKpi)
    if kpi_id:
        query = query.filter(MedicionKpi.kpi_id == kpi_id)
    if periodo and periodo != "TODOS":
        query = query.filter(MedicionKpi.periodo == periodo)
    if origen and origen != "TODOS":
        query = query.filter(MedicionKpi.origen == origen)

    return query.order_by(MedicionKpi.fecha.desc()).limit(limit).all()

@router.post("", response_model=MedicionResponse, status_code=status.HTTP_201_CREATED)
def create_medicion(data: MedicionCreate, db: Session = Depends(get_db)):
    kpi = db.query(IndicadorKpi).filter(IndicadorKpi.id == data.kpi_id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI no encontrado.")

    medicion = MedicionKpi(**data.model_dump())
    db.add(medicion)
    db.commit()
    db.refresh(medicion)

    # Regla 6: Recalcular automáticamente KPI, Objetivo y BSC
    recalcular_kpi(db, kpi, medicion.periodo)
    if kpi.objetivo_rel:
        recalcular_objetivo(db, kpi.objetivo_rel)
    recalcular_todo_el_bsc(db, medicion.periodo)

    return medicion

@router.put("/{id}", response_model=MedicionResponse)
def update_medicion(id: int, data: MedicionCreate, db: Session = Depends(get_db)):
    medicion = db.query(MedicionKpi).filter(MedicionKpi.id == id).first()
    if not medicion:
        raise HTTPException(status_code=404, detail="Medición no encontrada.")

    for field, value in data.model_dump().items():
        setattr(medicion, field, value)

    db.add(medicion)
    db.commit()
    db.refresh(medicion)

    # Regla 6: Recalcular automáticamente
    kpi = medicion.kpi_rel
    if kpi:
        recalcular_kpi(db, kpi, medicion.periodo)
        if kpi.objetivo_rel:
            recalcular_objetivo(db, kpi.objetivo_rel)
        recalcular_todo_el_bsc(db, medicion.periodo)

    return medicion

@router.delete("/{id}")
def delete_medicion(id: int, db: Session = Depends(get_db)):
    medicion = db.query(MedicionKpi).filter(MedicionKpi.id == id).first()
    if not medicion:
        raise HTTPException(status_code=404, detail="Medición no encontrada.")

    kpi = medicion.kpi_rel
    periodo = medicion.periodo
    db.delete(medicion)
    db.commit()

    if kpi:
        recalcular_kpi(db, kpi, periodo)
        if kpi.objetivo_rel:
            recalcular_objetivo(db, kpi.objetivo_rel)
        recalcular_todo_el_bsc(db, periodo)

    return {"mensaje": "Medición eliminada exitosamente y scorecard actualizado."}
