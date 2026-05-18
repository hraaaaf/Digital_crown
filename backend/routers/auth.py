from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from backend import models, schemas, database
from backend.security import (
    verify_password,
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
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


from backend.services.audit_service import audit_service


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    check_rate_limit(request)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
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
    token_blacklist.revoke(body.refresh_token, db)
    new_access = create_access_token(data={"sub": user.email})
    new_refresh = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: schemas.RefreshRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Révoquer l'access token courant et le refresh token fourni
    token_blacklist.revoke(token, db)
    token_blacklist.revoke(body.refresh_token, db)

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


@router.post("/sync-supabase")
async def sync_supabase_user(
    body: schemas.SupabaseSyncRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronise l'utilisateur authentifié via Supabase avec la DB locale.
    Vérifie également la validité de la licence (Kill-Switch).
    """
    if not settings.SUPABASE_URL:
        # En mode dev sans config, on laisse passer si c'est l'admin par défaut
        if body.email == "admin@digitalcrown.com":
             user = db.query(models.User).filter(models.User.email == body.email).first()
             return {"status": "ok", "token": create_access_token(data={"sub": user.email})}
        raise HTTPException(status_code=500, detail="Supabase n'est pas configuré sur le serveur.")

    # 1. Valider le token auprès de Supabase
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {body.access_token}",
                "apikey": settings.SUPABASE_ANON_KEY
            }
            # Appel à l'endpoint /user de Supabase Auth
            response = await client.get(f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Session Cloud invalide ou expirée.")
            
            supabase_user = response.json()
            if supabase_user.get("email") != body.email:
                raise HTTPException(status_code=401, detail="Email mismatch.")
                
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=401, detail=f"Erreur de validation Cloud: {str(e)}")

    # 2. Synchronisation Locale
    user = db.query(models.User).filter(models.User.email == body.email).first()
    
    if not user:
        # Vérifier s'il y a déjà un admin (le propriétaire)
        has_admin = db.query(models.User).filter(models.User.role == models.UserRole.ADMIN).first()
        
        # Création automatique du praticien lors de sa première connexion
        import uuid
        user = models.User(
            email=body.email,
            hashed_password=uuid.uuid4().hex,
            role=models.UserRole.ADMIN if not has_admin else models.UserRole.DENTISTE,
            nom_complet=body.email.split('@')[0].capitalize(),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)


    # 3. LE KILL-SWITCH (Brainstorming : Période d'essai)
    # On récupère les métadonnées de l'utilisateur Supabase (ou une table dédiée)
    user_metadata = supabase_user.get("user_metadata", {})
    trial_end_str = user_metadata.get("trial_end") # Format YYYY-MM-DD
    
    if trial_end_str:
        from datetime import datetime
        try:
            trial_end = datetime.strptime(trial_end_str, "%Y-%m-%d")
            if datetime.now() > trial_end:
                audit_service.log(
                    db=db, user_id=user.id, action="TRIAL_EXPIRED",
                    resource_type="User", resource_id=user.email, severity="CRITICAL",
                    details=f"Tentative d'accès après expiration ({trial_end_str})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Votre période d'essai a expiré. Contactez le support pour activer votre licence."
                )
        except ValueError:
            pass

    # 4. Générer un token local pour les requêtes suivantes
    local_token = create_access_token(data={"sub": user.email})
    
    return {
        "status": "synchronized",
        "user_id": user.id,
        "role": user.role,
        "token": local_token
    }
