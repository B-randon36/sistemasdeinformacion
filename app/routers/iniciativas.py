from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IniciativaEstrategica, ObjetivoEstrategico, IndicadorKpi
from app.schemas import IniciativaCreate, IniciativaUpdate, IniciativaResponse

router = APIRouter(prefix="/iniciativas", tags=["Iniciativas Estratégicas"])

@router.get("", response_model=List[IniciativaResponse])
def get_iniciativas(
    estado: Optional[str] = Query(None),
    objetivo_id: Optional[int] = Query(None),
    modulo_odoo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(IniciativaEstrategica)
    if estado and estado != "TODOS":
        query = query.filter(IniciativaEstrategica.estado == estado)
    if objetivo_id:
        query = query.filter(IniciativaEstrategica.objetivo_id == objetivo_id)
    if modulo_odoo and modulo_odoo != "TODOS":
        query = query.filter(IniciativaEstrategica.modulo_odoo.ilike(f"%{modulo_odoo}%"))
    if search:
        query = query.filter(
            (IniciativaEstrategica.nombre.ilike(f"%{search}%")) |
            (IniciativaEstrategica.codigo.ilike(f"%{search}%")) |
            (IniciativaEstrategica.responsable.ilike(f"%{search}%"))
        )

    iniciativas = query.all()
    resultado = []
    for ini in iniciativas:
        resultado.append({
            "id": ini.id,
            "codigo": ini.codigo,
            "nombre": ini.nombre,
            "descripcion": ini.descripcion,
            "objetivo_id": ini.objetivo_id,
            "kpi_id": ini.kpi_id,
            "modulo_odoo": ini.modulo_odoo,
            "responsable": ini.responsable,
            "presupuesto": ini.presupuesto,
            "fecha_inicio": ini.fecha_inicio,
            "fecha_fin": ini.fecha_fin,
            "porcentaje_avance": ini.porcentaje_avance,
            "estado": ini.estado,
            "objetivo_nombre": ini.objetivo_rel.nombre if ini.objetivo_rel else None,
            "kpi_nombre": ini.kpi_rel.nombre if ini.kpi_rel else None
        })
    return resultado

@router.get("/resumen")
def get_iniciativas_resumen(db: Session = Depends(get_db)):
    iniciativas = db.query(IniciativaEstrategica).all()
    presupuesto_total = sum(i.presupuesto for i in iniciativas)
    promedio_avance = round(sum(i.porcentaje_avance for i in iniciativas) / len(iniciativas), 2) if iniciativas else 0.0

    en_ejecucion = sum(1 for i in iniciativas if i.estado == "EN_EJECUCION")
    retrasadas = sum(1 for i in iniciativas if i.estado == "RETRASADA")
    finalizadas = sum(1 for i in iniciativas if i.estado == "FINALIZADA")

    return {
        "total_iniciativas": len(iniciativas),
        "presupuesto_total": presupuesto_total,
        "promedio_avance": promedio_avance,
        "en_ejecucion": en_ejecucion,
        "retrasadas": retrasadas,
        "finalizadas": finalizadas
    }

@router.post("", response_model=IniciativaResponse, status_code=status.HTTP_201_CREATED)
def create_iniciativa(data: IniciativaCreate, db: Session = Depends(get_db)):
    existente = db.query(IniciativaEstrategica).filter(IniciativaEstrategica.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"El código {data.codigo} ya está en uso.")

    ini = IniciativaEstrategica(**data.model_dump())
    db.add(ini)
    db.commit()
    db.refresh(ini)

    return {
        "id": ini.id,
        "codigo": ini.codigo,
        "nombre": ini.nombre,
        "descripcion": ini.descripcion,
        "objetivo_id": ini.objetivo_id,
        "kpi_id": ini.kpi_id,
        "modulo_odoo": ini.modulo_odoo,
        "responsable": ini.responsable,
        "presupuesto": ini.presupuesto,
        "fecha_inicio": ini.fecha_inicio,
        "fecha_fin": ini.fecha_fin,
        "porcentaje_avance": ini.porcentaje_avance,
        "estado": ini.estado,
        "objetivo_nombre": ini.objetivo_rel.nombre if ini.objetivo_rel else None,
        "kpi_nombre": ini.kpi_rel.nombre if ini.kpi_rel else None
    }

@router.put("/{id}", response_model=IniciativaResponse)
def update_iniciativa(id: int, data: IniciativaUpdate, db: Session = Depends(get_db)):
    ini = db.query(IniciativaEstrategica).filter(IniciativaEstrategica.id == id).first()
    if not ini:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ini, field, value)

    db.add(ini)
    db.commit()
    db.refresh(ini)

    return {
        "id": ini.id,
        "codigo": ini.codigo,
        "nombre": ini.nombre,
        "descripcion": ini.descripcion,
        "objetivo_id": ini.objetivo_id,
        "kpi_id": ini.kpi_id,
        "modulo_odoo": ini.modulo_odoo,
        "responsable": ini.responsable,
        "presupuesto": ini.presupuesto,
        "fecha_inicio": ini.fecha_inicio,
        "fecha_fin": ini.fecha_fin,
        "porcentaje_avance": ini.porcentaje_avance,
        "estado": ini.estado,
        "objetivo_nombre": ini.objetivo_rel.nombre if ini.objetivo_rel else None,
        "kpi_nombre": ini.kpi_rel.nombre if ini.kpi_rel else None
    }

@router.delete("/{id}")
def delete_iniciativa(id: int, db: Session = Depends(get_db)):
    ini = db.query(IniciativaEstrategica).filter(IniciativaEstrategica.id == id).first()
    if not ini:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada.")

    db.delete(ini)
    db.commit()
    return {"mensaje": f"Iniciativa {ini.codigo} eliminada exitosamente."}
