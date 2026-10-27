from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario, Periodo, ModuloOdooArea
from app.schemas import (
    UsuarioCreate, UsuarioResponse,
    PeriodoCreate, PeriodoResponse,
    ModuloOdooCreate, ModuloOdooResponse
)

router = APIRouter(prefix="/admin", tags=["Administración del Sistema"])

# --- USUARIOS ---
@router.get("/usuarios", response_model=List[UsuarioResponse])
def get_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.username == data.username).first()
    if existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

    user = Usuario(**data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/usuarios/{id}")
def delete_usuario(id: int, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el usuario administrador principal.")

    db.delete(user)
    db.commit()
    return {"mensaje": "Usuario eliminado exitosamente."}

# --- PERIODOS ---
@router.get("/periodos", response_model=List[PeriodoResponse])
def get_periodos(db: Session = Depends(get_db)):
    return db.query(Periodo).order_by(Periodo.codigo.desc()).all()

@router.post("/periodos", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
def create_periodo(data: PeriodoCreate, db: Session = Depends(get_db)):
    existente = db.query(Periodo).filter(Periodo.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail="El código de período ya existe.")

    periodo = Periodo(**data.model_dump())
    if periodo.activo:
        # Desactivar los demás
        db.query(Periodo).update({Periodo.activo: False})

    db.add(periodo)
    db.commit()
    db.refresh(periodo)
    return periodo

@router.put("/periodos/{id}/activar")
def activar_periodo(id: int, db: Session = Depends(get_db)):
    periodo = db.query(Periodo).filter(Periodo.id == id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Período no encontrado.")

    db.query(Periodo).update({Periodo.activo: False})
    periodo.activo = True
    db.commit()
    return {"mensaje": f"Período {periodo.codigo} activado como oficial."}

# --- MODULOS ODOO ---
@router.get("/modulos-odoo", response_model=List[ModuloOdooResponse])
def get_modulos_odoo(db: Session = Depends(get_db)):
    return db.query(ModuloOdooArea).all()

@router.post("/modulos-odoo", response_model=ModuloOdooResponse, status_code=status.HTTP_201_CREATED)
def create_modulo_odoo(data: ModuloOdooCreate, db: Session = Depends(get_db)):
    existente = db.query(ModuloOdooArea).filter(ModuloOdooArea.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail="El código de módulo Odoo ya existe.")

    modulo = ModuloOdooArea(**data.model_dump())
    db.add(modulo)
    db.commit()
    db.refresh(modulo)
    return modulo
