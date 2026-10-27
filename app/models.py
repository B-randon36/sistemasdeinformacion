from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(String(20), default="RESPONSABLE") # ADMIN, GERENTE, RESPONSABLE
    area = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Periodo(Base):
    __tablename__ = "periodos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False) # ej. '2026-10'
    nombre = Column(String(100), nullable=False) # ej. 'Octubre 2026'
    activo = Column(Boolean, default=False)
    fecha_inicio = Column(String(20), nullable=True)
    fecha_fin = Column(String(20), nullable=True)

class ModuloOdooArea(Base):
    __tablename__ = "modulos_odoo_areas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, index=True, nullable=False) # MOD-ACCOUNT, MOD-POS, MOD-SALE, MOD-CRM, MOD-MRP, MOD-STOCK, MOD-PURCHASE, MOD-HR
    nombre_modulo_odoo = Column(String(100), nullable=False)
    modelo_tecnico = Column(String(100), nullable=False) # sale.order, mrp.production, etc.
    responsable = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    icono = Column(String(50), default="fa-cogs")

    objetivos = relationship("ObjetivoEstrategico", back_populates="modulo_rel")

class ObjetivoEstrategico(Base):
    __tablename__ = "objetivos_estrategicos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False) # ej. OBJ-FIN-01
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    perspectiva = Column(String(50), nullable=False) # FINANCIERA, CLIENTE, PROCESOS_INTERNOS, APRENDIZAJE
    modulo_odoo_id = Column(Integer, ForeignKey("modulos_odoo_areas.id"), nullable=True)
    responsable = Column(String(100), nullable=True)
    prioridad = Column(String(20), default="Media") # Alta, Media, Baja
    ponderacion = Column(Float, default=25.0) # Porcentaje de ponderación en la perspectiva
    estado = Column(String(50), default="Activo") # Activo, En Revisión, Completado
    objetivo_padre_id = Column(Integer, ForeignKey("objetivos_estrategicos.id"), nullable=True)
    avance_calculado = Column(Float, default=0.0)

    modulo_rel = relationship("ModuloOdooArea", back_populates="objetivos")
    kpis = relationship("IndicadorKpi", back_populates="objetivo_rel", cascade="all, delete-orphan")
    iniciativas = relationship("IniciativaEstrategica", back_populates="objetivo_rel", cascade="all, delete-orphan")
    objetivo_padre = relationship("ObjetivoEstrategico", remote_side=[id], backref="hijos")

class IndicadorKpi(Base):
    __tablename__ = "indicadores_kpi"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False) # ej. FIN-01, CLI-01
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    formula = Column(String(255), nullable=True)
    unidad = Column(String(30), default="%") # %, S/, Kg, Unidades, Horas
    objetivo_id = Column(Integer, ForeignKey("objetivos_estrategicos.id"), nullable=False)
    modulo_odoo = Column(String(100), nullable=False) # Facturación, Ventas, etc.
    modelo_odoo = Column(String(100), nullable=False) # sale.order, crm.lead, mrp.production, etc.
    responsable = Column(String(100), nullable=True)
    frecuencia = Column(String(50), default="Mensual") # Mensual, Trimestral
    linea_base = Column(Float, default=0.0)
    meta = Column(Float, nullable=False)
    valor_actual = Column(Float, nullable=True)
    sentido = Column(String(20), default="MAYOR_MEJOR") # MAYOR_MEJOR, MENOR_MEJOR, RANGO
    rango_min = Column(Float, nullable=True)
    rango_max = Column(Float, nullable=True)
    umbral_verde = Column(Float, default=90.0) # >= 90% es CUMPLIDO
    umbral_amarillo = Column(Float, default=75.0) # >= 75% es EN_ALERTA, < 75% es CRITICO
    porcentaje_cumplimiento = Column(Float, nullable=True)
    semaforo = Column(String(20), default="SIN_DATOS") # CUMPLIDO, EN_ALERTA, CRITICO, SIN_DATOS

    objetivo_rel = relationship("ObjetivoEstrategico", back_populates="kpis")
    mediciones = relationship("MedicionKpi", back_populates="kpi_rel", cascade="all, delete-orphan", order_by="MedicionKpi.fecha.desc()")
    iniciativas = relationship("IniciativaEstrategica", back_populates="kpi_rel")

class MedicionKpi(Base):
    __tablename__ = "mediciones_kpi"

    id = Column(Integer, primary_key=True, index=True)
    kpi_id = Column(Integer, ForeignKey("indicadores_kpi.id"), nullable=False)
    periodo = Column(String(20), nullable=False) # ej. 2026-10
    fecha = Column(String(20), nullable=False) # ej. 2026-10-25
    valor_obtenido = Column(Float, nullable=False)
    observaciones = Column(Text, nullable=True)
    responsable = Column(String(100), nullable=True)
    origen = Column(String(50), default="MANUAL") # MANUAL, ODOO_17_SYNC
    created_at = Column(DateTime, default=datetime.utcnow)

    kpi_rel = relationship("IndicadorKpi", back_populates="mediciones")

class IniciativaEstrategica(Base):
    __tablename__ = "iniciativas_estrategicas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False) # ej. INI-01
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    objetivo_id = Column(Integer, ForeignKey("objetivos_estrategicos.id"), nullable=False)
    kpi_id = Column(Integer, ForeignKey("indicadores_kpi.id"), nullable=True)
    modulo_odoo = Column(String(100), nullable=True)
    responsable = Column(String(100), nullable=True)
    presupuesto = Column(Float, default=0.0) # En S/ Soles
    fecha_inicio = Column(String(20), nullable=True)
    fecha_fin = Column(String(20), nullable=True)
    porcentaje_avance = Column(Float, default=0.0)
    estado = Column(String(30), default="EN_EJECUCION") # EN_EJECUCION, RETRASADA, FINALIZADA

    objetivo_rel = relationship("ObjetivoEstrategico", back_populates="iniciativas")
    kpi_rel = relationship("IndicadorKpi", back_populates="iniciativas")

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    origen = Column(String(50), default="ODOO_17_XMLRPC")
    modulo = Column(String(50), default="TODOS")
    estado = Column(String(20), default="EXITOSO") # EXITOSO, ERROR, ADVERTENCIA
    registros_procesados = Column(Integer, default=0)
    mensaje_detalle = Column(Text, nullable=True)
