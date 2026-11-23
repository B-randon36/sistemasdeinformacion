import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import PROJECT_NAME, API_V1_STR, PORT
from app.database import engine, Base, get_db, SessionLocal
import app.models
from app.models import Periodo
from app.services.seed_data import precargar_datos_si_vacio

# Routers
from app.routers import (
    auth, dashboard, objetivos, kpis,
    mediciones, iniciativas, reportes, odoo_sync, admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar tablas en base de datos
    Base.metadata.create_all(bind=engine)
    # Precargar datos si la BD está limpia y normalizar etiquetas de período activo
    db = SessionLocal()
    try:
        precargar_datos_si_vacio(db)
        changed = False
        for p in db.query(Periodo).all():
            if not p.activo and " (Período Actual)" in p.nombre:
                p.nombre = p.nombre.replace(" (Período Actual)", "")
                changed = True
            elif p.activo and "(Período Actual)" not in p.nombre:
                p.nombre = f"{p.nombre} (Período Actual)"
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(
    title=PROJECT_NAME,
    version="1.0.0",
    description="Cuadro de Mando Integral (BSC) para AGRO PERUVIAN FOODS S.A.C. integrado con Odoo 17 ERP",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Routers de la API RESTful
app.include_router(auth.router, prefix=API_V1_STR)
app.include_router(dashboard.router, prefix=API_V1_STR)
app.include_router(objetivos.router, prefix=API_V1_STR)
app.include_router(kpis.router, prefix=API_V1_STR)
app.include_router(mediciones.router, prefix=API_V1_STR)
app.include_router(iniciativas.router, prefix=API_V1_STR)
app.include_router(reportes.router, prefix=API_V1_STR)
app.include_router(odoo_sync.router, prefix=API_V1_STR)
app.include_router(admin.router, prefix=API_V1_STR)

@app.get("/api/v1/health", tags=["Estado"])
def health_check():
    return {
        "status": "online",
        "empresa": "AGRO PERUVIAN FOODS S.A.C.",
        "sistema": "Balanced Scorecard Enterprise Odoo 17",
        "version": "1.0.0"
    }

# Servir archivos estáticos del Frontend
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    logo_path = os.path.join(static_dir, "img", "logo_agroperuvian.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return Response(status_code=204)

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"mensaje": "AGRO PERUVIAN FOODS S.A.C. - BSC Backend Activo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
