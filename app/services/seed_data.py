"""
Módulo de Inicialización y Precarga de Datos - AGRO PERUVIAN FOODS S.A.C.
Carga catálogos de Odoo 17, usuarios, períodos, 16 objetivos estratégicos,
14 KPIs, mediciones históricas de 6 meses y 8 iniciativas con presupuesto en Soles.
"""

import logging
from sqlalchemy.orm import Session
from app.models import (
    Usuario, Periodo, ModuloOdooArea, ObjetivoEstrategico,
    IndicadorKpi, MedicionKpi, IniciativaEstrategica, SyncLog
)
from app.services.bsc_engine import recalcular_todo_el_bsc

logger = logging.getLogger("bsc.seed_data")

def precargar_datos_si_vacio(db: Session):
    """
    Verifica si existen datos precargados; si la base de datos está vacía,
    crea todo el ecosistema de Balanced Scorecard para AGRO PERUVIAN FOODS S.A.C.
    """
    if db.query(Usuario).first():
        logger.info("Base de datos ya contiene registros. Omitiendo seed inicial.")
        return

    logger.info("Iniciando precarga de datos estratégicos para AGRO PERUVIAN FOODS S.A.C....")

    # 1. USUARIOS DEMOSTRATIVOS
    usuarios_demo = [
        Usuario(
            username="admin",
            password="admin123",
            nombre="Ing. Jean Paul Ramos",
            rol="ADMIN",
            area="Dirección de Estrategia y TI",
            activo=True
        ),
        Usuario(
            username="gerente",
            password="gerente123",
            nombre="Dra. Gabriela Vega Solari",
            rol="GERENTE",
            area="Gerencia General",
            activo=True
        ),
        Usuario(
            username="jefe_mrp",
            password="mrp123",
            nombre="Ing. Roberto Santillán",
            rol="RESPONSABLE",
            area="Planta y Manufactura (Satipo)",
            activo=True
        )
    ]
    db.add_all(usuarios_demo)
    db.commit()

    # 2. PERIODOS DE EVALUACION (Mayo a Octubre 2026)
    periodos_demo = [
        Periodo(codigo="2026-05", nombre="Mayo 2026", activo=False, fecha_inicio="2026-05-01", fecha_fin="2026-05-31"),
        Periodo(codigo="2026-06", nombre="Junio 2026", activo=False, fecha_inicio="2026-06-01", fecha_fin="2026-06-30"),
        Periodo(codigo="2026-07", nombre="Julio 2026", activo=False, fecha_inicio="2026-07-01", fecha_fin="2026-07-31"),
        Periodo(codigo="2026-08", nombre="Agosto 2026", activo=False, fecha_inicio="2026-08-01", fecha_fin="2026-08-31"),
        Periodo(codigo="2026-09", nombre="Setiembre 2026", activo=False, fecha_inicio="2026-09-01", fecha_fin="2026-09-30"),
        Periodo(codigo="2026-10", nombre="Octubre 2026 (Período Actual)", activo=True, fecha_inicio="2026-10-01", fecha_fin="2026-10-31"),
    ]
    db.add_all(periodos_demo)
    db.commit()

    # 3. MODULOS DE ODOO 17 / AREAS
    modulos_odoo = [
        ModuloOdooArea(
            codigo="MOD-ACCOUNT",
            nombre_modulo_odoo="Facturación (account)",
            modelo_tecnico="account.move",
            responsable="Lic. Carlos Mendoza (Finanzas)",
            descripcion="Emisión de comprobantes electrónicos B2B, márgenes de utilidad y cobranzas a crédito.",
            icono="fa-file-invoice-dollar"
        ),
        ModuloOdooArea(
            codigo="MOD-POS",
            nombre_modulo_odoo="Punto de Venta (point_of_sale)",
            modelo_tecnico="pos.session",
            responsable="Renata Castillo (Ventas Directas)",
            descripcion="Ventas en tienda de fábrica Satipo, bioferias de Lima y arqueos de caja.",
            icono="fa-cash-register"
        ),
        ModuloOdooArea(
            codigo="MOD-SALE",
            nombre_modulo_odoo="Ventas (sale_management)",
            modelo_tecnico="sale.order",
            responsable="Ing. Marcos Paredes (Comercial)",
            descripcion="Órdenes de venta mayoristas confirmadas a supermercados y cadenas ecológicas.",
            icono="fa-shopping-cart"
        ),
        ModuloOdooArea(
            codigo="MOD-CRM",
            nombre_modulo_odoo="CRM (crm)",
            modelo_tecnico="crm.lead",
            responsable="Valeria Huamán (Desarrollo B2B)",
            descripcion="Seguimiento de prospectos, distribuidores regionales e iniciativas de exportación.",
            icono="fa-handshake"
        ),
        ModuloOdooArea(
            codigo="MOD-MRP",
            nombre_modulo_odoo="Manufactura BOM (mrp)",
            modelo_tecnico="mrp.production",
            responsable="Ing. Roberto Santillán (Planta Satipo)",
            descripcion="Lista de materiales BOM, prensado de coco en frío, tostado de cacao y mermas.",
            icono="fa-industry"
        ),
        ModuloOdooArea(
            codigo="MOD-STOCK",
            nombre_modulo_odoo="Inventario y Lotes (stock)",
            modelo_tecnico="stock.lot",
            responsable="Sonia Alarcón (Almacenes y Calidad)",
            descripcion="Trazabilidad por número de lote, humedad en silos de cacao y rotación FIFO.",
            icono="fa-boxes"
        ),
        ModuloOdooArea(
            codigo="MOD-PURCHASE",
            nombre_modulo_odoo="Compras (purchase)",
            modelo_tecnico="purchase.order",
            responsable="Esteban Quispe (Acopio y Cadena de Suministro)",
            descripcion="Abastecimiento de cacao criollo y coco de cooperativas de Satipo y Pichanaqui.",
            icono="fa-truck-loading"
        ),
        ModuloOdooArea(
            codigo="MOD-HR",
            nombre_modulo_odoo="Empleados y Planta (hr)",
            modelo_tecnico="hr.employee",
            responsable="Dra. Elena Vargas (Gestión del Talento)",
            descripcion="Capacitaciones en Buenas Prácticas de Manufactura (BPM), clima laboral y bienestar.",
            icono="fa-user-tie"
        )
    ]
    db.add_all(modulos_odoo)
    db.commit()

    # Mapear IDs de módulos
    mod_map = {m.codigo: m.id for m in db.query(ModuloOdooArea).all()}

    # 4. OBJETIVOS ESTRATÉGICOS (16 Objetivos en las 4 perspectivas con relaciones Causa-Efecto)
    # Primero insertamos los de base (Aprendizaje) y luego vamos encadenando hacia arriba
    # Aprendizaje
    obj_apr_01 = ObjetivoEstrategico(
        codigo="OBJ-APR-01",
        nombre="Certificar al 100% de operarios en BPM, HACCP y seguridad agroindustrial",
        descripcion="Elevar la competencia técnica en inocuidad y control de calidad en planta Satipo.",
        perspectiva="APRENDIZAJE",
        modulo_odoo_id=mod_map["MOD-HR"],
        responsable="Dra. Elena Vargas (Talento Humano)",
        prioridad="Alta",
        ponderacion=40.0,
        estado="Activo",
        objetivo_padre_id=None
    )
    obj_apr_02 = ObjetivoEstrategico(
        codigo="OBJ-APR-02",
        nombre="Fomentar un clima laboral óptimo y sentido de pertenencia en planta Satipo",
        descripcion="Disminuir la rotación operativa y afianzar la identidad corporativa y bienestar.",
        perspectiva="APRENDIZAJE",
        modulo_odoo_id=mod_map["MOD-HR"],
        responsable="Dra. Elena Vargas (Talento Humano)",
        prioridad="Media",
        ponderacion=30.0,
        estado="Activo",
        objetivo_padre_id=None
    )
    obj_apr_03 = ObjetivoEstrategico(
        codigo="OBJ-APR-03",
        nombre="Fortalecer las competencias digitales del equipo en el uso de Odoo 17 ERP",
        descripcion="Optimizar el registro ágil en los módulos mrp, stock y sale desde tablets de planta.",
        perspectiva="APRENDIZAJE",
        modulo_odoo_id=mod_map["MOD-HR"],
        responsable="Ing. Jean Paul Ramos (TI)",
        prioridad="Media",
        ponderacion=30.0,
        estado="Activo",
        objetivo_padre_id=None
    )
    db.add_all([obj_apr_01, obj_apr_02, obj_apr_03])
    db.commit()

    # Procesos Internos (Hijos de Aprendizaje)
    obj_pro_01 = ObjetivoEstrategico(
        codigo="OBJ-PRO-01",
        nombre="Asegurar el cumplimiento eficiente del programa de manufactura BOM",
        descripcion="Procesar lotes programados de derivados sin retrasos en las líneas de cacao y coco.",
        perspectiva="PROCESOS_INTERNOS",
        modulo_odoo_id=mod_map["MOD-MRP"],
        responsable="Ing. Roberto Santillán (Planta Satipo)",
        prioridad="Alta",
        ponderacion=25.0,
        estado="Activo",
        objetivo_padre_id=obj_apr_01.id
    )
    obj_pro_02 = ObjetivoEstrategico(
        codigo="OBJ-PRO-02",
        nombre="Minimizar mermas operativas en prensado en frío de coco y tostado de cacao",
        descripcion="Reducir las pérdidas de materia prima e incrementar el rendimiento por tonelada.",
        perspectiva="PROCESOS_INTERNOS",
        modulo_odoo_id=mod_map["MOD-MRP"],
        responsable="Ing. Roberto Santillán (Planta Satipo)",
        prioridad="Alta",
        ponderacion=25.0,
        estado="Activo",
        objetivo_padre_id=obj_apr_01.id
    )
    obj_pro_03 = ObjetivoEstrategico(
        codigo="OBJ-PRO-03",
        nombre="Optimizar la rotación de lotes FIFO y condiciones de almacenamiento",
        descripcion="Garantizar despachos frescos sin mermas de caducidad ni deterioro de packaging.",
        perspectiva="PROCESOS_INTERNOS",
        modulo_odoo_id=mod_map["MOD-STOCK"],
        responsable="Sonia Alarcón (Almacenes y Calidad)",
        prioridad="Media",
        ponderacion=20.0,
        estado="Activo",
        objetivo_padre_id=obj_apr_01.id
    )
    obj_pro_04 = ObjetivoEstrategico(
        codigo="OBJ-PRO-04",
        nombre="Fortalecer la alianza y cumplimiento de entrega de cooperativas de Satipo/Pichanaqui",
        descripcion="Afianzar la cadena de suministro ético y abastecimiento oportuno de grano orgánico.",
        perspectiva="PROCESOS_INTERNOS",
        modulo_odoo_id=mod_map["MOD-PURCHASE"],
        responsable="Esteban Quispe (Acopio)",
        prioridad="Alta",
        ponderacion=15.0,
        estado="Activo",
        objetivo_padre_id=obj_apr_02.id
    )
    obj_pro_05 = ObjetivoEstrategico(
        codigo="OBJ-PRO-05",
        nombre="Mantener los parámetros técnicos de humedad e inocuidad en silos de acopio",
        descripcion="Control estricto de humedad (6.5% - 8.0%) para prevenir aflatoxinas y moho.",
        perspectiva="PROCESOS_INTERNOS",
        modulo_odoo_id=mod_map["MOD-STOCK"],
        responsable="Sonia Alarcón (Almacenes y Calidad)",
        prioridad="Alta",
        ponderacion=15.0,
        estado="Activo",
        objetivo_padre_id=obj_apr_01.id
    )
    db.add_all([obj_pro_01, obj_pro_02, obj_pro_03, obj_pro_04, obj_pro_05])
    db.commit()

    # Clientes (Hijos de Procesos Internos)
    obj_cli_01 = ObjetivoEstrategico(
        codigo="OBJ-CLI-01",
        nombre="Expandir la cuota de mercado en supermercados y biotiendas especializadas",
        descripcion="Consolidar presencia en Lima y principales capitales con productos 100% orgánicos.",
        perspectiva="CLIENTE",
        modulo_odoo_id=mod_map["MOD-SALE"],
        responsable="Ing. Marcos Paredes (Comercial)",
        prioridad="Alta",
        ponderacion=35.0,
        estado="Activo",
        objetivo_padre_id=obj_pro_01.id
    )
    obj_cli_02 = ObjetivoEstrategico(
        codigo="OBJ-CLI-02",
        nombre="Incrementar la efectividad de conversión de distribuidores mayoristas B2B",
        descripcion="Cierre oportuno de acuerdos comerciales a gran escala para exportación e intermediación.",
        perspectiva="CLIENTE",
        modulo_odoo_id=mod_map["MOD-CRM"],
        responsable="Valeria Huamán (Desarrollo B2B)",
        prioridad="Media",
        ponderacion=25.0,
        estado="Activo",
        objetivo_padre_id=obj_pro_03.id
    )
    obj_cli_03 = ObjetivoEstrategico(
        codigo="OBJ-CLI-03",
        nombre="Captar nuevos canales de venta directa y ferias agroindustriales",
        descripcion="Atraer consumidores finales con empaques retail en ferias saludables y puntos POS.",
        perspectiva="CLIENTE",
        modulo_odoo_id=mod_map["MOD-CRM"],
        responsable="Renata Castillo (Ventas Directas)",
        prioridad="Media",
        ponderacion=20.0,
        estado="Activo",
        objetivo_padre_id=obj_pro_04.id
    )
    obj_cli_04 = ObjetivoEstrategico(
        codigo="OBJ-CLI-04",
        nombre="Garantizar un nivel de satisfacción y fidelidad superior al 95%",
        descripcion="Cero reclamos por calidad, frescura y puntualidad en despachos logísticos.",
        perspectiva="CLIENTE",
        modulo_odoo_id=mod_map["MOD-SALE"],
        responsable="Ing. Marcos Paredes (Comercial)",
        prioridad="Media",
        ponderacion=20.0,
        estado="Activo",
        objetivo_padre_id=obj_pro_05.id
    )
    db.add_all([obj_cli_01, obj_cli_02, obj_cli_03, obj_cli_04])
    db.commit()

    # Financiera (Hijos de Cliente)
    obj_fin_01 = ObjetivoEstrategico(
        codigo="OBJ-FIN-01",
        nombre="Maximizar los ingresos totales facturados en el canal B2B mayorista",
        descripcion="Superar la meta mensual de facturación mediante ventas a grandes cuentas corporativas.",
        perspectiva="FINANCIERA",
        modulo_odoo_id=mod_map["MOD-ACCOUNT"],
        responsable="Lic. Carlos Mendoza (Finanzas)",
        prioridad="Alta",
        ponderacion=30.0,
        estado="Activo",
        objetivo_padre_id=obj_cli_01.id
    )
    obj_fin_02 = ObjetivoEstrategico(
        codigo="OBJ-FIN-02",
        nombre="Optimizar los márgenes brutos de las líneas derivadas de cacao y coco",
        descripcion="Sostener un margen superior al 45% reduciendo costos de manufactura y empaque.",
        perspectiva="FINANCIERA",
        modulo_odoo_id=mod_map["MOD-ACCOUNT"],
        responsable="Lic. Carlos Mendoza (Finanzas)",
        prioridad="Alta",
        ponderacion=30.0,
        estado="Activo",
        objetivo_padre_id=obj_cli_01.id
    )
    obj_fin_03 = ObjetivoEstrategico(
        codigo="OBJ-FIN-03",
        nombre="Fortalecer el flujo de caja y efectividad de arqueos en puntos POS",
        descripcion="Control estricto de cierres de caja y minimización de faltantes en venta retail.",
        perspectiva="FINANCIERA",
        modulo_odoo_id=mod_map["MOD-POS"],
        responsable="Renata Castillo (Ventas Directas)",
        prioridad="Media",
        ponderacion=20.0,
        estado="Activo",
        objetivo_padre_id=obj_cli_03.id
    )
    obj_fin_04 = ObjetivoEstrategico(
        codigo="OBJ-FIN-04",
        nombre="Acelerar la recuperación de cuentas por cobrar comerciales a 30 días",
        descripcion="Evitar morosidad de cadenas mayoristas y asegurar liquidez operativa para compra de materia prima.",
        perspectiva="FINANCIERA",
        modulo_odoo_id=mod_map["MOD-ACCOUNT"],
        responsable="Lic. Carlos Mendoza (Finanzas)",
        prioridad="Alta",
        ponderacion=20.0,
        estado="Activo",
        objetivo_padre_id=obj_cli_02.id
    )
    db.add_all([obj_fin_01, obj_fin_02, obj_fin_03, obj_fin_04])
    db.commit()

    # 5. INDICADORES KPI (14 KPIs exactos alineados a Odoo 17)
    kpis_data = [
        # FINANCIERA
        {
            "codigo": "FIN-01",
            "nombre": "Ventas Totales Facturadas B2B",
            "descripcion": "Total de facturas validadas en Odoo 17 por venta de derivados a cadenas y mayoristas.",
            "formula": "Suma de importes en account.move con state='posted' y type='out_invoice'",
            "unidad": "S/",
            "objetivo_id": obj_fin_01.id,
            "modulo_odoo": "Facturación (account)",
            "modelo_odoo": "account.move",
            "responsable": "Lic. Carlos Mendoza (Finanzas)",
            "frecuencia": "Mensual",
            "linea_base": 20000.0,
            "meta": 25000.0,
            "valor_actual": 24500.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        },
        {
            "codigo": "FIN-02",
            "nombre": "Margen Bruto Línea Aceite de Coco y Pasta de Cacao",
            "descripcion": "Margen porcentual sobre ventas netas tras descontar costo de insumos y mermas.",
            "formula": "((Ventas Netas - Costo de Ventas) / Ventas Netas) * 100",
            "unidad": "%",
            "objetivo_id": obj_fin_02.id,
            "modulo_odoo": "Facturación (account)",
            "modelo_odoo": "account.move",
            "responsable": "Lic. Carlos Mendoza (Finanzas)",
            "frecuencia": "Mensual",
            "linea_base": 42.0,
            "meta": 45.0,
            "valor_actual": 48.5,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        },
        {
            "codigo": "FIN-03",
            "nombre": "Efectividad de Arqueos de Caja POS",
            "descripcion": "Porcentaje de sesiones de punto de venta sin diferencias de efectivo o tarjeta.",
            "formula": "(Sesiones Cuadradas / Total Sesiones de Caja) * 100",
            "unidad": "%",
            "objetivo_id": obj_fin_03.id,
            "modulo_odoo": "Punto de Venta (point_of_sale)",
            "modelo_odoo": "pos.session",
            "responsable": "Renata Castillo (Ventas Directas)",
            "frecuencia": "Mensual",
            "linea_base": 92.0,
            "meta": 100.0,
            "valor_actual": 96.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 98.0,
            "umbral_amarillo": 95.0,
        },
        {
            "codigo": "FIN-04",
            "nombre": "Recuperación de Cuentas por Cobrar a 30 días",
            "descripcion": "Porcentaje de facturas a crédito cobradas puntualmente dentro de su vencimiento.",
            "formula": "(Monto Cobrado a Plazo / Monto Total Facturado a Crédito) * 100",
            "unidad": "%",
            "objetivo_id": obj_fin_04.id,
            "modulo_odoo": "Facturación (account)",
            "modelo_odoo": "account.move",
            "responsable": "Lic. Carlos Mendoza (Finanzas)",
            "frecuencia": "Mensual",
            "linea_base": 85.0,
            "meta": 95.0,
            "valor_actual": 78.0, # 78 / 95 * 100 = 82.1% -> Umbral verde 90, amarillo 85 -> En Alerta / Crítico
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 85.0,
        },

        # CLIENTE
        {
            "codigo": "CLI-01",
            "nombre": "Monto de Órdenes de Venta Confirmadas",
            "descripcion": "Valor monetario de pedidos firmados y confirmados en Odoo 17 (ej. Supermercados Peruanos S00001-S00003).",
            "formula": "Suma de amount_total en sale.order con state in ('sale', 'done')",
            "unidad": "S/",
            "objetivo_id": obj_cli_01.id,
            "modulo_odoo": "Ventas (sale_management)",
            "modelo_odoo": "sale.order",
            "responsable": "Ing. Marcos Paredes (Comercial)",
            "frecuencia": "Mensual",
            "linea_base": 12000.0,
            "meta": 15000.0,
            "valor_actual": 15800.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        },
        {
            "codigo": "CLI-02",
            "nombre": "Tasa de Conversión de Oportunidades B2B",
            "descripcion": "Proporción de iniciativas en el CRM que se convierten en contratos formales de distribución.",
            "formula": "(Oportunidades Ganadas / Oportunidades Totales en Pipeline) * 100",
            "unidad": "%",
            "objetivo_id": obj_cli_02.id,
            "modulo_odoo": "CRM (crm)",
            "modelo_odoo": "crm.lead",
            "responsable": "Valeria Huamán (Desarrollo B2B)",
            "frecuencia": "Mensual",
            "linea_base": 30.0,
            "meta": 40.0,
            "valor_actual": 35.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        },
        {
            "codigo": "CLI-03",
            "nombre": "Nuevos Distribuidores y Bio Tiendas Captados",
            "descripcion": "Número de nuevas tiendas ecológicas y mayoristas dados de alta en el maestro de contactos.",
            "formula": "Conteo de res.partner con categoría 'Distribuidor_Bio' creados en el mes",
            "unidad": "Unidades",
            "objetivo_id": obj_cli_03.id,
            "modulo_odoo": "CRM (crm)",
            "modelo_odoo": "res.partner",
            "responsable": "Valeria Huamán (Desarrollo B2B)",
            "frecuencia": "Mensual",
            "linea_base": 6.0,
            "meta": 10.0,
            "valor_actual": 11.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 70.0,
        },

        # PROCESOS INTERNOS
        {
            "codigo": "PRO-01",
            "nombre": "Cumplimiento de Órdenes de Fabricación BOM",
            "descripcion": "Porcentaje de lotes de manufactura completados dentro del tiempo estándar de lista de materiales.",
            "formula": "(Órdenes Terminadas a Tiempo / Órdenes Planificadas) * 100",
            "unidad": "%",
            "objetivo_id": obj_pro_01.id,
            "modulo_odoo": "Manufactura BOM (mrp)",
            "modelo_odoo": "mrp.production",
            "responsable": "Ing. Roberto Santillán (Planta Satipo)",
            "frecuencia": "Mensual",
            "linea_base": 88.0,
            "meta": 95.0,
            "valor_actual": 92.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 95.0,
            "umbral_amarillo": 85.0,
        },
        {
            "codigo": "PRO-02",
            "nombre": "Merma en Extracción de Aceite de Coco Extra Virgen",
            "descripcion": "Pérdida porcentual de materia prima durante el proceso de prensado y centrifugado mecánico.",
            "formula": "((Kg Coco Entrada - Kg Aceite Obtenido / Rendimiento Teórico) / Kg Entrada) * 100",
            "unidad": "%",
            "objetivo_id": obj_pro_02.id,
            "modulo_odoo": "Manufactura BOM (mrp)",
            "modelo_odoo": "mrp.production",
            "responsable": "Ing. Roberto Santillán (Planta Satipo)",
            "frecuencia": "Mensual",
            "linea_base": 5.5,
            "meta": 4.0,
            "valor_actual": 6.2, # Crítico! Sentido MENOR_MEJOR: 4.0 / 6.2 * 100 = 64.52% < 75%
            "sentido": "MENOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        },
        {
            "codigo": "PRO-03",
            "nombre": "Rotación de Lotes Vigentes sin Merma por Caducidad",
            "descripcion": "Trazabilidad de lotes despachados respetando estrictamente la política FIFO sin vencimientos.",
            "formula": "(Lotes Despachados en Óptima Vigencia / Total Lotes Movilizados) * 100",
            "unidad": "%",
            "objetivo_id": obj_pro_03.id,
            "modulo_odoo": "Inventario y Lotes (stock)",
            "modelo_odoo": "stock.lot",
            "responsable": "Sonia Alarcón (Almacenes y Calidad)",
            "frecuencia": "Mensual",
            "linea_base": 96.0,
            "meta": 98.0,
            "valor_actual": 99.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 95.0,
            "umbral_amarillo": 85.0,
        },
        {
            "codigo": "PRO-04",
            "nombre": "Cumplimiento de Entregas de Cacao y Coco de Cooperativas Satipo/Pichanaqui",
            "descripcion": "Puntualidad y volumen entregado por los comités agrarios según órdenes de compra purchase.order.",
            "formula": "(Órdenes de Compra Recibidas a Tiempo y Conformes / Órdenes Emitidas) * 100",
            "unidad": "%",
            "objetivo_id": obj_pro_04.id,
            "modulo_odoo": "Compras (purchase)",
            "modelo_odoo": "purchase.order",
            "responsable": "Esteban Quispe (Acopio)",
            "frecuencia": "Mensual",
            "linea_base": 80.0,
            "meta": 90.0,
            "valor_actual": 85.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 80.0,
        },
        {
            "codigo": "PRO-05",
            "nombre": "Humedad de Almacenamiento de Grano de Cacao Seco",
            "descripcion": "Control del rango higrométrico óptimo (6.5% a 8.0%) en sacos de yute para prevenir hongos.",
            "formula": "Medición termohigrométrica certificada en lotes de almacén",
            "unidad": "%",
            "objetivo_id": obj_pro_05.id,
            "modulo_odoo": "Inventario y Lotes (stock)",
            "modelo_odoo": "stock.lot",
            "responsable": "Sonia Alarcón (Almacenes y Calidad)",
            "frecuencia": "Mensual",
            "linea_base": 7.4,
            "meta": 7.25,
            "valor_actual": 7.2,
            "sentido": "RANGO",
            "rango_min": 6.5,
            "rango_max": 8.0,
            "umbral_verde": 95.0,
            "umbral_amarillo": 80.0,
        },

        # APRENDIZAJE Y CRECIMIENTO
        {
            "codigo": "APR-01",
            "nombre": "Operarios Certificados en BPM y Control de Calidad",
            "descripcion": "Personal de planta que aprobó la recertificación de Buenas Prácticas de Manufactura e Higiene.",
            "formula": "(Operarios con Examen BPM >= 16 / Total Operarios en Planilla de Planta) * 100",
            "unidad": "%",
            "objetivo_id": obj_apr_01.id,
            "modulo_odoo": "Empleados y Planta (hr)",
            "modelo_odoo": "hr.employee",
            "responsable": "Dra. Elena Vargas (Talento Humano)",
            "frecuencia": "Mensual",
            "linea_base": 80.0,
            "meta": 100.0,
            "valor_actual": 90.0,
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 95.0,
            "umbral_amarillo": 85.0,
        },
        {
            "codigo": "APR-02",
            "nombre": "Evaluación de Clima Laboral en Planta Satipo",
            "descripcion": "Índice de satisfacción laboral medido anualmente. Sin mediciones registradas en el período.",
            "formula": "Puntaje promedio encuesta de clima laboral / Escala máxima * 100",
            "unidad": "%",
            "objetivo_id": obj_apr_02.id,
            "modulo_odoo": "Empleados y Planta (hr)",
            "modelo_odoo": "hr.employee",
            "responsable": "Dra. Elena Vargas (Talento Humano)",
            "frecuencia": "Trimestral",
            "linea_base": 75.0,
            "meta": 85.0,
            "valor_actual": None, # REGLA 1: SIN DATOS (No mediciones)
            "sentido": "MAYOR_MEJOR",
            "umbral_verde": 90.0,
            "umbral_amarillo": 75.0,
        }
    ]

    for kdata in kpis_data:
        kpi_obj = IndicadorKpi(**kdata)
        db.add(kpi_obj)
    db.commit()

    # Mapeo de KPIs para mediciones e iniciativas
    kpis_db = {k.codigo: k for k in db.query(IndicadorKpi).all()}

    # 6. HISTORIAL DE MEDICIONES (6 MESES: Mayo a Octubre 2026) para los KPIs 1 al 13
    # Simula evolución real con tendencia al alza o alertas
    historico_valores = {
        "FIN-01": [21500.0, 22200.0, 23100.0, 23800.0, 24100.0, 24500.0],
        "FIN-02": [43.5, 44.0, 45.2, 46.0, 47.1, 48.5],
        "FIN-03": [94.0, 95.0, 97.0, 95.5, 96.0, 96.0],
        "FIN-04": [88.0, 86.5, 84.0, 82.0, 80.0, 78.0], # Tendencia a la baja (Crítico)
        "CLI-01": [12800.0, 13400.0, 14100.0, 14700.0, 15200.0, 15800.0],
        "CLI-02": [31.0, 32.5, 33.0, 34.0, 34.5, 35.0],
        "CLI-03": [7.0, 8.0, 8.0, 9.0, 10.0, 11.0],
        "PRO-01": [89.0, 90.5, 91.0, 91.5, 91.0, 92.0],
        "PRO-02": [4.8, 5.0, 5.3, 5.7, 6.0, 6.2], # Merma subiendo (Crítico)
        "PRO-03": [97.0, 97.5, 98.0, 98.5, 99.0, 99.0],
        "PRO-04": [82.0, 83.0, 84.0, 84.5, 86.0, 85.0],
        "PRO-05": [7.4, 7.35, 7.3, 7.28, 7.22, 7.20], # Dentro del rango óptimo
        "APR-01": [82.0, 84.0, 86.0, 88.0, 88.0, 90.0]
        # "APR-02" no tiene mediciones registradas a propósito
    }

    periodos_codigos = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
    fechas_medicion = ["2026-05-28", "2026-06-28", "2026-07-28", "2026-08-28", "2026-09-28", "2026-10-25"]

    for k_cod, valores in historico_valores.items():
        kpi_inst = kpis_db.get(k_cod)
        if not kpi_inst:
            continue

        for i, val in enumerate(valores):
            med = MedicionKpi(
                kpi_id=kpi_inst.id,
                periodo=periodos_codigos[i],
                fecha=fechas_medicion[i],
                valor_obtenido=val,
                observaciones=f"Cierre de medición mensual per {periodos_codigos[i]}",
                responsable=kpi_inst.responsable,
                origen="MANUAL" if i < 5 else "ODOO_17_SYNC"
            )
            db.add(med)

    db.commit()

    # 7. INICIATIVAS ESTRATÉGICAS (8 proyectos estratégicos con presupuesto en Soles)
    iniciativas_demo = [
        IniciativaEstrategica(
            codigo="INI-01",
            nombre="Automatización de Prensa Hidráulica para Aceite de Coco",
            descripcion="Instalación de sensores de presión continua y control de temperatura para abatir la merma del 6.2% al 4.0%.",
            objetivo_id=obj_pro_02.id,
            kpi_id=kpis_db["PRO-02"].id,
            modulo_odoo="Manufactura BOM (mrp)",
            responsable="Ing. Roberto Santillán",
            presupuesto=45000.0,
            fecha_inicio="2026-08-01",
            fecha_fin="2026-11-30",
            porcentaje_avance=65.0,
            estado="EN_EJECUCION"
        ),
        IniciativaEstrategica(
            codigo="INI-02",
            nombre="Plan de Recuperación de Cartera Morosa B2B y Política de Crédito",
            descripcion="Revisión de líneas de crédito en Odoo 17 y acuerdos de pronto pago con cadenas minoristas.",
            objetivo_id=obj_fin_04.id,
            kpi_id=kpis_db["FIN-04"].id,
            modulo_odoo="Facturación (account)",
            responsable="Lic. Carlos Mendoza",
            presupuesto=18000.0,
            fecha_inicio="2026-09-01",
            fecha_fin="2026-10-31",
            porcentaje_avance=40.0,
            estado="RETRASADA"
        ),
        IniciativaEstrategica(
            codigo="INI-03",
            nombre="Campaña Comercial 'Poder del Cacao Criollo' en Supermercados Peruanos",
            descripcion="Activaciones en punto de venta, degustación de nibs orgánicos y pasta pura de cacao.",
            objetivo_id=obj_cli_01.id,
            kpi_id=kpis_db["CLI-01"].id,
            modulo_odoo="Ventas (sale_management)",
            responsable="Ing. Marcos Paredes",
            presupuesto=32000.0,
            fecha_inicio="2026-07-01",
            fecha_fin="2026-10-15",
            porcentaje_avance=100.0,
            estado="FINALIZADA"
        ),
        IniciativaEstrategica(
            codigo="INI-04",
            nombre="Programa de Acopio Fitosanitario con Cooperativa Satipo",
            descripcion="Talleres de fermentación homogénea en cajones de madera laurel y secado solar bajo carpas.",
            objetivo_id=obj_pro_04.id,
            kpi_id=kpis_db["PRO-04"].id,
            modulo_odoo="Compras (purchase)",
            responsable="Esteban Quispe",
            presupuesto=25000.0,
            fecha_inicio="2026-06-15",
            fecha_fin="2026-12-15",
            porcentaje_avance=75.0,
            estado="EN_EJECUCION"
        ),
        IniciativaEstrategica(
            codigo="INI-05",
            nombre="Auditoría y Certificación Internacional HACCP y USDA Organic",
            descripcion="Capacitación intensiva de operarios en BPM y homologación de líneas de envasado.",
            objetivo_id=obj_apr_01.id,
            kpi_id=kpis_db["APR-01"].id,
            modulo_odoo="Empleados y Planta (hr)",
            responsable="Dra. Elena Vargas",
            presupuesto=38000.0,
            fecha_inicio="2026-05-01",
            fecha_fin="2026-10-31",
            porcentaje_avance=90.0,
            estado="EN_EJECUCION"
        ),
        IniciativaEstrategica(
            codigo="INI-06",
            nombre="Despliegue de Terminales POS Táctiles en Tienda de Fábrica y Ferias",
            descripcion="Integración directa de lectores de código de barras y arqueo digital en Odoo POS.",
            objetivo_id=obj_fin_03.id,
            kpi_id=kpis_db["FIN-03"].id,
            modulo_odoo="Punto de Venta (point_of_sale)",
            responsable="Renata Castillo",
            presupuesto=15000.0,
            fecha_inicio="2026-08-15",
            fecha_fin="2026-10-01",
            porcentaje_avance=100.0,
            estado="FINALIZADA"
        ),
        IniciativaEstrategica(
            codigo="INI-07",
            nombre="Modernización de Silos de Cacao con Monitoreo IoT de Humedad",
            descripcion="Sondas continuas de temperatura y humedad relativa conectadas a alertas en tiempo real.",
            objetivo_id=obj_pro_05.id,
            kpi_id=kpis_db["PRO-05"].id,
            modulo_odoo="Inventario y Lotes (stock)",
            responsable="Sonia Alarcón",
            presupuesto=28000.0,
            fecha_inicio="2026-09-15",
            fecha_fin="2026-12-30",
            porcentaje_avance=50.0,
            estado="EN_EJECUCION"
        ),
        IniciativaEstrategica(
            codigo="INI-08",
            nombre="Encuesta Integral de Clima Laboral y Bienestar en Planta Satipo",
            descripcion="Diagnóstico psicosocial, plan de reconocimientos y mejoras ergonómicas en empaque.",
            objetivo_id=obj_apr_02.id,
            kpi_id=kpis_db["APR-02"].id,
            modulo_odoo="Empleados y Planta (hr)",
            responsable="Dra. Elena Vargas",
            presupuesto=12000.0,
            fecha_inicio="2026-10-15",
            fecha_fin="2026-11-30",
            porcentaje_avance=20.0,
            estado="EN_EJECUCION"
        )
    ]
    db.add_all(iniciativas_demo)
    db.commit()

    # 8. Sincronizar y recalcular todo el BSC para dejar los semáforos y cálculos listos
    recalcular_todo_el_bsc(db, "2026-10")

    # Registro de log inicial
    db.add(SyncLog(
        origen="SISTEMA_INIT",
        modulo="TODOS",
        estado="EXITOSO",
        registros_procesados=13,
        mensaje_detalle="Precarga estratégica completa de AGRO PERUVIAN FOODS S.A.C. finalizada exitosamente."
    ))
    db.commit()

    logger.info("Precarga estratégica completada con éxito.")
