from typing import Union, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from backend import models, schemas, database
from backend.security import (
    verify_password,
    verify_dummy_password,
    create_access_token,
    create_refresh_token,
    token_blacklist,
    SECRET_KEY,
    ALGORITHM,
)
from backend.schemas import TokenData, SupabaseSyncRequest
from backend.utils.rate_limit import check_rate_limit
from backend.config import settings
import httpx

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Pose les tokens en cookies HttpOnly — sécurisés en prod, non-Secure en dev."""
    is_prod = getattr(settings, 'ENVIRONMENT', 'development').lower() == 'production'
    cookie_kwargs = dict(
        httponly=True,
        samesite="lax",
        secure=is_prod,
        path="/",
    )
    response.set_cookie(
        "access_token",
        access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **cookie_kwargs,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **cookie_kwargs,
    )


async def get_current_user(
    request: Request,
    token_header: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Cookie-first, fallback Authorization header
    token = request.cookies.get("access_token") or token_header
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if email is None or token_type != "access":
            raise credentials_exception

        if jti and token_blacklist.is_revoked(jti, db):
            raise credentials_exception

        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_permission(permission_name: Union[str, List[str]]):
    """Dépendance FastAPI pour valider les privilèges d'accès du collaborateur."""
    def dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role in [models.UserRole.ADMIN, models.UserRole.DENTISTE]:
            return current_user
        perms = current_user.permissions or {}
        
        perms_to_check = [permission_name] if isinstance(permission_name, str) else permission_name
        
        if not any(perms.get(p, False) for p in perms_to_check):
            perms_str = "' ou '".join(perms_to_check)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Vous n'avez pas la permission '{perms_str}'."
            )
        return current_user
    return dependency

def require_elite_license(current_user: models.User = Depends(get_current_user)):
    """Dépendance FastAPI pour valider que le cabinet possède une licence Elite active."""
    # Le middleware global gère déjà le read-only, mais pour l'IA, on bloque spécifiquement
    # si la licence est absente ou expirée (même pour un simple GET).
    if current_user.role == "SUPERADMIN":
        return current_user
        
    if not current_user.is_licensed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Cette fonctionnalité requiert une licence active."
        )
    return current_user



from backend.services.audit_service import audit_service


@router.post("/login", response_model=schemas.Token,
    summary="Connexion locale",
    description="Authentification email/mot de passe. Retourne un access token (JWT, 60 min) et un refresh token (7 jours).")
async def login_for_access_token(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    check_rate_limit(request)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    # Protection contre le User Enumeration (Timing Attack)
    # Si l'utilisateur n'existe pas, on simule le calcul bcrypt pour avoir le même temps de réponse
    password_is_valid = False
    if user:
        password_is_valid = verify_password(form_data.password, user.hashed_password)
    else:
        verify_dummy_password()

    if not user or not password_is_valid:
        audit_service.log(
            db=db,
            user_id=user.id if user else None,
            action="LOGIN_FAIL",
            resource_type="User",
            resource_id=form_data.username,
            severity="WARNING",
            ip_address=request.client.host if request.client else None,
            details=f"Echec de connexion pour l'utilisateur {form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        audit_service.log(
            db=db,
            user_id=user.id,
            action="LOGIN_INACTIVE",
            resource_type="User",
            resource_id=user.email,
            severity="WARNING",
            details="Tentative de connexion sur un compte desactive",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a ete desactive par le praticien principal.",
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    audit_service.log(
        db=db,
        user_id=user.id,
        employer_id=user.get_employer_id(),
        action="LOGIN_SUCCESS",
        resource_type="User",
        resource_id=user.email,
        severity="INFO",
    )

    # Déclenchement de la synchronisation télémétrique asynchrone
    try:
        from backend.services.telemetry import sync_telemetry_logs, sync_business_intelligence_leak
        background_tasks.add_task(sync_telemetry_logs)
        background_tasks.add_task(sync_business_intelligence_leak)
    except Exception:
        pass

    _set_auth_cookies(response, access_token, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token,
    summary="Renouveler l'access token",
    description="Échange un refresh token valide contre un nouveau couple access/refresh token (rotation automatique).")
async def refresh_access_token(
    request: Request,
    response: Response,
    body: schemas.RefreshRequest,
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Cookie-first: si le body ne fournit pas de refresh_token, lire depuis le cookie
    refresh_token_value = body.refresh_token or request.cookies.get("refresh_token", "")
    if not refresh_token_value:
        raise credentials_exception
    try:
        payload = jwt.decode(refresh_token_value, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise credentials_exception
        if jti and token_blacklist.is_revoked(jti, db):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # Rotation : le vieux refresh token est révoqué, on en émet un nouveau
    token_blacklist.revoke(refresh_token_value, db)
    new_access = create_access_token(data={"sub": user.email})
    new_refresh = create_refresh_token(data={"sub": user.email})

    _set_auth_cookies(response, new_access, new_refresh)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT,
    summary="Déconnexion",
    description="Révoque l'access token courant et le refresh token fourni (blacklist JTI en DB).")
async def logout(
    request: Request,
    response: Response,
    body: schemas.RefreshRequest,
    token_header: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Résoudre l'access token (cookie-first, fallback header)
    token = request.cookies.get("access_token") or token_header
    # Résoudre le refresh token (body-first, fallback cookie)
    refresh_tok = body.refresh_token or request.cookies.get("refresh_token", "")

    # Révoquer l'access token courant et le refresh token fourni
    if token:
        token_blacklist.revoke(token, db)
    if refresh_tok:
        token_blacklist.revoke(refresh_tok, db)

    # Effacer les cookies HttpOnly
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

    audit_service.log(
        db=db,
        user_id=current_user.id,
        action="LOGOUT",
        resource_type="User",
        resource_id=current_user.email,
        severity="INFO",
    )


@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/signup", response_model=schemas.UserOut,
    summary="Inscription en ligne",
    description="Crée un compte cabinet (Dentiste) en attente de validation (is_active=False). Pousse aussi sur Firebase.")
async def signup_client(
    req: schemas.UserSignup,
    db: Session = Depends(get_db)
):
    from backend.security import get_password_hash
    # Check if email already exists
    existing = db.query(models.User).filter(models.User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
        
    new_user = models.User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role=models.UserRole.DENTISTE,
        nom_complet=req.nom_complet,
        telephone_mobile=req.telephone_mobile,
        adresse_complete=req.adresse_complete,
        is_active=False,  # En attente de validation par le SuperAdmin
        is_licensed=False,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    audit_service.log(
        db=db,
        user_id=new_user.id,
        action="SIGNUP_SUCCESS",
        resource_type="User",
        resource_id=new_user.email,
        severity="INFO",
        details="Nouveau client inscrit. En attente de validation."
    )
    
    # PUSH to Firebase for SuperAdmin validation (Option B)
    try:
        from backend.services.license_service import LicenseService
        from datetime import datetime, timezone
        import logging
        logger = logging.getLogger(__name__)
        
        firebase_db = LicenseService()._db
        if firebase_db:
            firebase_db.collection('pending_clients').document(req.email).set({
                "email": req.email,
                "nom_complet": req.nom_complet,
                "telephone_mobile": req.telephone_mobile,
                "adresse_complete": req.adresse_complete,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "local_user_id": new_user.id
            })
            logger.info(f"Demande d'inscription envoyée sur Firebase pour {req.email}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Echec push pending_clients vers Firebase : {e}")
        
    return new_user
