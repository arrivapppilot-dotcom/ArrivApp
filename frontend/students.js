// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://arrivapp-backend.onrender.com';

let allStudents = [];
let filteredStudents = [];
let allSchools = [];
let currentEditingStudentId = null;

document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadSchools();
    await loadStudents();
    setupFilters();
});

async function checkAuth() {
    const token = localStorage.getItem('arrivapp_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) {
            localStorage.removeItem('arrivapp_token');
            window.location.href = 'login.html';
            return;
        }
        const user = await response.json();
        if (user.role !== 'admin' && user.role !== 'director') {
            alert('No tienes permisos para acceder a esta página');
            window.location.href = 'dashboard.html';
            return;
        }
        document.getElementById('userInfo').textContent = `${user.name || user.nombre || user.username} (${user.role})`;
    } catch (error) {
        console.error('Error checking authentication:', error);
        localStorage.removeItem('arrivapp_token');
        window.location.href = 'login.html';
    }
}

function logout() {
    localStorage.removeItem('arrivapp_token');
    window.location.href = 'login.html';
}

async function loadSchools() {
    const token = localStorage.getItem('arrivapp_token');
    try {
        const response = await fetch(`${API_BASE_URL}/api/schools/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load schools');
        allSchools = await response.json();
        
        // Populate school filters
        const schoolFilter = document.getElementById('schoolFilter');
        const studentSchool = document.getElementById('studentSchool');
        
        allSchools.forEach(school => {
            const option = new Option(school.name, school.id);
            schoolFilter.add(option.cloneNode(true));
            studentSchool.add(option);
        });
    } catch (error) {
        console.error('Error loading schools:', error);
        alert('Error al cargar los colegios');
    }
}

async function loadStudents() {
    const token = localStorage.getItem('arrivapp_token');
    try {
        const response = await fetch(`${API_BASE_URL}/api/students/?limit=10000`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load students');
        allStudents = await response.json();
        filteredStudents = [...allStudents];
        
        // Extract unique classes for filter
        const classes = [...new Set(allStudents.map(s => s.class_name).filter(Boolean))].sort();
        const classFilter = document.getElementById('classFilter');
        classes.forEach(clase => {
            classFilter.add(new Option(clase, clase));
        });
        
        renderTable();
        updateStats();
    } catch (error) {
        console.error('Error loading students:', error);
        document.getElementById('studentsTableBody').innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-12 text-center">
                    <p class="text-red-500 text-lg font-medium">Error al cargar los estudiantes</p>
                    <button onclick="loadStudents()" class="mt-4 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg">
                        Reintentar
                    </button>
                </td>
            </tr>
        `;
    }
}

function setupFilters() {
    document.getElementById('searchInput').addEventListener('input', applyFilters);
    document.getElementById('schoolFilter').addEventListener('change', applyFilters);
    document.getElementById('classFilter').addEventListener('change', applyFilters);
    document.getElementById('statusFilter').addEventListener('change', applyFilters);
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const schoolId = document.getElementById('schoolFilter').value;
    const clase = document.getElementById('classFilter').value;
    const status = document.getElementById('statusFilter').value;
    
    filteredStudents = allStudents.filter(student => {
        const studentName = student.name || '';
        const studentEmail = student.parent_email || '';
        const studentId = student.student_id || '';
        
        const matchesSearch = !searchTerm || 
            studentName.toLowerCase().includes(searchTerm) ||
            studentId.toLowerCase().includes(searchTerm) ||
            studentEmail.toLowerCase().includes(searchTerm);
        
        const matchesSchool = !schoolId || student.school_id == schoolId;
        const matchesClass = !clase || student.class_name === clase;
        const matchesStatus = !status || student.is_active.toString() === status;
        
        return matchesSearch && matchesSchool && matchesClass && matchesStatus;
    });
    
    renderTable();
    updateStats();
}

function renderTable() {
    const tbody = document.getElementById('studentsTableBody');
    
    if (filteredStudents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-12 text-center">
                    <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
                    </svg>
                    <p class="text-gray-500 text-lg font-medium">No se encontraron estudiantes</p>
                    <p class="text-gray-400 text-sm mt-2">Intenta ajustar los filtros o añade nuevos alumnos</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredStudents.map(student => {
        const school = allSchools.find(s => s.id === student.school_id);
        const statusClass = student.is_active ? 'status-active' : 'status-inactive';
        const statusText = student.is_active ? 'Activo' : 'Inactivo';
        const studentName = student.name || 'Sin nombre';
        const studentInitial = studentName.charAt(0).toUpperCase();
        
        return `
            <tr class="hover:bg-indigo-50 cursor-pointer transition-colors" onclick="viewStudentDetail(${student.id})">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-full flex items-center justify-center border-2 border-indigo-200">
                            <span class="text-indigo-700 font-bold">${studentInitial}</span>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-semibold text-gray-900">${studentName}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${student.student_id}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${school ? school.name : 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${student.class_name || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${student.parent_email || 'N/A'}</div>
                    <div class="text-sm text-gray-500">${student.parent_phone || ''}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <button onclick="event.stopPropagation(); viewStudentDetail(${student.id})" 
                        class="text-indigo-600 hover:text-indigo-900 font-semibold mr-3">
                        Ver
                    </button>
                    <button onclick="event.stopPropagation(); editStudentDirect(${student.id})" 
                        class="text-violet-600 hover:text-violet-900 font-semibold mr-3">
                        Editar
                    </button>
                    <button onclick="event.stopPropagation(); downloadStudentQR(${student.id})" 
                        class="text-emerald-600 hover:text-emerald-900 font-semibold" title="Descargar QR">
                        QR
                    </button>
                </td>
                </td>
            </tr>
        `;
    }).join('');
}

function updateStats() {
    document.getElementById('totalCount').textContent = filteredStudents.length;
}

function viewStudentDetail(studentId) {
    const student = allStudents.find(s => s.id === studentId);
    if (!student) return;
    
    const school = allSchools.find(s => s.id === student.school_id);
    const statusClass = student.is_active ? 'text-green-600' : 'text-red-600';
    const statusText = student.is_active ? 'Activo' : 'Inactivo';
    const studentName = student.name || 'Sin nombre';
    const studentInitial = studentName.charAt(0).toUpperCase();
    
    document.getElementById('studentDetailContent').innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center space-x-4 pb-4 border-b-2 border-gray-200">
                <div class="flex-shrink-0 h-20 w-20 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-full flex items-center justify-center border-4 border-indigo-200 shadow-lg">
                    <span class="text-indigo-700 font-bold text-3xl">${studentInitial}</span>
                </div>
                <div>
                    <h4 class="text-xl font-bold text-gray-900">${studentName}</h4>
                    <p class="text-gray-600">${student.student_id}</p>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Colegio</p>
                    <p class="text-sm text-gray-900">${school ? school.name : 'N/A'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Clase</p>
                    <p class="text-sm text-gray-900">${student.class_name || 'N/A'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Email</p>
                    <p class="text-sm text-gray-900">${student.parent_email || 'N/A'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Teléfono</p>
                    <p class="text-sm text-gray-900">${student.parent_phone || 'N/A'}</p>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-500">Estado</p>
                    <p class="text-sm font-semibold ${statusClass}">${statusText}</p>
                </div>
            </div>
        </div>
    `;
    
    currentEditingStudentId = studentId;
    document.getElementById('studentDetailModal').classList.add('active');
}

function closeStudentDetailModal() {
    document.getElementById('studentDetailModal').classList.remove('active');
    currentEditingStudentId = null;
}

function editStudent() {
    closeStudentDetailModal();
    editStudentDirect(currentEditingStudentId);
}

function editStudentDirect(studentId) {
    const student = allStudents.find(s => s.id === studentId);
    if (!student) return;
    
    document.getElementById('addStudentTitle').textContent = 'Editar Alumno';
    document.getElementById('studentId').value = student.id;
    document.getElementById('studentName').value = student.name || '';
    document.getElementById('studentStudentId').value = student.student_id;
    document.getElementById('studentEmail').value = student.parent_email || '';
    document.getElementById('studentPhone').value = student.parent_phone || '';
    document.getElementById('studentClass').value = student.class_name || '';
    document.getElementById('studentSchool').value = student.school_id;
    document.getElementById('studentActive').checked = student.is_active;
    
    currentEditingStudentId = studentId;
    document.getElementById('addStudentModal').classList.add('active');
}

function openAddStudentModal() {
    document.getElementById('addStudentTitle').textContent = 'Añadir Alumno';
    document.getElementById('studentForm').reset();
    document.getElementById('studentId').value = '';
    document.getElementById('studentActive').checked = true;
    currentEditingStudentId = null;
    document.getElementById('addStudentModal').classList.add('active');
}

function closeAddStudentModal() {
    document.getElementById('addStudentModal').classList.remove('active');
    document.getElementById('studentForm').reset();
    currentEditingStudentId = null;
}

document.getElementById('studentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveStudent();
});

async function saveStudent() {
    const token = localStorage.getItem('arrivapp_token');
    const studentId = document.getElementById('studentId').value;
    
    const data = {
        name: document.getElementById('studentName').value,
        student_id: document.getElementById('studentStudentId').value,
        parent_email: document.getElementById('studentEmail').value || null,
        parent_phone: document.getElementById('studentPhone').value || null,
        class_name: document.getElementById('studentClass').value,
        school_id: parseInt(document.getElementById('studentSchool').value),
        is_active: document.getElementById('studentActive').checked
    };
    
    try {
        const url = studentId ? `${API_BASE_URL}/api/students/${studentId}` : `${API_BASE_URL}/api/students/`;
        const method = studentId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar el alumno');
        }
        
        alert(studentId ? 'Alumno actualizado correctamente' : 'Alumno añadido correctamente');
        closeAddStudentModal();
        await loadStudents();
    } catch (error) {
        console.error('Error saving student:', error);
        alert('Error: ' + error.message);
    }
}

function openBulkUploadModal() {
    document.getElementById('bulkUploadModal').classList.add('active');
}

function closeBulkUploadModal() {
    document.getElementById('bulkUploadModal').classList.remove('active');
    document.getElementById('bulkFile').value = '';
    document.getElementById('uploadProgress').classList.add('hidden');
}

async function uploadBulkFile() {
    const fileInput = document.getElementById('bulkFile');
    if (!fileInput.files.length) {
        alert('Por favor selecciona un archivo');
        return;
    }
    
    const token = localStorage.getItem('arrivapp_token');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        document.getElementById('uploadProgress').classList.remove('hidden');
        document.getElementById('uploadProgressBar').style.width = '50%';
        document.getElementById('uploadStatus').textContent = 'Subiendo archivo...';
        
        const response = await fetch(`${API_BASE_URL}/api/students/bulk-upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al subir el archivo');
        }
        
        const result = await response.json();
        document.getElementById('uploadProgressBar').style.width = '100%';
        document.getElementById('uploadStatus').textContent = `¡Completado! ${result.created || 0} alumnos añadidos`;
        
        setTimeout(() => {
            closeBulkUploadModal();
            loadStudents();
        }, 2000);
    } catch (error) {
        console.error('Error uploading file:', error);
        document.getElementById('uploadStatus').textContent = 'Error: ' + error.message;
        document.getElementById('uploadProgressBar').style.width = '0%';
    }
}

async function exportStudents() {
    const csv = [
        ['Nombre', 'ID Estudiante', 'Email', 'Teléfono', 'Clase', 'Colegio', 'Estado'],
        ...filteredStudents.map(s => {
            const school = allSchools.find(sc => sc.id === s.school_id);
            return [
                s.name || '',
                s.student_id,
                s.parent_email || '',
                s.parent_phone || '',
                s.class_name || '',
                school ? school.name : '',
                s.is_active ? 'Activo' : 'Inactivo'
            ];
        })
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `alumnos_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
}

// QR Code Download Functions
async function downloadQRCode() {
    if (!currentEditingStudentId) return;
    await downloadStudentQR(currentEditingStudentId);
}

async function downloadStudentQR(studentId) {
    const student = allStudents.find(s => s.id === studentId);
    if (!student) {
        alert('Estudiante no encontrado');
        return;
    }
    
    const token = localStorage.getItem('arrivapp_token');
    try {
        const response = await fetch(`${API_BASE_URL}/api/students/${studentId}/qr`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Error al descargar el código QR');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `QR_${student.student_id}_${student.name || 'student'}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading QR code:', error);
        alert('Error al descargar el código QR: ' + error.message);
    }
}
