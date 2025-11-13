// Auto-detect if running on Cloudflare or localhost
const API_BASE_URL = window.location.hostname.includes('trycloudflare.com') 
    ? 'https://enhancement-organizations-herb-patio.trycloudflare.com'
    : 'http://localhost:8088';
let dashboardData = null;
let searchTerm = '';
let currentUser = null;

// Navigation function for reports
function navigateToReports() {
    console.log('Navigating to reports page...');
    setTimeout(() => {
        window.location.href = 'reports.html';
    }, 0);
}

// Authentication check
const token = localStorage.getItem('arrivapp_token');
const userName = localStorage.getItem('arrivapp_user');

if (!token) {
    window.location.href = 'login.html';
}

// Fetch current user info and set up UI
async function initializeUser() {
    try {
        currentUser = await apiRequest('/api/auth/me');
        const usernameEl = document.getElementById('userName');
        const userRoleEl = document.getElementById('userRole');
        const userInitialsEl = document.getElementById('userInitials');
        
        if (usernameEl) usernameEl.textContent = currentUser.username || 'Usuario';
        if (userRoleEl) {
            const roleNames = {
                'admin': 'Administrador',
                'director': 'Director',
                'teacher': 'Profesor'
            };
            userRoleEl.textContent = roleNames[currentUser.role] || currentUser.role;
        }
        if (userInitialsEl) {
            const initials = currentUser.username ? currentUser.username.substring(0, 2).toUpperCase() : 'U';
            userInitialsEl.textContent = initials;
        }
        
        // Show/hide admin navigation items based on role
        if (currentUser.role === 'admin') {
            const navSchools = document.getElementById('navSchools');
            const navUsers = document.getElementById('navUsers');
            if (navSchools) navSchools.classList.remove('hidden');
            if (navUsers) navUsers.classList.remove('hidden');
            
            // Legacy header buttons (if exist)
            const schoolsBtn = document.getElementById('manageSchoolsBtn');
            const usersBtn = document.getElementById('manageUsersBtn');
            if (schoolsBtn) schoolsBtn.classList.remove('hidden');
            if (usersBtn) usersBtn.classList.remove('hidden');
            
            // Show school filter for admin
            const schoolFilterContainer = document.getElementById('school-filter-container');
            if (schoolFilterContainer) {
                schoolFilterContainer.classList.remove('hidden');
                await loadSchools();
            }
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
        const usernameEl = document.getElementById('userName');
        if (usernameEl) usernameEl.textContent = userName || 'Usuario';
    }
}

// API request helper
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        // Unauthorized - redirect to login
        localStorage.removeItem('arrivapp_token');
        localStorage.removeItem('arrivapp_user');
        window.location.href = 'login.html';
        return;
    }
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// Logout function (called from HTML button)
async function logout() {
    try {
        await apiRequest('/api/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        localStorage.removeItem('arrivapp_token');
        localStorage.removeItem('arrivapp_user');
        window.location.href = 'login.html';
    }
}

// Date formatting
function formatDate(date) {
    const d = new Date(date);
    let day = ('0' + d.getDate()).slice(-2);
    let month = ('0' + (d.getMonth() + 1)).slice(-2);
    let year = d.getFullYear();
    return `${year}-${month}-${day}`;
}

function formatDateDisplay(date) {
    const d = new Date(date);
    let day = ('0' + d.getDate()).slice(-2);
    let month = ('0' + (d.getMonth() + 1)).slice(-2);
    let year = d.getFullYear();
    return `${day}/${month}/${year}`;
}

// Fetch dashboard data
let justificationsData = {};
let selectedClass = ''; // Track selected class filter

async function loadSchools() {
    try {
        const schools = await apiRequest('/api/schools/');
        const schoolFilter = document.getElementById('school-filter');
        
        // Clear existing options except "Todos los colegios"
        schoolFilter.innerHTML = '<option value="">Todos los colegios</option>';
        
        // Add schools to dropdown
        schools.forEach(school => {
            const option = document.createElement('option');
            option.value = school.id;
            option.textContent = school.name;
            schoolFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading schools:', error);
    }
}

async function loadClasses() {
    try {
        const classes = await apiRequest('/api/checkin/classes');
        const classFilter = document.getElementById('class-filter');
        
        // Clear existing options except "Todas las clases"
        classFilter.innerHTML = '<option value="">Todas las clases</option>';
        
        // Add classes to dropdown
        classes.forEach(className => {
            const option = document.createElement('option');
            option.value = className;
            option.textContent = className;
            classFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

async function fetchDashboardData() {
    const selectedDate = document.getElementById('date-picker').value;
    const classFilter = document.getElementById('class-filter')?.value || '';
    const schoolFilter = document.getElementById('school-filter')?.value || '';
    
    try {
        let url = `/api/checkin/dashboard?date_filter=${selectedDate}`;
        if (classFilter) {
            url += `&class_filter=${encodeURIComponent(classFilter)}`;
        }
        if (schoolFilter) {
            url += `&school_id=${schoolFilter}`;
        }
        
        dashboardData = await apiRequest(url);
        
        // Fetch justifications for the selected date
        try {
            const justifications = await apiRequest(`/api/justifications/?date=${selectedDate}&status=pending`);
            justificationsData = {};
            justifications.forEach(j => {
                justificationsData[j.student_id] = j;
            });
        } catch (error) {
            console.error('Error fetching justifications:', error);
            justificationsData = {};
        }
        
        renderDashboard();
        
        const now = new Date();
        document.getElementById('lastUpdated').textContent = 
            `Última actualización: ${now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showError('Error al cargar los datos. Reintentando...');
    }
}

// Render dashboard
function renderDashboard() {
    if (!dashboardData) return;
    
    const { stats, checkins, late_students, absent_students } = dashboardData;
    
    // Update main stats cards
    document.getElementById('total-present').textContent = stats.total_present;
    document.getElementById('total-absent').textContent = stats.total_absent;
    document.getElementById('total-late').textContent = stats.total_late;
    
    // Calculate total students
    const totalStudents = stats.total_present + stats.total_absent;
    
    // Calculate attendance rate
    const attendanceRate = totalStudents > 0 
        ? Math.round((stats.total_present / totalStudents) * 100) 
        : 0;
    
    // Calculate on-time students (present students who are not late)
    const onTimeStudents = stats.total_present - stats.total_late;
    const onTimeRate = stats.total_present > 0 
        ? Math.round((onTimeStudents / stats.total_present) * 100)
        : 0;
    
    // Students needing attention (absent without justification)
    const unjustifiedAbsent = absent_students.filter(s => !justificationsData[s.student_id]);
    
    // Count justified absences
    const justifiedCount = Object.keys(justificationsData).length;
    
    // Update insight cards
    document.getElementById('attendance-rate').textContent = attendanceRate + '%';
    document.getElementById('on-time-rate').textContent = onTimeRate + '%';
    document.getElementById('attention-count').textContent = unjustifiedAbsent.length;
    
    // Update behavior metrics cards
    document.getElementById('total-students').textContent = totalStudents;
    document.getElementById('on-time-count').textContent = onTimeStudents;
    document.getElementById('justified-count').textContent = justifiedCount;
    
    // Render justifications widget
    renderJustificationsWidget();
    
    // Filter by search term
    const filteredCheckins = checkins.filter(c => 
        c.student_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    const filteredLate = late_students.filter(s => 
        s.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    const filteredAbsent = absent_students.filter(s => 
        s.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Render check-in table
    const checkinTableBody = document.getElementById('checkin-table');
    checkinTableBody.innerHTML = '';
    
    if (filteredCheckins.length === 0) {
        checkinTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-10 text-gray-500">No hay registros para la fecha o búsqueda seleccionada.</td></tr>';
    } else {
        filteredCheckins.reverse().forEach(checkin => {
            const tr = document.createElement('tr');
            tr.className = 'new-row hover:bg-gray-50';
            const checkoutDisplay = checkin.checkout_time 
                ? `<div class="text-sm font-medium text-green-600">${checkin.checkout_time}</div>`
                : `<div class="text-sm text-gray-400 italic">En el colegio</div>`;
            tr.innerHTML = `
                <td class="px-6 py-4"><div class="text-sm font-medium text-gray-900">${checkin.checkin_time}</div></td>
                <td class="px-6 py-4"><div class="text-sm text-gray-500">${checkin.student_name}</div></td>
                <td class="px-6 py-4"><div class="text-sm text-blue-600">${checkin.school_name}</div></td>
                <td class="px-6 py-4">${checkoutDisplay}</td>
            `;
            checkinTableBody.appendChild(tr);
        });
    }
    const lateTableBody = document.getElementById('late-table');
    lateTableBody.innerHTML = '';
    
    if (filteredLate.length === 0) {
        lateTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-10 text-gray-500">Ningún alumno ha llegado con retraso.</td></tr>';
    } else {
        filteredLate.reverse().forEach(student => {
            const tr = document.createElement('tr');
            tr.className = 'new-row hover:bg-gray-50';
            const emailStatus = student.email_sent 
                ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">✓ Enviado</span>'
                : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">✗ No enviado</span>';
            tr.innerHTML = `
                <td class="px-6 py-4"><div class="text-sm font-medium text-red-500">${student.time}</div></td>
                <td class="px-6 py-4"><div class="text-sm text-gray-500">${student.name}</div></td>
                <td class="px-6 py-4"><div class="text-sm text-blue-600">${student.school_name}</div></td>
                <td class="px-6 py-4">${emailStatus}</td>
            `;
            lateTableBody.appendChild(tr);
        });
    }
    
    // Render absent table
    const absentTableBody = document.getElementById('absent-table');
    absentTableBody.innerHTML = '';
    
    if (filteredAbsent.length === 0) {
        absentTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-10 text-gray-500">¡Todos los alumnos han llegado!</td></tr>';
    } else {
        filteredAbsent.forEach(student => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50';
            
            // Check if student has justification
            const justification = justificationsData[student.id];
            const hasJustification = !!justification;
            
            const emailStatus = student.email_sent 
                ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">✓ Enviado</span>'
                : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Pendiente 9:10</span>';
            
            const justificationBadge = hasJustification
                ? `<span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-amber-100 text-amber-800 ml-2" title="${justification.reason}"> Justificado</span>`
                : '';
            
            tr.innerHTML = `
                <td class="px-6 py-4">
                    <div class="text-sm flex items-center">
                        <a href="#" onclick="showStudentProfile(${student.id}); return false;" class="text-blue-600 hover:text-blue-800 hover:underline font-medium">
                            ${student.name}
                        </a>
                        ${justificationBadge}
                    </div>
                    ${hasJustification ? `<div class="text-xs text-gray-500 mt-1">Motivo: ${justification.reason}</div>` : ''}
                </td>
                <td class="px-6 py-4"><div class="text-sm text-gray-500">${student.class_name}</div></td>
                <td class="px-6 py-4"><div class="text-sm text-blue-600">${student.school_name}</div></td>
                <td class="px-6 py-4">${emailStatus}</td>
            `;
            absentTableBody.appendChild(tr);
        });
    }
}

// Render justifications widget
function renderJustificationsWidget() {
    const widget = document.getElementById('justificationsWidget');
    const listContainer = document.getElementById('justifications-list');
    const countElement = document.getElementById('justifications-count');
    
    const justifications = Object.values(justificationsData);
    
    if (justifications.length === 0) {
        widget.classList.add('hidden');
        return;
    }
    
    widget.classList.remove('hidden');
    countElement.textContent = justifications.length;
    
    listContainer.innerHTML = justifications.map(j => {
        // Use student_name from justification data, fallback to searching absent_students
        let studentName = j.student_name;
        if (!studentName) {
            const student = dashboardData.absent_students.find(s => s.id === j.student_id);
            studentName = student ? student.name : `Alumno #${j.student_id}`;
        }
        
        const typeIcons = {
            'absence': '🏠',
            'tardiness': '',
            'early_dismissal': ''
        };
        
        const typeLabels = {
            'absence': 'Ausencia',
            'tardiness': 'Llegada tarde',
            'early_dismissal': 'Salida anticipada'
        };
        
        return `
            <div class="bg-white rounded-lg p-3 border border-amber-200">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <p class="font-semibold text-gray-800">${studentName}</p>
                        <p class="text-sm text-gray-600 mt-1">
                            ${typeIcons[j.justification_type]} ${typeLabels[j.justification_type]}
                        </p>
                        <p class="text-xs text-gray-500 mt-1">${j.reason}</p>
                        <p class="text-xs text-amber-600 mt-1">Por: ${j.submitted_by}</p>
                    </div>
                    <span class="text-xs px-2 py-1 bg-amber-100 text-amber-800 rounded-full">Pendiente</span>
                </div>
            </div>
        `;
    }).join('');
}

// Export to CSV
function exportToCSV() {
    if (!dashboardData || !dashboardData.checkins.length) {
        alert('No hay datos para exportar');
        return;
    }
    
    const selectedDate = document.getElementById('date-picker').value;
    let csvContent = "data:text/csv;charset=utf-8,Timestamp,StudentName\n";
    
    dashboardData.checkins.forEach(checkin => {
        csvContent += `${checkin.checkin_time},${checkin.student_name}\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `arrivapp_registro_${selectedDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Update clock
function updateClock() {
    const now = new Date();
    const timeEl = document.getElementById('currentTime');
    const dateEl = document.getElementById('currentDate');
    
    if (timeEl) {
        timeEl.textContent = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    if (dateEl) {
        dateEl.textContent = now.toLocaleDateString('es-ES', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }
}

// Show error
function showError(message) {
    console.error(message);
    // You can add a toast notification here
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const datePicker = document.getElementById('date-picker');
    const searchInput = document.getElementById('search-input');
    const classFilter = document.getElementById('class-filter');
    const exportButton = document.getElementById('export-csv');
    const btnToday = document.getElementById('btn-today');
    const btnYesterday = document.getElementById('btn-yesterday');
    
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    datePicker.value = formatDate(today);
    btnToday.classList.add('date-btn-active');
    
    // Load classes dropdown
    loadClasses();
    
    // Initial load
    fetchDashboardData();
    updateClock();
    
    // Auto-refresh every 5 seconds for faster updates
    setInterval(fetchDashboardData, 5000);
    setInterval(updateClock, 1000);
    
    // Check for date change at midnight
    let lastCheckedDate = formatDate(today);
    setInterval(() => {
        const currentDate = formatDate(new Date());
        if (currentDate !== lastCheckedDate) {
            lastCheckedDate = currentDate;
            // If user is viewing "today", update to the new today
            if (datePicker.value === formatDate(yesterday)) {
                datePicker.value = currentDate;
                btnToday.classList.add('date-btn-active');
                btnYesterday.classList.remove('date-btn-active');
                fetchDashboardData();
            }
        }
    }, 60000); // Check every minute
    
    // Date button management
    function updateDateButtons() {
        const selectedDate = datePicker.value;
        if (selectedDate === formatDate(today)) {
            btnToday.classList.add('date-btn-active');
            btnYesterday.classList.remove('date-btn-active');
        } else if (selectedDate === formatDate(yesterday)) {
            btnYesterday.classList.add('date-btn-active');
            btnToday.classList.remove('date-btn-active');
        } else {
            btnToday.classList.remove('date-btn-active');
            btnYesterday.classList.remove('date-btn-active');
        }
    }
    
    // Event listeners
    datePicker.addEventListener('change', () => {
        updateDateButtons();
        fetchDashboardData();
    });
    
    classFilter.addEventListener('change', () => {
        fetchDashboardData();
    });
    
    // School filter event listener (for admin)
    const schoolFilter = document.getElementById('school-filter');
    if (schoolFilter) {
        schoolFilter.addEventListener('change', () => {
            fetchDashboardData();
        });
    }
    
    searchInput.addEventListener('input', (e) => {
        searchTerm = e.target.value;
        renderDashboard();
    });
    
    exportButton.addEventListener('click', exportToCSV);
    
    btnToday.addEventListener('click', () => {
        datePicker.value = formatDate(today);
        updateDateButtons();
        fetchDashboardData();
    });
    
    btnYesterday.addEventListener('click', () => {
        datePicker.value = formatDate(yesterday);
        updateDateButtons();
        fetchDashboardData();
    });
});

// ============================================
// STUDENT MANAGEMENT MODAL
// ============================================

const modal = document.getElementById('studentModal');
const manageStudentsBtn = document.getElementById('manageStudentsBtn');
const closeModal = document.getElementById('closeModal');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Open modal (only if button exists - now redirects to students.html)
if (manageStudentsBtn) {
    manageStudentsBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        loadStudentList();
        loadSchoolsForAdmin(); // Load schools if admin
    });
}

// Close modal (only if exists)
if (closeModal) {
    closeModal.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
}

// Close modal when clicking outside (only if modal exists)
if (modal) {
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
}

// Tab switching
tabButtons.forEach((button, index) => {
    button.addEventListener('click', () => {
        // Remove active class from all tabs
        tabButtons.forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-500');
            btn.classList.add('text-gray-500');
        });
        
        // Hide all tab contents
        tabContents.forEach(content => content.classList.add('hidden'));
        
        // Activate clicked tab
        button.classList.add('border-blue-500', 'text-blue-500');
        button.classList.remove('text-gray-500');
        tabContents[index].classList.remove('hidden');
        
        // Load student list when switching to that tab
        if (button.id === 'tab-list') {
            loadStudentList();
        }
    });
});

// ============================================
// MANUAL STUDENT ENTRY
// ============================================

const addStudentForm = document.getElementById('addStudentForm');
const clearFormBtn = document.getElementById('clearForm');
const addStudentMessage = document.getElementById('addStudentMessage');

// Load schools for admin users
async function loadSchoolsForAdmin() {
    try {
        const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!userResponse.ok) return;
        
        const currentUser = await userResponse.json();
        
        // Show school selector for admins
        if (currentUser.is_admin || currentUser.role === 'admin') {
            const schoolSelectContainer = document.getElementById('schoolSelectContainer');
            const schoolSelect = document.getElementById('student_school_id');
            
            schoolSelectContainer.classList.remove('hidden');
            schoolSelect.required = true;
            
            // Load schools
            const schoolsResponse = await fetch(`${API_BASE_URL}/schools/`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (schoolsResponse.ok) {
                const schools = await schoolsResponse.json();
                schoolSelect.innerHTML = '<option value="">Selecciona un colegio</option>';
                schools.forEach(school => {
                    const option = document.createElement('option');
                    option.value = school.id;
                    option.textContent = school.name;
                    schoolSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading schools:', error);
    }
}

addStudentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get current user info to get school_id
    try {
        const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!userResponse.ok) {
            throw new Error('Failed to get user info');
        }
        
        const currentUser = await userResponse.json();
        
        // Determine school_id
        let schoolId = currentUser.school_id;
        
        // For admins, get school from selector
        if (currentUser.is_admin || currentUser.role === 'admin') {
            const schoolSelect = document.getElementById('student_school_id');
            schoolId = parseInt(schoolSelect.value);
            
            if (!schoolId) {
                showMessage(addStudentMessage, ' Error: Debes seleccionar un colegio', 'error');
                return;
            }
        }
        
        if (!schoolId) {
            showMessage(addStudentMessage, ' Error: Usuario sin colegio asignado. Contacta al administrador.', 'error');
            return;
        }
        
        const studentData = {
            student_id: document.getElementById('student_id').value.trim(),
            name: document.getElementById('student_name').value.trim(),
            class_name: document.getElementById('class_name').value.trim(),
            parent_email: document.getElementById('parent_email').value.trim(),
            school_id: schoolId
        };
        
        const response = await fetch(`${API_BASE_URL}/api/students/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(studentData)
        });
        
        if (response.ok) {
            const student = await response.json();
            showMessage(addStudentMessage, 
                ` Alumno añadido: ${student.name} (ID: ${student.student_id}). QR generado.`, 
                'success');
            addStudentForm.reset();
            
            // Refresh dashboard data
            setTimeout(() => {
                fetchDashboardData();
                addStudentMessage.classList.add('hidden');
            }, 2000);
        } else {
            const error = await response.json();
            let errorMessage = 'No se pudo añadir el alumno';
            
            if (error.detail) {
                if (typeof error.detail === 'string') {
                    errorMessage = error.detail;
                } else if (Array.isArray(error.detail)) {
                    errorMessage = error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                } else {
                    errorMessage = JSON.stringify(error.detail);
                }
            }
            
            showMessage(addStudentMessage, ` Error: ${errorMessage}`, 'error');
        }
    } catch (error) {
        showMessage(addStudentMessage, ` Error de conexión: ${error.message}`, 'error');
    }
});

clearFormBtn.addEventListener('click', () => {
    addStudentForm.reset();
    addStudentMessage.classList.add('hidden');
});

// ============================================
// EXCEL UPLOAD
// ============================================

const excelFileInput = document.getElementById('excelFile');
const excelFileName = document.getElementById('excelFileName');
const uploadExcelBtn = document.getElementById('uploadExcel');
const uploadMessage = document.getElementById('uploadMessage');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const downloadTemplate = document.getElementById('downloadTemplate');

// File selection
excelFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        excelFileName.textContent = ` Archivo seleccionado: ${file.name}`;
        excelFileName.classList.remove('hidden');
        uploadExcelBtn.disabled = false;
    } else {
        excelFileName.classList.add('hidden');
        uploadExcelBtn.disabled = true;
    }
});

// Download template
downloadTemplate.addEventListener('click', (e) => {
    e.preventDefault();
    
    // Create sample Excel data
    const csvContent = "student_id,name,class_name,parent_email\n" +
                      "001,Juan Pérez,5A,juan.padre@email.com\n" +
                      "002,María García,5A,maria.padre@email.com\n" +
                      "003,Pedro López,5B,pedro.padre@email.com";
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'plantilla_alumnos.csv';
    a.click();
    window.URL.revokeObjectURL(url);
});

// Upload Excel
uploadExcelBtn.addEventListener('click', async () => {
    const file = excelFileInput.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadExcelBtn.disabled = true;
    uploadProgress.classList.remove('hidden');
    uploadMessage.classList.add('hidden');
    progressBar.style.width = '30%';
    progressText.textContent = 'Subiendo archivo...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/students/upload-excel`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        progressBar.style.width = '70%';
        progressText.textContent = 'Procesando datos...';
        
        if (response.ok) {
            const result = await response.json();
            progressBar.style.width = '100%';
            progressText.textContent = 'Completado!';
            
            let message = ` Proceso completado:\n`;
            message += `• ${result.created} alumnos creados\n`;
            if (result.skipped > 0) message += `• ${result.skipped} omitidos (ya existen)\n`;
            if (result.errors > 0) message += `• ${result.errors} errores\n`;
            
            if (result.details.error_messages.length > 0) {
                message += `\nErrores:\n${result.details.error_messages.slice(0, 5).join('\n')}`;
            }
            
            showMessage(uploadMessage, message, 'success');
            
            // Reset form
            excelFileInput.value = '';
            excelFileName.classList.add('hidden');
            uploadExcelBtn.disabled = true;
            
            // Refresh dashboard
            setTimeout(() => {
                fetchDashboardData();
                loadStudentList();
                uploadProgress.classList.add('hidden');
            }, 2000);
        } else {
            const error = await response.json();
            showMessage(uploadMessage, ` Error: ${error.detail}`, 'error');
            uploadProgress.classList.add('hidden');
        }
    } catch (error) {
        showMessage(uploadMessage, ` Error de conexión: ${error.message}`, 'error');
        uploadProgress.classList.add('hidden');
    } finally {
        uploadExcelBtn.disabled = false;
    }
});

// ============================================
// STUDENT LIST
// ============================================

const studentListTable = document.getElementById('studentListTable');
const totalStudentsSpan = document.getElementById('totalStudents');
const refreshListBtn = document.getElementById('refreshList');

async function loadStudentList() {
    studentListTable.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">Cargando...</td></tr>';
    
    try {
        const students = await apiRequest('/api/students/');
        totalStudentsSpan.textContent = students.length;
        
        if (students.length === 0) {
            studentListTable.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No hay alumnos registrados</td></tr>';
            return;
        }
        
        studentListTable.innerHTML = students.map(student => `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3">${student.student_id}</td>
                <td class="px-4 py-3">${student.name}</td>
                <td class="px-4 py-3">${student.class_name}</td>
                <td class="px-4 py-3 text-center">
                    <button onclick="downloadQR('${student.qr_code_path.split('/').pop()}', '${student.student_id}')" 
                            class="text-blue-500 hover:text-blue-700 font-semibold text-sm">
                        📥 Descargar
                    </button>
                </td>
                <td class="px-4 py-3 text-center">
                    <button onclick="deleteStudent(${student.id})" 
                            class="text-red-500 hover:text-red-700 font-semibold text-sm">
                        🗑️ Eliminar
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        studentListTable.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-red-500">Error: ${error.message}</td></tr>`;
    }
}

refreshListBtn.addEventListener('click', loadStudentList);

// Download QR code function (global scope for onclick)
window.downloadQR = async function(qrFileName, studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/qr_codes/${qrFileName}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('No se pudo descargar el QR');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `QR_${studentId}.png`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert(`Error al descargar QR: ${error.message}`);
    }
};

// Delete student function (global scope for onclick)
window.deleteStudent = async function(studentId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este alumno?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/students/${studentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok || response.status === 204) {
            loadStudentList();
            fetchDashboardData();
        } else {
            alert('Error al eliminar el alumno');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
};

// Helper function to show messages
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `mt-4 p-3 rounded-md text-sm ${
        type === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
    }`;
    element.classList.remove('hidden');
}

// Student Profile Modal Functions
async function showStudentProfile(studentId) {
    try {
        const student = await apiRequest(`/api/students/${studentId}`);
        
        const modal = document.getElementById('studentProfileModal');
        const content = document.getElementById('studentProfileContent');
        
        content.innerHTML = `
            <div class="space-y-4">
                <div class="border-b pb-4">
                    <h4 class="text-2xl font-bold text-gray-800">${student.name}</h4>
                    <p class="text-sm text-gray-500">ID: ${student.student_id}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm font-semibold text-gray-600">Clase</p>
                        <p class="text-lg text-gray-800">${student.class_name}</p>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-600">Colegio</p>
                        <p class="text-lg text-blue-600">${student.school.name}</p>
                    </div>
                </div>
                
                <div>
                    <p class="text-sm font-semibold text-gray-600">Email del Padre/Madre</p>
                    <p class="text-lg text-gray-800">${student.parent_email}</p>
                </div>
                
                <div>
                    <p class="text-sm font-semibold text-gray-600">Estado</p>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        student.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                    }">
                        ${student.is_active ? '✓ Activo' : '✗ Inactivo'}
                    </span>
                </div>
                
                <div>
                    <p class="text-sm font-semibold text-gray-600">Fecha de Registro</p>
                    <p class="text-gray-800">${new Date(student.created_at).toLocaleDateString('es-ES')}</p>
                </div>
                
                ${student.qr_code_path ? `
                    <div>
                        <p class="text-sm font-semibold text-gray-600 mb-2">Código QR</p>
                        <img src="http://127.0.0.1:8088${student.qr_code_path}" alt="QR Code" class="w-48 h-48 border rounded">
                    </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading student profile:', error);
        alert('Error al cargar el perfil del alumno');
    }
}

function closeStudentProfile() {
    document.getElementById('studentProfileModal').style.display = 'none';
}

// Mobile menu toggle
function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 768) {
                if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }
}

// Initialize user on page load
initializeUser();
initializeMobileMenu();
