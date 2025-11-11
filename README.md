# ArrivApp v2.0 - Sistema de Asistencia Escolar

Sistema completo de control de asistencia escolar con check-in por QR, notificaciones automáticas y dashboard en tiempo real.

## 🚀 Características

- ✅ **Check-in por QR**: Escaneo rápido y sin contacto
- 📧 **Notificaciones automáticas**: Email instantáneo a padres
- 📊 **Dashboard en tiempo real**: Visualización de asistencia
- 🔐 **Sistema de autenticación**: Login seguro con JWT
- 👥 **Gestión de estudiantes**: CRUD completo
- 📱 **Responsive**: Funciona en móvil, tablet y desktop
- 🐳 **Docker ready**: Despliegue fácil con Docker Compose

## 🏗️ Arquitectura

```
ArrivApp/
├── backend/              # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── core/        # Config, DB, Security
│   │   ├── models/      # SQLAlchemy models & Pydantic schemas
│   │   ├── routers/     # API endpoints
│   │   └── services/    # QR, Email services
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/             # HTML + Vanilla JS
│   ├── login.html
│   ├── dashboard.html
│   ├── dashboard.js
│   └── checkin.html
└── qr_codes/            # Generated QR codes
```

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 15+ (o SQLite para desarrollo)
- Node.js 18+ (opcional, para frontend server)
- Docker & Docker Compose (opcional)

## 🔧 Instalación

### Opción 1: Con Docker (Recomendado)

1. **Clonar y configurar**:
```bash
cd backend
cp .env.example .env
# Edita .env con tus configuraciones
```

2. **Iniciar servicios**:
```bash
docker-compose up -d
```

3. **Inicializar base de datos**:
```bash
docker-compose exec backend python -m app.init_db
```

4. **Acceder**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: Abre `frontend/login.html` en un navegador

### Opción 2: Instalación Manual

1. **Backend Setup**:
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus configuraciones

# Para desarrollo con SQLite, usa:
# DATABASE_URL=sqlite:///./arrivapp.db

# Inicializar base de datos
python -m app.init_db

# Iniciar servidor
uvicorn app.main:app --reload
```

2. **Frontend Setup**:
```bash
cd frontend

# Opción A: Servidor Python simple
python -m http.server 8080

# Opción B: Servidor Node.js
npx http-server -p 8080
```

3. **Acceder**:
- Backend: http://localhost:8000
- Frontend: http://localhost:8080

## 🔐 Configuración de Email

Edita el archivo `.env` con tus credenciales SMTP:

### Gmail:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password  # Ver: https://myaccount.google.com/apppasswords
FROM_EMAIL=arrivapp@tudominio.com
FROM_NAME=ArrivApp
ADMIN_EMAIL=admin@tudominio.com
```

### SendGrid:
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=tu-sendgrid-api-key
FROM_EMAIL=arrivapp@tudominio.com
FROM_NAME=ArrivApp
ADMIN_EMAIL=admin@tudominio.com
```

## 👤 Usuario Inicial

Después de ejecutar `init_db.py`:

- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **IMPORTANTE**: Cambia esta contraseña inmediatamente en producción.

## 📱 Uso del Sistema

### 1. Login
1. Abre `http://localhost:8080/login.html`
2. Ingresa: `admin` / `admin123`
3. Serás redirigido al dashboard

### 2. Gestionar Estudiantes

Usa la API o crea un admin panel. Ejemplo con curl:

```bash
# Login y obtener token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Crear estudiante
curl -X POST "http://localhost:8000/api/students/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "EST001",
    "name": "Juan Pérez",
    "class_name": "3ro A",
    "parent_email": "padre@email.com"
  }'
```

### 3. Generar QR Codes

Los QR se generan automáticamente al crear estudiantes. Descárgalos desde:
```
http://localhost:8000/api/students/{id}/qr
```

### 4. Estación de Check-in

1. Abre `http://localhost:8080/checkin.html` en tablet/móvil
2. Permite acceso a la cámara
3. Estudiantes escanean su QR
4. ¡Listo! Email enviado automáticamente

### 5. Dashboard

Dashboard actualizado automáticamente cada 30 segundos:
- Ver presentes, ausentes, tardíos
- Filtrar por fecha
- Buscar estudiantes
- Exportar a CSV

## 🔌 API Endpoints

### Auth
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Usuario actual
- `POST /api/auth/logout` - Logout

### Students
- `GET /api/students/` - Listar estudiantes
- `POST /api/students/` - Crear estudiante (admin)
- `GET /api/students/{id}` - Obtener estudiante
- `PUT /api/students/{id}` - Actualizar estudiante (admin)
- `DELETE /api/students/{id}` - Eliminar estudiante (admin)
- `GET /api/students/{id}/qr` - Descargar QR

### Check-in
- `POST /api/checkin/scan?student_id={id}` - Check-in (sin auth)
- `GET /api/checkin/dashboard?date_filter={YYYY-MM-DD}` - Datos dashboard
- `GET /api/checkin/` - Listar check-ins

Documentación interactiva: http://localhost:8000/docs

## 📧 Sistema de Notificaciones

### Email a Padres (Inmediato)
Cuando un estudiante hace check-in:
```
Asunto: ArrivApp: Juan Pérez ha llegado al cole

¡Hola!

Buenas noticias.

Juan Pérez (3ro A) ha registrado su entrada 
en el colegio a las 08:45h.

Gracias por participar en el programa piloto de ArrivApp.
```

### Reporte de Ausentes (9:10 AM)
Email diario al administrador con lista de ausentes.

## 🚀 Despliegue en Producción

### Railway (Recomendado)

1. **Crear proyecto en Railway**:
   - Conecta tu repositorio
   - Railway detectará automáticamente el Dockerfile

2. **Agregar PostgreSQL**:
   - Añade servicio PostgreSQL
   - Railway configura DATABASE_URL automáticamente

3. **Configurar variables de entorno**:
   Añade todas las variables del `.env`:
   - SECRET_KEY (genera uno nuevo)
   - SMTP_* (config email)
   - ADMIN_EMAIL
   - FRONTEND_URL (tu dominio)

4. **Deploy**:
   - Push a main branch
   - Railway deploya automáticamente

### Render / Fly.io

Similar a Railway. Sigue su documentación específica.

### VPS (DigitalOcean, Linode, etc.)

```bash
# En el servidor
git clone tu-repo
cd ArrivApp/backend

# Configurar .env con valores de producción
cp .env.example .env
nano .env

# Iniciar con Docker Compose
docker-compose -f docker-compose.yml up -d

# O con systemd
sudo systemctl enable arrivapp
sudo systemctl start arrivapp
```

## 🔒 Seguridad

- ✅ JWT para autenticación
- ✅ Passwords hasheados con bcrypt
- ✅ CORS configurado
- ✅ HTTPS recomendado en producción
- ✅ Rate limiting (TODO)
- ✅ Input validation con Pydantic

## 🧪 Testing

```bash
cd backend
pytest
```

## 📊 Monitoreo

- Logs: `docker-compose logs -f backend`
- Health check: `http://localhost:8000/health`
- Métricas: Integrar Prometheus/Grafana (TODO)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📝 Roadmap

- [ ] Admin panel UI completo
- [ ] Check-out tracking
- [ ] Reports y analytics avanzados
- [ ] Mobile app (React Native)
- [ ] Multi-school support
- [ ] WhatsApp notifications
- [ ] Face recognition check-in
- [ ] Parent portal

## 🐛 Troubleshooting

### Error: Cannot connect to database
- Verifica que PostgreSQL esté corriendo
- Revisa DATABASE_URL en .env

### Error: Email not sending
- Verifica credenciales SMTP
- Usa App Password para Gmail
- Revisa firewall/puerto 587

### QR Scanner no funciona
- Permite acceso a cámara en navegador
- Usa HTTPS en producción (requerido para cámara)
- Prueba en diferentes navegadores

### Token expired
- Login de nuevo
- Ajusta ACCESS_TOKEN_EXPIRE_MINUTES en .env

## 📄 Licencia

MIT License - ver LICENSE file

## 👨‍💻 Autor

Desarrollado para el programa piloto ArrivApp Barcelona 2025

## 📞 Soporte

- Email: luca.alice@gmail.com
- Issues: GitHub Issues

---

**¡Gracias por usar ArrivApp!** 🎉
