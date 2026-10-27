from typing import Optional, List
from pydantic import BaseModel, Field

# --- USUARIO ---
class UsuarioBase(BaseModel):
    username: str
    nombre: str
    rol: str = "RESPONSABLE" # ADMIN, GERENTE, RESPONSABLE
    area: Optional[str] = None
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioResponse

# --- PERIODO ---
class PeriodoBase(BaseModel):
    codigo: str
    nombre: str
    activo: bool = False
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None

class PeriodoCreate(PeriodoBase):
    pass

class PeriodoResponse(PeriodoBase):
    id: int
    class Config:
        from_attributes = True

# --- MODULO ODOO AREA ---
class ModuloOdooBase(BaseModel):
    codigo: str
    nombre_modulo_odoo: str
    modelo_tecnico: str
    responsable: Optional[str] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = "fa-cogs"

class ModuloOdooCreate(ModuloOdooBase):
    pass

class ModuloOdooResponse(ModuloOdooBase):
    id: int
    class Config:
        from_attributes = True

# --- MEDICION KPI ---
class MedicionBase(BaseModel):
    kpi_id: int
    periodo: str
    fecha: str
    valor_obtenido: float
    observaciones: Optional[str] = None
    responsable: Optional[str] = None
    origen: Optional[str] = "MANUAL"

class MedicionCreate(MedicionBase):
    pass

class MedicionResponse(MedicionBase):
    id: int
    class Config:
        from_attributes = True

# --- INDICADOR KPI ---
class KpiBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    formula: Optional[str] = None
    unidad: str = "%"
    objetivo_id: int
    modulo_odoo: str
    modelo_odoo: str
    responsable: Optional[str] = None
    frecuencia: str = "Mensual"
    linea_base: float = 0.0
    meta: float
    sentido: str = "MAYOR_MEJOR" # MAYOR_MEJOR, MENOR_MEJOR, RANGO
    rango_min: Optional[float] = None
    rango_max: Optional[float] = None
    umbral_verde: float = 90.0
    umbral_amarillo: float = 75.0

class KpiCreate(KpiBase):
    pass

class KpiUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    formula: Optional[str] = None
    unidad: Optional[str] = None
    objetivo_id: Optional[int] = None
    modulo_odoo: Optional[str] = None
    modelo_odoo: Optional[str] = None
    responsable: Optional[str] = None
    frecuencia: Optional[str] = None
    linea_base: Optional[float] = None
    meta: Optional[float] = None
    sentido: Optional[str] = None
    rango_min: Optional[float] = None
    rango_max: Optional[float] = None
    umbral_verde: Optional[float] = None
    umbral_amarillo: Optional[float] = None

class KpiResponse(KpiBase):
    id: int
    valor_actual: Optional[float] = None
    porcentaje_cumplimiento: Optional[float] = None
    semaforo: str = "SIN_DATOS"
    mediciones_count: Optional[int] = 0
    perspectiva: Optional[str] = None
    objetivo_nombre: Optional[str] = None
    class Config:
        from_attributes = True

# --- INICIATIVA ESTRATEGICA ---
class IniciativaBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    objetivo_id: int
    kpi_id: Optional[int] = None
    modulo_odoo: Optional[str] = None
    responsable: Optional[str] = None
    presupuesto: float = 0.0
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    porcentaje_avance: float = 0.0
    estado: str = "EN_EJECUCION" # EN_EJECUCION, RETRASADA, FINALIZADA

class IniciativaCreate(IniciativaBase):
    pass

class IniciativaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    objetivo_id: Optional[int] = None
    kpi_id: Optional[int] = None
    modulo_odoo: Optional[str] = None
    responsable: Optional[str] = None
    presupuesto: Optional[float] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    porcentaje_avance: Optional[float] = None
    estado: Optional[str] = None

class IniciativaResponse(IniciativaBase):
    id: int
    objetivo_nombre: Optional[str] = None
    kpi_nombre: Optional[str] = None
    class Config:
        from_attributes = True

# --- OBJETIVO ESTRATEGICO ---
class ObjetivoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    perspectiva: str # FINANCIERA, CLIENTE, PROCESOS_INTERNOS, APRENDIZAJE
    modulo_odoo_id: Optional[int] = None
    responsable: Optional[str] = None
    prioridad: str = "Media"
    ponderacion: float = 25.0
    estado: str = "Activo"
    objetivo_padre_id: Optional[int] = None

class ObjetivoCreate(ObjetivoBase):
    pass

class ObjetivoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    perspectiva: Optional[str] = None
    modulo_odoo_id: Optional[int] = None
    responsable: Optional[str] = None
    prioridad: Optional[str] = None
    ponderacion: Optional[float] = None
    estado: Optional[str] = None
    objetivo_padre_id: Optional[int] = None

class ObjetivoResponse(ObjetivoBase):
    id: int
    avance_calculado: float = 0.0
    modulo_nombre: Optional[str] = None
    modulo_codigo: Optional[str] = None
    modulo_modelo: Optional[str] = None
    kpis_count: Optional[int] = 0
    iniciativas_count: Optional[int] = 0
    semaforo: Optional[str] = "SIN_DATOS"
    class Config:
        from_attributes = True

class ObjetivoDetailResponse(ObjetivoResponse):
    kpis: List[KpiResponse] = []
    iniciativas: List[IniciativaResponse] = []
    objetivo_padre_codigo: Optional[str] = None
    objetivo_padre_nombre: Optional[str] = None

# --- DASHBOARD & REPORTES ---
class DashboardMetricsResponse(BaseModel):
    total_objetivos: int
    total_kpis: int
    total_iniciativas: int
    cumplimiento_global: float
    total_cumplidos: int
    total_alerta: int
    total_criticos: int
    total_sin_datos: int
    periodo_actual: str
    perspectivas: dict
    desempeno_modulos: dict
    indicadores_atencion: List[dict]
    historico_tendencia: List[dict]

class SyncResponse(BaseModel):
    exito: bool
    mensaje: str
    origen: str
    registros_actualizados: int
    detalles: List[dict] = []
