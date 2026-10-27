from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SyncLog, Periodo
from app.services.odoo_connector import odoo_connector
from app.schemas import SyncResponse

router = APIRouter(prefix="/bsc", tags=["Integración Odoo 17 ERP"])

@router.post("/sync-odoo", response_model=SyncResponse)
def sincronizar_odoo(
    periodo: Optional[str] = Query(None, description="Período a sincronizar, ej. 2026-10"),
    db: Session = Depends(get_db)
):
    if not periodo:
        periodo_activo = db.query(Periodo).filter(Periodo.activo == True).first()
        periodo = periodo_activo.codigo if periodo_activo else "2026-10"

    resultado = odoo_connector.sincronizar_metricas_completas(db, periodo)
    return resultado

@router.get("/sync-status")
def get_sync_status():
    status_odoo = odoo_connector.probar_conexion_odoo()
    status_n8n = odoo_connector.probar_conexion_n8n()
    return {
        "odoo_17": status_odoo,
        "n8n_webhook": status_n8n,
        "configuracion": {
            "odoo_url": odoo_connector.url,
            "odoo_db": odoo_connector.db,
            "odoo_user": odoo_connector.user,
            "n8n_webhook_url": odoo_connector.n8n_url
        }
    }

@router.get("/sync-logs")
def get_sync_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(SyncLog).order_by(SyncLog.fecha.desc()).limit(limit).all()
    return logs
