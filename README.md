# Balanced Scorecard (Cuadro de Mando Integral) - AGRO PERUVIAN FOODS S.A.C.
### Integración Estratégica con ERP Odoo 17 (`agroperuvian_db`)

Sistema empresarial completo para la gestión y monitoreo estratégico de la empresa agroindustrial **AGRO PERUVIAN FOODS S.A.C.** (productora y exportadora de derivados de cacao criollo y coco de la selva central peruana - Satipo y Pichanaqui).

---

## 🏛️ 1. Alineación con los Módulos de Odoo 17 ERP

Todos los **Objetivos Estratégicos (16)**, **Indicadores KPI (14)**, **Mediciones** e **Iniciativas (8)** están estrictamente clasificados por las **4 Perspectivas del BSC** y los **Módulos de Odoo 17**:

| Perspectiva BSC | Módulo de Odoo 17 | Modelo Técnico Odoo | Indicadores Clave |
| :--- | :--- | :--- | :--- |
| **Financiera** | Facturación (`account`) & Punto de Venta (`point_of_sale`) | `account.move`, `pos.session` | `FIN-01`, `FIN-02`, `FIN-03`, `FIN-04` |
| **Cliente** | CRM (`crm`) & Ventas (`sale_management`) | `sale.order`, `crm.lead`, `res.partner` | `CLI-01`, `CLI-02`, `CLI-03` |
| **Procesos Internos** | Manufactura BOM (`mrp`), Inventario (`stock`) & Compras (`purchase`) | `mrp.production`, `stock.lot`, `purchase.order` | `PRO-01`, `PRO-02`, `PRO-03`, `PRO-04`, `PRO-05` |
| **Aprendizaje y Crecimiento** | Empleados y Planta (`hr`) | `hr.employee` | `APR-01`, `APR-02` *(Regla 1 Sin Datos)* |

---

## ⚙️ 2. Arquitectura de Software

- **Backend:** FastAPI (Python 3.13) con arquitectura modular (`app/database.py`, `app/models.py`, `app/schemas.py`, `app/services/bsc_engine.py`, `app/services/odoo_connector.py`, `app/routers/`).
- **Base de Datos:** SQLAlchemy 2.0 con soporte relacional SQLite local (`agroperuvian_bsc.db`) y conmutación automática de contingencia.
- **Integración Odoo 17:** Conector XML-RPC nativo hacia `http://localhost:8069` o `http://odoo:8069` (`agroperuvian_db`) con timeout de 3.0s y motor resiliente de contingencia que extrae métricas de `sale.order`, `crm.lead`, `mrp.production`, `pos.session` y `purchase.order`.
- **Frontend SPA:** Single Page Application construida con Tailwind CSS, Chart.js 4.4, FontAwesome 6, Google Fonts (Inter & Outfit), diseño responsive con dark mode corporativo y soporte de exportación a CSV y PDF (`@media print`).

---

## 📈 3. Las 14 Reglas de Negocio Implementadas en `bsc_engine.py`

1. **Regla de Sin Datos:** Si un KPI no posee mediciones registradas en el período, su estado es `SIN_DATOS` (gris) y **nunca** `CUMPLIDO` (`APR-02`).
2. **Regla Mayor es Mejor:** `cumplimiento = (valor_actual / meta) * 100` con control de división por cero.
3. **Regla Menor es Mejor (ej. Merma en Aceite de Coco Extra Virgen %):** Si `valor_actual <= meta`, cumplimiento &ge; 100%; si `valor_actual > meta`, `cumplimiento = (meta / valor_actual) * 100` (`PRO-02`).
4. **Regla de Rango Óptimo (ej. Humedad de Silos de Cacao 6.5% - 8.0%):** 100% de cumplimiento dentro del intervalo óptimo, con penalización proporcional simétrica en los extremos (`PRO-05`).
5. **Semáforo Automático:**
   - `CUMPLIDO` (Verde) si cumplimiento &ge; `umbral_verde` (por defecto 90%).
   - `EN_ALERTA` (Amarillo) si cumplimiento &ge; `umbral_amarillo` y < `umbral_verde` (75% - 89.9%).
   - `CRITICO` (Rojo) si cumplimiento < `umbral_amarillo` (< 75%).
6. **Recalculación Automática en Cascada:** Al registrar, modificar o sincronizar una `MedicionKpi`, se actualiza el `valor_actual`, `% de cumplimiento` y `semaforo` del KPI, recalculando el avance del Objetivo Estratégico, la Perspectiva y el **Cumplimiento Global Ponderado**.
7. **Sincronización Odoo 17 / n8n:** Endpoint `POST /api/v1/bsc/sync-odoo` con fallback automático y trazabilidad en `SyncLog`.
8. **Ponderación Estratégica:** Cumplimiento global calculado mediante media ponderada normalizada de los objetivos.
9. **Causa-Efecto:** Trazabilidad de objetivos ascendentes y descendentes en el Mapa Estratégico.
10. **Trazabilidad de Auditoría:** Registro de origen `MANUAL` vs `ODOO_17_SYNC` por medición.
11. **Historial Cronológico:** Seguimiento de mediciones mensuales de 6 períodos (Mayo a Octubre 2026).
12. **Control Presupuestal en Soles:** Seguimiento de presupuesto y % de avance en Iniciativas Estratégicas.
13. **Seguridad y Roles:** Perfiles `ADMIN`, `GERENTE` y `RESPONSABLE` con restricciones de interfaz.
14. **Exportabilidad:** Generación de CSV descargable y maquetación de impresión ejecutiva para reportes de directorio.

---

## 👥 4. Credenciales de Demostración

| Rol | Usuario | Contraseña | Área |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` | Dirección de Estrategia y TI |
| **Gerente General** | `gerente` | `gerente123` | Gerencia General |
| **Jefe de Planta MRP** | `jefe_mrp` | `mrp123` | Operaciones y Manufactura (Satipo) |

---

## 🚀 5. Guía de Inicialización y Ejecución

### Opción A: Ejecutar en el Servidor AWS EC2 (Puerto 8000)

1. **Conectarse al servidor por SSH:**
   ```bash
   ssh -i "awz-ccalla.pem" ubuntu@<IP_PUBLICA_EC2>
   ```

2. **Ingresar a la carpeta del proyecto y activar el entorno:**
   ```bash
   cd ~/bsc-agroperuvian
   source venv/bin/activate
   ```

3. **Verificar el archivo `.env`:**
   Asegúrate de que tenga el puerto 8000 configurado:
   ```env
   PORT=8000
   DATABASE_URL=sqlite:///./agroperuvian_bsc.db
   ODOO_URL=http://localhost:8069
   ODOO_DB=agroperuvian_db
   ODOO_USER=admin@agroperuvian.pe
   ODOO_PASSWORD=admin_odoo_secure_2026
   ```

4. **Encender la aplicación en primer plano:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   *Acceso web:* `http://<IP_PUBLICA_EC2>:8000`  
   *(Para detener la aplicación, presiona `Ctrl + C` en la terminal).*

---

### Opción B: Ejecutar en tu Computadora Local (Puerto 8001)

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar servidor:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. **Acceder:**
   - Aplicación Web: `http://localhost:8001/`
   - Documentación Swagger API: `http://localhost:8001/docs`
