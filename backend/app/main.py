from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from contextlib import asynccontextmanager
import os
import traceback
from pathlib import Path
from app.core.config import get_settings
from app.core.database import engine, Base, SessionLocal

# Version: 2.0.1 - UTC timezone fix for reports endpoint
from app.routers import auth, students, checkin, schools, users, reports, justifications, comedor, admin_tools
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)


def init_admin_user():
    """Create default admin user if it doesn't exist."""
    try:
        from app.models.models import User, UserRole
        from app.core.security import get_password_hash
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            # Check if admin exists using raw SQL to avoid any model issues
            result = db.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).scalar()
            
            if result == 0:
                # Create new admin user
                hashed_pw = get_password_hash("madrid123")
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
                print("✅ Default admin user created (username: admin, password: madrid123)")
            else:
                print("✅ Admin user already exists")
        except Exception as e:
            print(f"⚠️ Error initializing admin user: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Could not initialize admin user: {e}")
        # Don't crash the app if admin creation fails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    init_admin_user()
    # Start scheduler for automated email notifications
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    pass


# API Metadata
description = """
## ArrivApp - Sistema de Control de Asistencia Escolar 🎓

Sistema completo de gestión de asistencia escolar con códigos QR, diseñado para múltiples colegios.

### Características Principales

* **Multi-Colegio**: Gestión de múltiples instituciones educativas
* **Check-in/Check-out con QR**: Registro rápido mediante escaneo de códigos QR
* **Notificaciones Email**: Alertas automáticas para ausencias, retrasos y salidas anticipadas
* **Justificaciones**: Sistema de notificación de ausencias por parte de padres
* **Reportes**: Generación de reportes detallados de asistencia
* **Roles de Usuario**: Admin, Director y Profesor con permisos específicos
* **Dashboard en Tiempo Real**: Visualización instantánea del estado de asistencia
* **Filtros por Clase**: Visualización específica por clase o grupo

### Seguridad

* Autenticación JWT
* Control de acceso basado en roles
* Protección contra escaneos duplicados
* Validación de tiempo mínimo de permanencia
* Alertas de salida anticipada

### Autores
Desarrollado para facilitar la gestión de asistencia escolar de forma moderna y eficiente.
"""

tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operaciones de autenticación y gestión de sesiones. Incluye login, logout y verificación de usuario actual.",
    },
    {
        "name": "Users",
        "description": "Gestión de usuarios del sistema (Admins, Directores, Profesores). Solo administradores pueden crear y modificar usuarios.",
    },
    {
        "name": "Schools",
        "description": "Gestión de colegios/escuelas. Incluye creación, edición, listado y gestión de estudiantes por colegio.",
    },
    {
        "name": "Students",
        "description": "Gestión de estudiantes. Incluye registro, edición, generación de códigos QR y carga masiva mediante CSV.",
    },
    {
        "name": "Check-in",
        "description": "Sistema de registro de entrada/salida mediante códigos QR. Incluye dashboard de asistencia, detección de retrasos y salidas anticipadas.",
    },
    {
        "name": "Reports",
        "description": "Generación de reportes de asistencia. Exportación en CSV y estadísticas detalladas por fecha, colegio y clase.",
    },
    {
        "name": "Justifications",
        "description": "Sistema de justificación de ausencias. Permite a los padres notificar ausencias mediante formulario público validado por email.",
    },
]

# Create FastAPI app
app = FastAPI(
    title="ArrivApp API",
    version=settings.APP_VERSION,
    description=description,
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "ArrivApp Support",
        "email": "support@arrivapp.com",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware - MUST be added AFTER app creation but BEFORE routers are included
# Note: add_middleware executes in LIFO (reverse) order, so this is added last but runs first
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "https://arrivapp-frontend.onrender.com",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
    allow_headers=["Content-Type", "Authorization", "*"],
    expose_headers=["Content-Type", "Authorization", "*"],
    max_age=3600,
)


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(checkin.router)
app.include_router(reports.router)
app.include_router(justifications.router)
app.include_router(comedor.router)
app.include_router(admin_tools.router)


# Exception handlers to ensure CORS headers are always sent
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers are included."""
    print(f"Exception occurred: {str(exc)}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "https://arrivapp-frontend.onrender.com",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler that ensures CORS headers are included."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "https://arrivapp-frontend.onrender.com",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )# Create qr_codes directory if it doesn't exist
qr_codes_dir = Path("qr_codes")
qr_codes_dir.mkdir(exist_ok=True)

# Mount static files for QR codes
app.mount("/qr_codes", StaticFiles(directory="qr_codes"), name="qr_codes")

# Determine frontend directory
backend_dir = Path(__file__).parent.parent.parent  # Go from main.py -> app -> backend -> project root
frontend_dir = backend_dir / "frontend"

print(f"Backend location: {Path(__file__).parent.parent}")
print(f"Frontend path: {frontend_dir}")
print(f"Frontend exists: {frontend_dir.exists()}")


@app.get("/", tags=["Root"])
async def root():
    """
    # Endpoint Principal
    
    Retorna información básica sobre la API, incluyendo versión y enlaces a la documentación.
    
    **Información retornada:**
    - Nombre y versión de la aplicación
    - Link a la documentación interactiva
    - Estado del servicio
    """
    return {
        "message": "ArrivApp API - Sistema Multi-Colegio",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
        "features": [
            "Multi-School Management",
            "QR Code Check-in/Check-out",
            "Email Notifications",
            "Absence Justifications",
            "Real-time Dashboard",
            "Attendance Reports"
        ]
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """
    # Health Check
    
    Verifica que el servicio esté funcionando correctamente.
    
    Útil para monitoreo y balanceadores de carga.
    """
    return {
        "status": "healthy",
        "service": "ArrivApp API",
        "version": settings.APP_VERSION
    }


# Serve HTML files - catch-all for frontend
@app.get("/{path:path}", tags=["Frontend"])
async def serve_html(path: str):
    """Serve HTML files from frontend directory with cache-busting headers"""
    # Prevent serving API paths
    if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    # Try to serve the exact file if it exists (for any file type)
    file_path = frontend_dir / path
    
    # Ensure path doesn't escape frontend directory
    try:
        file_path.resolve().relative_to(frontend_dir.resolve())
    except ValueError:
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    if file_path.exists() and file_path.is_file():
        try:
            # Add cache-busting headers to prevent stale CSS/JS
            headers = {
                "Cache-Control": "public, max-age=3600",
                "ETag": str(file_path.stat().st_mtime)
            }
            
            # For text files (HTML, CSS, JS)
            if path.endswith(('.html', '.css', '.js', '.json')):
                with open(file_path, "r", encoding="utf-8") as f:
                    if path.endswith('.html'):
                        return HTMLResponse(f.read(), headers=headers)
                    elif path.endswith('.css'):
                        return FileResponse(file_path, media_type="text/css", headers=headers)
                    elif path.endswith('.js'):
                        return FileResponse(file_path, media_type="application/javascript", headers=headers)
                    else:
                        return FileResponse(file_path, headers=headers)
            # For binary files (images, etc.)
            else:
                return FileResponse(file_path, headers=headers)
        except Exception as e:
            print(f"Error serving {path}: {e}")
            return JSONResponse({"detail": "Error reading file"}, status_code=500)
    
    # For non-existent static files, return 404
    if path.endswith(('.css', '.js', '.jpg', '.png', '.gif', '.ico', '.svg', '.pdf', '.woff', '.woff2')):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    # For HTML files, return 404 if not found
    if path.endswith('.html'):
        print(f"HTML file not found: {file_path}")
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    # Try index.html as fallback only for non-file paths (SPA routing)
    index_path = frontend_dir / "index.html"
    if index_path.exists() and index_path.is_file():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                headers = {"Cache-Control": "public, max-age=3600"}
                return HTMLResponse(f.read(), headers=headers)
        except Exception as e:
            print(f"Error serving index.html: {e}")
    
    return JSONResponse({"detail": "Not Found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
