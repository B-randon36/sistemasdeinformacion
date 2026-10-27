from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UsuarioResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == request.username).first()
    if not user or user.password != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifique su usuario y contraseña."
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo en el sistema."
        )

    # Token simple para demo empresarial
    fake_token = f"agro_token_{user.username}_{user.id}"
    return {
        "access_token": fake_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)):
    users = db.query(Usuario).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "password": u.password,
            "nombre": u.nombre,
            "rol": u.rol,
            "area": u.area
        }
        for u in users
    ]
