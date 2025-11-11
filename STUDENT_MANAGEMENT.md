# 🎓 Student Management Guide

## Overview
The dashboard now includes a comprehensive student management system with three methods to add students:

### 1. ➕ Manual Entry (Single Student)
**Perfect for**: Adding one student at a time

**Steps**:
1. Login to dashboard at http://localhost:8080/dashboard.html
2. Click **"➕ Gestionar Alumnos"** button (top right)
3. The "Añadir Manualmente" tab opens by default
4. Fill in the form:
   - **Student ID**: Unique identifier (e.g., 001, S001)
   - **Full Name**: Student's complete name
   - **Class**: Grade/class (e.g., 5A, 3B)
   - **Parent Email**: For late arrival notifications
5. Click **"✅ Añadir Alumno"**
6. QR code is automatically generated

**Result**: Instant student creation with QR code ready to download

---

### 2. 📤 Excel Bulk Upload
**Perfect for**: Adding many students at once (start of year, new class)

**Steps**:
1. Click **"➕ Gestionar Alumnos"** → **"Subir Excel"** tab
2. Download the template:
   - Click **"📥 Descargar plantilla Excel"**
   - Opens CSV file with correct format
3. Fill the template with your students:
   ```csv
   student_id,name,class_name,parent_email
   001,Juan Pérez,5A,juan.padre@email.com
   002,María García,5A,maria.padre@email.com
   ```
4. Save as `.xlsx` or `.csv`
5. Click **"Selecciona un archivo"** or drag & drop
6. Click **"📤 Subir y Procesar Excel"**
7. Wait for processing (shows progress bar)
8. Review results:
   - ✅ Students created
   - ⚠️ Students skipped (duplicates)
   - ❌ Errors (invalid data)

**Result**: Batch creation of all valid students with QR codes

---

### 3. 📋 Student List Management
**Perfect for**: Viewing, downloading QR codes, managing existing students

**Features**:
- View all registered students
- Download individual QR codes
- Delete students (soft delete)
- See total student count
- Refresh list

**Steps**:
1. Click **"➕ Gestionar Alumnos"** → **"Lista de Alumnos"** tab
2. Browse student list
3. Actions available:
   - **📥 Descargar**: Download student's QR code as PNG
   - **🗑️ Eliminar**: Remove student (requires confirmation)
4. Click **🔄 Actualizar** to refresh list

---

## File Format Requirements

### Excel/CSV Format
Must include these 4 columns (exact names):

| Column | Description | Example |
|--------|-------------|---------|
| `student_id` | Unique identifier | 001, S001, 2024001 |
| `name` | Full student name | Juan Pérez López |
| `class_name` | Grade/class code | 5A, 3B, Infantil |
| `parent_email` | Guardian email | padre@email.com |

**Notes**:
- Headers must match exactly (case-sensitive)
- Student IDs must be unique
- All fields are required
- Duplicate student IDs will be skipped
- Invalid emails will cause errors

---

## QR Code Management

### Auto-Generation
- QR codes are created automatically when adding students
- Stored in `backend/qr_codes/` directory
- Filename format: `student_XXX.png`
- Contains student ID for check-in scanning

### Downloading QR Codes

**Method 1: Individual Download**
- Go to **"Lista de Alumnos"** tab
- Click **"📥 Descargar"** next to student name
- PNG file downloads automatically

**Method 2: Direct URL Access**
```
http://localhost:8000/qr_codes/student_001.png
```

**Method 3: API Endpoint**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/students/1/qr
```

---

## Common Workflows

### Start of School Year
1. Prepare Excel file with all new students
2. Use **"Subir Excel"** to bulk upload
3. Download all QR codes from **"Lista de Alumnos"**
4. Print and distribute to students
5. Set up check-in kiosk

### Adding Mid-Year Transfer Student
1. Use **"Añadir Manualmente"**
2. Fill student details
3. Download QR immediately
4. Print and give to student

### Removing Graduated Students
1. Go to **"Lista de Alumnos"**
2. Click **🗑️ Eliminar** for each graduated student
3. Confirm deletion
4. Students are soft-deleted (data preserved)

---

## Troubleshooting

### "Student ID already exists"
**Cause**: Trying to add student with duplicate ID
**Solution**: Check **"Lista de Alumnos"** for existing student or use different ID

### Excel upload fails
**Causes**:
- Wrong file format (use .xlsx or .csv)
- Missing required columns
- Empty cells in required fields
- Invalid email format

**Solution**: Download template and follow format exactly

### QR code not generating
**Cause**: Backend service issue
**Solution**: 
1. Check backend logs
2. Verify `qr_codes/` directory exists
3. Ensure pillow library installed

### Can't delete student
**Cause**: Not logged in as admin
**Solution**: Login with admin account (default: admin/admin123)

---

## API Endpoints (for developers)

### Create Student
```http
POST /api/students/
Authorization: Bearer {token}
Content-Type: application/json

{
  "student_id": "001",
  "name": "Juan Pérez",
  "class_name": "5A",
  "parent_email": "padre@email.com"
}
```

### Upload Excel
```http
POST /api/students/upload-excel
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [Excel file]
```

### Get All Students
```http
GET /api/students/
Authorization: Bearer {token}
```

### Delete Student
```http
DELETE /api/students/{id}
Authorization: Bearer {token}
```

---

## Security Notes

- Only **admin users** can add/delete students
- Regular users can only view students
- JWT token required for all operations
- Student deletion is **soft delete** (data preserved)
- Parent emails are **not validated** for sending (configure SMTP in production)

---

## Next Steps

1. **Test Manual Entry**: Add a test student and scan their QR
2. **Test Excel Upload**: Use `sample_students.csv` provided
3. **Print QR Codes**: Download and print for distribution
4. **Set Up Kiosk**: Open check-in page on tablet/monitor
5. **Test Full Flow**: Scan QR → Check dashboard for arrival

---

For more help, see:
- [QUICKSTART.md](./QUICKSTART.md) - Initial setup
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
