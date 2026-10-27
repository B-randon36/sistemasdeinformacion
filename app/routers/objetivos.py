from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ObjetivoEstrategico, IndicadorKpi, IniciativaEstrategica, ModuloOdooArea
from app.schemas import ObjetivoCreate, ObjetivoUpdate, ObjetivoResponse, ObjetivoDetailResponse
from app.services.bsc_engine import recalcular_objetivo, recalcular_todo_el_bsc

router = APIRouter(prefix="/objetivos", tags=["Objetivos Estratégicos"])

@router.get("", response_model=List[ObjetivoResponse])
def get_objetivos(
    perspectiva: Optional[str] = Query(None),
    modulo_odoo_id: Optional[int] = Query(None),
    prioridad: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ObjetivoEstrategico)
    if perspectiva and perspectiva != "TODAS":
        query = query.filter(ObjetivoEstrategico.perspectiva == perspectiva)
    if modulo_odoo_id:
        query = query.filter(ObjetivoEstrategico.modulo_odoo_id == modulo_odoo_id)
    if prioridad and prioridad != "TODAS":
        query = query.filter(ObjetivoEstrategico.prioridad == prioridad)
    if search:
        query = query.filter(
            (ObjetivoEstrategico.nombre.ilike(f"%{search}%")) |
            (ObjetivoEstrategico.codigo.ilike(f"%{search}%")) |
            (ObjetivoEstrategico.responsable.ilike(f"%{search}%"))
        )

    objetivos = query.all()
    resultado = []
    for obj in objetivos:
        # Calcular semaforo del objetivo
        kpis_obj = obj.kpis
        semaforo_obj = "SIN_DATOS"
        if any(k.semaforo == "CRITICO" for k in kpis_obj):
            semaforo_obj = "CRITICO"
        elif any(k.semaforo == "EN_ALERTA" for k in kpis_obj):
            semaforo_obj = "EN_ALERTA"
        elif any(k.semaforo == "CUMPLIDO" for k in kpis_obj):
            semaforo_obj = "CUMPLIDO"

        item = ObjetivoResponse(
            id=obj.id,
            codigo=obj.codigo,
            nombre=obj.nombre,
            descripcion=obj.descripcion,
            perspectiva=obj.perspectiva,
            modulo_odoo_id=obj.modulo_odoo_id,
            responsable=obj.responsable,
            prioridad=obj.prioridad,
            ponderacion=obj.ponderacion,
            estado=obj.estado,
            objetivo_padre_id=obj.objetivo_padre_id,
            avance_calculado=obj.avance_calculado,
            modulo_nombre=obj.modulo_rel.nombre_modulo_odoo if obj.modulo_rel else None,
            modulo_codigo=obj.modulo_rel.codigo if obj.modulo_rel else None,
            modulo_modelo=obj.modulo_rel.modelo_tecnico if obj.modulo_rel else None,
            kpis_count=len(kpis_obj),
            iniciativas_count=len(obj.iniciativas),
            semaforo=semaforo_obj
        )
        resultado.append(item)

    return resultado

@router.get("/tree/map")
def get_mapa_estrategico(db: Session = Depends(get_db)):
    """
    Retorna la estructura del Mapa Estratégico agrupada por las 4 perspectivas
    con sus relaciones Causa-Efecto (padre e hijos) y detalles de Odoo 17.
    """
    objetivos = db.query(ObjetivoEstrategico).all()
    
    perspectivas = {
        "FINANCIERA": {"id": "FINANCIERA", "nombre": "Perspectiva Financiera", "color": "blue", "objetivos": []},
        "CLIENTE": {"id": "CLIENTE", "nombre": "Perspectiva del Cliente", "color": "emerald", "objetivos": []},
        "PROCESOS_INTERNOS": {"id": "PROCESOS_INTERNOS", "nombre": "Perspectiva de Procesos Internos", "color": "amber", "objetivos": []},
        "APRENDIZAJE": {"id": "APRENDIZAJE", "nombre": "Perspectiva de Aprendizaje y Crecimiento", "color": "indigo", "objetivos": []}
    }

    relaciones = []

    for obj in objetivos:
        kpis_obj = obj.kpis
        semaforo_obj = "SIN_DATOS"
        if any(k.semaforo == "CRITICO" for k in kpis_obj):
            semaforo_obj = "CRITICO"
        elif any(k.semaforo == "EN_ALERTA" for k in kpis_obj):
            semaforo_obj = "EN_ALERTA"
        elif any(k.semaforo == "CUMPLIDO" for k in kpis_obj):
            semaforo_obj = "CUMPLIDO"

        obj_info = {
            "id": obj.id,
            "codigo": obj.codigo,
            "nombre": obj.nombre,
            "perspectiva": obj.perspectiva,
            "avance_calculado": obj.avance_calculado,
            "ponderacion": obj.ponderacion,
            "prioridad": obj.prioridad,
            "responsable": obj.responsable,
            "modulo_odoo_nombre": obj.modulo_rel.nombre_modulo_odoo if obj.modulo_rel else "General",
            "modulo_odoo_codigo": obj.modulo_rel.codigo if obj.modulo_rel else "MOD-GEN",
            "modulo_odoo_modelo": obj.modulo_rel.modelo_tecnico if obj.modulo_rel else "",
            "modulo_odoo_icono": obj.modulo_rel.icono if obj.modulo_rel else "fa-cube",
            "kpis_count": len(kpis_obj),
            "iniciativas_count": len(obj.iniciativas),
            "semaforo": semaforo_obj,
            "objetivo_padre_id": obj.objetivo_padre_id
        }

        if obj.perspectiva in perspectivas:
            perspectivas[obj.perspectiva]["objetivos"].append(obj_info)

        if obj.objetivo_padre_id:
            relaciones.append({
                "from_id": obj.objetivo_padre_id,
                "to_id": obj.id,
                "label": "Impacta a"
            })

    return {
        "perspectivas": list(perspectivas.values()),
        "relaciones": relaciones
    }

@router.get("/{id}", response_model=ObjetivoDetailResponse)
def get_objetivo_detalle(id: int, db: Session = Depends(get_db)):
    obj = db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo estratégico no encontrado.")

    kpis_obj = obj.kpis
    semaforo_obj = "SIN_DATOS"
    if any(k.semaforo == "CRITICO" for k in kpis_obj):
        semaforo_obj = "CRITICO"
    elif any(k.semaforo == "EN_ALERTA" for k in kpis_obj):
        semaforo_obj = "EN_ALERTA"
    elif any(k.semaforo == "CUMPLIDO" for k in kpis_obj):
        semaforo_obj = "CUMPLIDO"

    kpis_list = []
    for k in kpis_obj:
        kpis_list.append({
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
            "perspectiva": obj.perspectiva,
            "objetivo_nombre": obj.nombre
        })

    iniciativas_list = []
    for ini in obj.iniciativas:
        iniciativas_list.append({
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
            "objetivo_nombre": obj.nombre,
            "kpi_nombre": ini.kpi_rel.nombre if ini.kpi_rel else None
        })

    return {
        "id": obj.id,
        "codigo": obj.codigo,
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "perspectiva": obj.perspectiva,
        "modulo_odoo_id": obj.modulo_odoo_id,
        "responsable": obj.responsable,
        "prioridad": obj.prioridad,
        "ponderacion": obj.ponderacion,
        "estado": obj.estado,
        "objetivo_padre_id": obj.objetivo_padre_id,
        "avance_calculado": obj.avance_calculado,
        "modulo_nombre": obj.modulo_rel.nombre_modulo_odoo if obj.modulo_rel else None,
        "modulo_codigo": obj.modulo_rel.codigo if obj.modulo_rel else None,
        "modulo_modelo": obj.modulo_rel.modelo_tecnico if obj.modulo_rel else None,
        "kpis_count": len(kpis_obj),
        "iniciativas_count": len(obj.iniciativas),
        "semaforo": semaforo_obj,
        "kpis": kpis_list,
        "iniciativas": iniciativas_list,
        "objetivo_padre_codigo": obj.objetivo_padre.codigo if obj.objetivo_padre else None,
        "objetivo_padre_nombre": obj.objetivo_padre.nombre if obj.objetivo_padre else None
    }

@router.post("", response_model=ObjetivoResponse, status_code=status.HTTP_201_CREATED)
def create_objetivo(data: ObjetivoCreate, db: Session = Depends(get_db)):
    existente = db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"El código {data.codigo} ya está en uso.")

    nuevo_obj = ObjetivoEstrategico(**data.model_dump())
    db.add(nuevo_obj)
    db.commit()
    db.refresh(nuevo_obj)

    recalcular_todo_el_bsc(db)
    return get_objetivo_detalle(nuevo_obj.id, db)

@router.put("/{id}", response_model=ObjetivoResponse)
def update_objetivo(id: int, data: ObjetivoUpdate, db: Session = Depends(get_db)):
    obj = db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)

    db.add(obj)
    db.commit()
    db.refresh(obj)

    recalcular_objetivo(db, obj)
    recalcular_todo_el_bsc(db)
    return get_objetivo_detalle(obj.id, db)

@router.delete("/{id}")
def delete_objetivo(id: int, db: Session = Depends(get_db)):
    obj = db.query(ObjetivoEstrategico).filter(ObjetivoEstrategico.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado.")

    db.delete(obj)
    db.commit()
    recalcular_todo_el_bsc(db)
    return {"mensaje": f"Objetivo {obj.codigo} eliminado exitosamente."}
