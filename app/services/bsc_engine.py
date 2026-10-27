"""
Motor de Lógica de Negocio Balanced Scorecard (BSC) - AGRO PERUVIAN FOODS S.A.C.
Implementación de las 14 reglas de negocio para cálculo de cumplimiento, semáforos,
recalculación de objetivos y consolidación estratégica.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import IndicadorKpi, MedicionKpi, ObjetivoEstrategico, Periodo

def calcular_cumplimiento_kpi(
    sentido: str,
    valor_actual: Optional[float],
    meta: float,
    rango_min: Optional[float] = None,
    rango_max: Optional[float] = None,
    umbral_verde: float = 90.0,
    umbral_amarillo: float = 75.0,
    has_mediciones: bool = True
) -> Dict[str, Any]:
    """
    Reglas 1 a 5:
    1. Si no hay mediciones, semáforo es SIN_DATOS (gris) y nunca CUMPLIDO.
    2. MAYOR_MEJOR: (valor_actual / meta) * 100 (con meta > 0).
    3. MENOR_MEJOR: si valor_actual <= meta -> >= 100%; si valor_actual > meta -> (meta / valor_actual) * 100.
    4. RANGO: 100% si rango_min <= valor_actual <= rango_max; penalización proporcional fuera del rango.
    5. Semáforo: CUMPLIDO (>= verde), EN_ALERTA (>= amarillo y < verde), CRITICO (< amarillo), SIN_DATOS.
    """
    # Regla 1: Sin datos
    if not has_mediciones or valor_actual is None:
        return {
            "porcentaje_cumplimiento": None,
            "semaforo": "SIN_DATOS",
            "descripcion_estado": "Sin mediciones registradas en el período"
        }

    cumplimiento = 0.0

    # Regla 2: MAYOR_MEJOR
    if sentido == "MAYOR_MEJOR":
        if meta <= 0:
            cumplimiento = 100.0 if valor_actual >= meta else 0.0
        else:
            cumplimiento = (valor_actual / meta) * 100.0

    # Regla 3: MENOR_MEJOR (ej. Merma en Extracción de Aceite de Coco)
    elif sentido == "MENOR_MEJOR":
        if meta <= 0:
            cumplimiento = 100.0 if valor_actual <= 0 else 0.0
        else:
            if valor_actual <= meta:
                # Si la merma es menor o igual a la meta, se ha superado la expectativa
                if valor_actual <= 0:
                    cumplimiento = 100.0 + 20.0 # Premio por merma 0
                else:
                    diferencia = meta - valor_actual
                    cumplimiento = 100.0 + (diferencia / meta) * 50.0 # Incremento proporcional
            else:
                # Merma mayor a la meta: penaliza (ej. 4.0 / 6.2 * 100 = 64.52%)
                cumplimiento = (meta / valor_actual) * 100.0

    # Regla 4: RANGO (ej. Humedad de Almacenamiento Grano de Cacao 6.5% - 8.0%)
    elif sentido == "RANGO":
        r_min = rango_min if rango_min is not None else meta * 0.9
        r_max = rango_max if rango_max is not None else meta * 1.1

        if r_min <= valor_actual <= r_max:
            cumplimiento = 100.0
        elif valor_actual < r_min:
            cumplimiento = (valor_actual / r_min) * 100.0 if r_min > 0 else 0.0
        else: # valor_actual > r_max
            cumplimiento = (r_max / valor_actual) * 100.0 if valor_actual > 0 else 0.0

    else:
        # Por defecto tratar como MAYOR_MEJOR
        cumplimiento = (valor_actual / meta) * 100.0 if meta > 0 else 100.0

    # Limitar decimales a 2
    cumplimiento = round(cumplimiento, 2)

    # Regla 5: Asignación de Semáforo
    if cumplimiento >= umbral_verde:
        semaforo = "CUMPLIDO"
        desc = "Meta alcanzada o superada (Verde)"
    elif cumplimiento >= umbral_amarillo:
        semaforo = "EN_ALERTA"
        desc = "En riesgo moderado / Precaución (Amarillo)"
    else:
        semaforo = "CRITICO"
        desc = "Desviación crítica de la meta (Rojo)"

    return {
        "porcentaje_cumplimiento": cumplimiento,
        "semaforo": semaforo,
        "descripcion_estado": desc
    }

def recalcular_kpi(db: Session, kpi: IndicadorKpi, periodo_codigo: Optional[str] = None) -> IndicadorKpi:
    """
    Recalcula el valor_actual, cumplimiento y semáforo de un KPI basado en sus mediciones.
    Si se pasa un período, prioriza la medición de ese período; de lo contrario toma la más reciente.
    """
    mediciones_query = db.query(MedicionKpi).filter(MedicionKpi.kpi_id == kpi.id)

    if periodo_codigo:
        medicion_periodo = mediciones_query.filter(MedicionKpi.periodo == periodo_codigo).first()
        if medicion_periodo:
            medicion_target = medicion_periodo
        else:
            medicion_target = mediciones_query.order_by(MedicionKpi.fecha.desc()).first()
    else:
        medicion_target = mediciones_query.order_by(MedicionKpi.fecha.desc()).first()

    if not medicion_target:
        kpi.valor_actual = None
        kpi.porcentaje_cumplimiento = None
        kpi.semaforo = "SIN_DATOS"
    else:
        kpi.valor_actual = medicion_target.valor_obtenido
        calc = calcular_cumplimiento_kpi(
            sentido=kpi.sentido,
            valor_actual=kpi.valor_actual,
            meta=kpi.meta,
            rango_min=kpi.rango_min,
            rango_max=kpi.rango_max,
            umbral_verde=kpi.umbral_verde,
            umbral_amarillo=kpi.umbral_amarillo,
            has_mediciones=True
        )
        kpi.porcentaje_cumplimiento = calc["porcentaje_cumplimiento"]
        kpi.semaforo = calc["semaforo"]

    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi

def recalcular_objetivo(db: Session, objetivo: ObjetivoEstrategico) -> ObjetivoEstrategico:
    """
    Regla 6 (parte A): Recalcula el avance del Objetivo Estratégico
    haciendo promedio del cumplimiento de sus KPIs activos con datos.
    """
    kpis = db.query(IndicadorKpi).filter(IndicadorKpi.objetivo_id == objetivo.id).all()
    
    kpis_con_datos = [k for k in kpis if k.porcentaje_cumplimiento is not None]
    if not kpis_con_datos:
        objetivo.avance_calculado = 0.0
    else:
        promedio = sum(k.porcentaje_cumplimiento for k in kpis_con_datos) / len(kpis_con_datos)
        objetivo.avance_calculado = round(promedio, 2)

    db.add(objetivo)
    db.commit()
    db.refresh(objetivo)
    return objetivo

def recalcular_todo_el_bsc(db: Session, periodo_codigo: Optional[str] = None) -> Dict[str, Any]:
    """
    Regla 6 (parte B): Recalcula todos los KPIs, Objetivos, Perspectivas y
    el Cumplimiento Global ponderado de AGRO PERUVIAN FOODS S.A.C.
    """
    # 1. Recalcular todos los KPIs
    kpis = db.query(IndicadorKpi).all()
    for k in kpis:
        recalcular_kpi(db, k, periodo_codigo)

    # 2. Recalcular todos los Objetivos
    objetivos = db.query(ObjetivoEstrategico).all()
    for obj in objetivos:
        recalcular_objetivo(db, obj)

    # 3. Consolidar por Perspectiva
    perspectivas = {
        "FINANCIERA": {"nombre": "Perspectiva Financiera", "avance": 0.0, "objetivos_count": 0, "kpis_count": 0, "ponderacion_total": 0.0, "suma_ponderada": 0.0},
        "CLIENTE": {"nombre": "Perspectiva del Cliente", "avance": 0.0, "objetivos_count": 0, "kpis_count": 0, "ponderacion_total": 0.0, "suma_ponderada": 0.0},
        "PROCESOS_INTERNOS": {"nombre": "Perspectiva de Procesos Internos", "avance": 0.0, "objetivos_count": 0, "kpis_count": 0, "ponderacion_total": 0.0, "suma_ponderada": 0.0},
        "APRENDIZAJE": {"nombre": "Perspectiva de Aprendizaje y Crecimiento", "avance": 0.0, "objetivos_count": 0, "kpis_count": 0, "ponderacion_total": 0.0, "suma_ponderada": 0.0}
    }

    total_suma_global = 0.0
    total_ponderacion_global = 0.0

    for obj in objetivos:
        p_key = obj.perspectiva
        if p_key in perspectivas:
            perspectivas[p_key]["objetivos_count"] += 1
            perspectivas[p_key]["kpis_count"] += len(obj.kpis)
            ponderacion = obj.ponderacion if obj.ponderacion > 0 else 25.0
            perspectivas[p_key]["ponderacion_total"] += ponderacion
            perspectivas[p_key]["suma_ponderada"] += (obj.avance_calculado * ponderacion)
            
            total_ponderacion_global += ponderacion
            total_suma_global += (obj.avance_calculado * ponderacion)

    for p_key, p_data in perspectivas.items():
        if p_data["ponderacion_total"] > 0:
            p_data["avance"] = round(p_data["suma_ponderada"] / p_data["ponderacion_total"], 2)
        else:
            p_data["avance"] = 0.0

    cumplimiento_global = round(total_suma_global / total_ponderacion_global, 2) if total_ponderacion_global > 0 else 0.0

    # Conteo de semáforos
    kpis_actualizados = db.query(IndicadorKpi).all()
    cumplidos = sum(1 for k in kpis_actualizados if k.semaforo == "CUMPLIDO")
    alerta = sum(1 for k in kpis_actualizados if k.semaforo == "EN_ALERTA")
    criticos = sum(1 for k in kpis_actualizados if k.semaforo == "CRITICO")
    sin_datos = sum(1 for k in kpis_actualizados if k.semaforo == "SIN_DATOS")

    return {
        "cumplimiento_global": cumplimiento_global,
        "perspectivas": perspectivas,
        "semaforos": {
            "cumplidos": cumplidos,
            "alerta": alerta,
            "criticos": criticos,
            "sin_datos": sin_datos,
            "total": len(kpis_actualizados)
        }
    }

def obtener_indicadores_requieren_atencion(db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene los KPIs con semáforo CRITICO o EN_ALERTA ordenados por severidad.
    """
    kpis = db.query(IndicadorKpi).filter(IndicadorKpi.semaforo.in_(["CRITICO", "EN_ALERTA"])).all()
    # Ordenar primero CRITICO, luego menor cumplimiento
    kpis_ordenados = sorted(
        kpis,
        key=lambda x: (0 if x.semaforo == "CRITICO" else 1, x.porcentaje_cumplimiento or 0.0)
    )

    resultado = []
    for k in kpis_ordenados:
        resultado.append({
            "id": k.id,
            "codigo": k.codigo,
            "nombre": k.nombre,
            "modulo_odoo": k.modulo_odoo,
            "modelo_odoo": k.modelo_odoo,
            "meta": k.meta,
            "valor_actual": k.valor_actual,
            "unidad": k.unidad,
            "porcentaje_cumplimiento": k.porcentaje_cumplimiento,
            "semaforo": k.semaforo,
            "responsable": k.responsable,
            "perspectiva": k.objetivo_rel.perspectiva if k.objetivo_rel else None,
            "objetivo_nombre": k.objetivo_rel.nombre if k.objetivo_rel else None,
            "sentido": k.sentido
        })
    return resultado

def obtener_tendencia_historica(db: Session) -> List[Dict[str, Any]]:
    """
    Calcula el cumplimiento promedio histórico por período para los gráficos de tendencia.
    """
    periodos = db.query(Periodo).order_by(Periodo.codigo.asc()).all()
    tendencia = []

    for p in periodos:
        # Obtener mediciones para este período
        mediciones = db.query(MedicionKpi).filter(MedicionKpi.periodo == p.codigo).all()
        if not mediciones:
            continue

        cumplimientos = []
        for m in mediciones:
            kpi = m.kpi_rel
            if not kpi:
                continue
            calc = calcular_cumplimiento_kpi(
                sentido=kpi.sentido,
                valor_actual=m.valor_obtenido,
                meta=kpi.meta,
                rango_min=kpi.rango_min,
                rango_max=kpi.rango_max,
                umbral_verde=kpi.umbral_verde,
                umbral_amarillo=kpi.umbral_amarillo,
                has_mediciones=True
            )
            if calc["porcentaje_cumplimiento"] is not None:
                cumplimientos.append(calc["porcentaje_cumplimiento"])

        promedio = round(sum(cumplimientos) / len(cumplimientos), 2) if cumplimientos else 0.0
        tendencia.append({
            "periodo": p.codigo,
            "nombre_periodo": p.nombre,
            "cumplimiento_promedio": promedio,
            "total_mediciones": len(mediciones)
        })

    return tendencia

def obtener_desempeno_por_modulo_odoo(db: Session) -> Dict[str, Any]:
    """
    Calcula el cumplimiento promedio clasificado por cada Módulo de Odoo 17.
    """
    from app.models import ModuloOdooArea
    modulos = db.query(ModuloOdooArea).all()
    desempeno = {}

    for mod in modulos:
        kpis = db.query(IndicadorKpi).filter(IndicadorKpi.modulo_odoo.ilike(f"%{mod.nombre_modulo_odoo}%")).all()
        # Fallback por código técnico
        if not kpis:
            kpis = db.query(IndicadorKpi).filter(IndicadorKpi.modelo_odoo == mod.modelo_tecnico).all()

        cumplimientos = [k.porcentaje_cumplimiento for k in kpis if k.porcentaje_cumplimiento is not None]
        promedio = round(sum(cumplimientos) / len(cumplimientos), 2) if cumplimientos else 0.0

        desempeno[mod.codigo] = {
            "nombre": mod.nombre_modulo_odoo,
            "modelo_tecnico": mod.modelo_tecnico,
            "kpis_count": len(kpis),
            "cumplimiento_promedio": promedio,
            "icono": mod.icono,
            "responsable": mod.responsable
        }

    return desempeno
