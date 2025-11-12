from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.database import engine, Base
from app.routers import auth, students, checkin, schools, users, reports, justifications
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    # Disabled scheduler for deployment without SMTP configuration
    # start_scheduler()
    yield
    # Shutdown
    # stop_scheduler()
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

# CORS middleware - Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://arrivapp-frontend.onrender.com"],  # Only allow deployed frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(checkin.router)
app.include_router(reports.router)
app.include_router(justifications.router)

# Mount static files for QR codes
app.mount("/qr_codes", StaticFiles(directory="qr_codes"), name="qr_codes")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
