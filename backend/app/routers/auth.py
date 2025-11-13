from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.models import User, UserRole
from app.models.schemas import Token, LoginRequest, UserCreate, User as UserSchema
from app.core.config import get_settings
from app.core.deps import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    # Manually construct the response to avoid ORM serialization issues
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "school_id": current_user.school_id,
        "created_at": current_user.created_at
    }


@router.post("/register", response_model=UserSchema)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Register a new user (admin only)."""
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should delete token)."""
    return {"message": "Successfully logged out"}


@router.get("/init-admin")
@router.post("/init-admin")
async def init_admin(db: Session = Depends(get_db)):
    """Initialize admin user if it doesn't exist (public endpoint for first-time setup)."""
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        return {"message": "Admin user already exists", "status": "exists"}
    
    # Create admin user
    try:
        # Use bcrypt directly to avoid passlib backend issues
        import bcrypt as bcrypt_lib
        
        password = "admin123"
        salt = bcrypt_lib.gensalt()
        hashed_pw = bcrypt_lib.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        admin = User(
            username="admin",
            email="admin@arrivapp.com",
            hashed_password=hashed_pw,
            full_name="Administrator",
            role=UserRole.admin,
            is_admin=True,
            is_active=True
        )
        db.add(admin)
        db.commit()
        return {
            "message": "Admin user created successfully", 
            "status": "created", 
            "username": "admin",
            "password": "admin123",
            "note": "Please login with these credentials"
        }
    except Exception as e:
        db.rollback()
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "failed"
        }
