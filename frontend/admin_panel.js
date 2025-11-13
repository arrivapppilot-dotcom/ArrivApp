const API_BASE_URL = 'http://localhost:8088';
const token = localStorage.getItem('arrivapp_token');
let currentUser = null;
let selectedUserId = null;

// Check authentication
if (!token) {
    window.location.href = 'login.html';
}

// Logout function
function logout() {
    localStorage.removeItem('arrivapp_token');
    localStorage.removeItem('arrivapp_user');
    window.location.href = 'login.html';
}

// API Request helper
async function apiRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        logout();
        return null;
    }

    return response;
}

// Show message
function showMessage(message, type = 'success') {
    const container = document.getElementById('messageContainer');
    container.className = `p-4 rounded-lg mb-6 ${type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`;
    container.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                ${type === 'success' 
                    ? '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
                    : '<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />'
                }
            </svg>
            <span>${message}</span>
        </div>
    `;
    container.classList.remove('hidden');
    
    setTimeout(() => {
        container.classList.add('hidden');
    }, 5000);
}

// Initialize
async function init() {
    try {
        const response = await apiRequest('/api/auth/me');
        currentUser = await response.json();
        
        // Check if user is admin
        if (!currentUser.is_admin) {
            alert('Acceso denegado. Solo administradores pueden acceder a este panel.');
            window.location.href = 'dashboard.html';
            return;
        }

        document.getElementById('adminName').textContent = currentUser.full_name || currentUser.username;

        // Load saved settings
        loadSettings();

    } catch (error) {
        console.error('Error initializing:', error);
        showMessage('Error al cargar configuración', 'error');
    }
}

// Load settings from localStorage
function loadSettings() {
    const lateThreshold = localStorage.getItem('lateThreshold') || '09:01';
    const absentCheckTime = localStorage.getItem('absentCheckTime') || '09:10';
    const earlyDismissalTime = localStorage.getItem('earlyDismissalTime') || '14:00';
    const sessionTimeout = localStorage.getItem('sessionTimeout') || '60';

    document.getElementById('lateThreshold').value = lateThreshold;
    document.getElementById('absentCheckTime').value = absentCheckTime;
    document.getElementById('earlyDismissalTime').value = earlyDismissalTime;
    document.getElementById('sessionTimeout').value = sessionTimeout;

    // Load email templates
    const absentSubject = localStorage.getItem('absentEmailSubject') || ' {student_name} ausente hoy - {date}';
    const absentBody = localStorage.getItem('absentEmailBody') || `Estimado/a padre/madre de {student_name},

Le informamos que su hijo/a NO ha llegado al colegio hoy {date}.

Si conoce el motivo de la ausencia, por favor contacte con el colegio.

Gracias,
{school_name}`;

    document.getElementById('absentEmailSubject').value = absentSubject;
    document.getElementById('absentEmailBody').value = absentBody;

    const lateSubject = localStorage.getItem('lateEmailSubject') || ' {student_name} llegó tarde - {time}';
    const lateBody = localStorage.getItem('lateEmailBody') || `Estimado/a padre/madre de {student_name},

Le informamos que su hijo/a llegó tarde al colegio hoy a las {time}.

Hora de entrada: {time}

Gracias,
{school_name}`;

    document.getElementById('lateEmailSubject').value = lateSubject;
    document.getElementById('lateEmailBody').value = lateBody;

    const earlySubject = localStorage.getItem('earlyEmailSubject') || ' ALERTA: {student_name} salió anticipadamente';
    const earlyBody = localStorage.getItem('earlyEmailBody') || ` ALERTA DE SALIDA ANTICIPADA

Estimado/a padre/madre de {student_name},

Su hijo/a salió del colegio ANTES de la hora normal.

Hora de salida: {time}
Fecha: {date}

Si usted autorizó esta salida, ignore este mensaje.
Si NO autorizó esta salida, contacte inmediatamente con el colegio.

Gracias,
{school_name}`;

    document.getElementById('earlyEmailSubject').value = earlySubject;
    document.getElementById('earlyEmailBody').value = earlyBody;
}

// Save Late Threshold
function saveLateThreshold() {
    const value = document.getElementById('lateThreshold').value;
    localStorage.setItem('lateThreshold', value);
    showMessage(`Umbral de retraso guardado: ${value}`);
}

// Save Absent Check Time
function saveAbsentCheckTime() {
    const value = document.getElementById('absentCheckTime').value;
    localStorage.setItem('absentCheckTime', value);
    showMessage(`Hora de verificación de ausencias guardada: ${value}`);
}

// Save Early Dismissal Time
function saveEarlyDismissalTime() {
    const value = document.getElementById('earlyDismissalTime').value;
    localStorage.setItem('earlyDismissalTime', value);
    showMessage(`Hora de salida anticipada guardada: ${value}`);
}

// Save Email Template
function saveEmailTemplate(type) {
    if (type === 'absence') {
        const subject = document.getElementById('absentEmailSubject').value;
        const body = document.getElementById('absentEmailBody').value;
        localStorage.setItem('absentEmailSubject', subject);
        localStorage.setItem('absentEmailBody', body);
        showMessage('Plantilla de email de ausencia guardada');
    } else if (type === 'late') {
        const subject = document.getElementById('lateEmailSubject').value;
        const body = document.getElementById('lateEmailBody').value;
        localStorage.setItem('lateEmailSubject', subject);
        localStorage.setItem('lateEmailBody', body);
        showMessage('Plantilla de email de retraso guardada');
    } else if (type === 'early') {
        const subject = document.getElementById('earlyEmailSubject').value;
        const body = document.getElementById('earlyEmailBody').value;
        localStorage.setItem('earlyEmailSubject', subject);
        localStorage.setItem('earlyEmailBody', body);
        showMessage('Plantilla de email de salida anticipada guardada');
    }
}

// Search User
async function searchUser() {
    const searchTerm = document.getElementById('searchUsername').value.trim();
    
    if (!searchTerm) {
        showMessage('Por favor ingrese un nombre de usuario o email', 'error');
        return;
    }

    try {
        const response = await apiRequest(`/api/users/search?q=${encodeURIComponent(searchTerm)}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showMessage('Usuario no encontrado', 'error');
                return;
            }
            throw new Error('Error al buscar usuario');
        }

        const user = await response.json();
        selectedUserId = user.id;

        // Display user info
        document.getElementById('foundUserName').textContent = user.full_name || user.username;
        document.getElementById('foundUserEmail').textContent = user.email;
        document.getElementById('foundUserRole').textContent = `Rol: ${user.role || 'teacher'}`;
        document.getElementById('userSearchResults').classList.remove('hidden');

        // Clear password fields
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';

    } catch (error) {
        console.error('Error searching user:', error);
        showMessage('Error al buscar usuario', 'error');
    }
}

// Reset User Password
async function resetUserPassword() {
    if (!selectedUserId) {
        showMessage('Por favor busque un usuario primero', 'error');
        return;
    }

    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!newPassword || !confirmPassword) {
        showMessage('Por favor complete ambos campos de contraseña', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showMessage('Las contraseñas no coinciden', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
        return;
    }

    if (!confirm('¿Está seguro de que desea restablecer la contraseña de este usuario?')) {
        return;
    }

    try {
        const response = await apiRequest(`/api/users/${selectedUserId}/reset-password`, {
            method: 'PUT',
            body: JSON.stringify({ new_password: newPassword })
        });

        if (!response.ok) {
            throw new Error('Error al restablecer contraseña');
        }

        showMessage(' Contraseña restablecida correctamente');
        
        // Clear form
        document.getElementById('userSearchResults').classList.add('hidden');
        document.getElementById('searchUsername').value = '';
        selectedUserId = null;

    } catch (error) {
        console.error('Error resetting password:', error);
        showMessage('Error al restablecer contraseña', 'error');
    }
}

// Save Session Timeout
function saveSessionTimeout() {
    const value = document.getElementById('sessionTimeout').value;
    if (value < 15 || value > 480) {
        showMessage('El tiempo debe estar entre 15 y 480 minutos', 'error');
        return;
    }
    localStorage.setItem('sessionTimeout', value);
    showMessage(`Tiempo de sesión guardado: ${value} minutos`);
}

// Tab switching
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');
        
        // Remove active from all
        tabButtons.forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });
        
        // Hide all content
        tabContents.forEach(content => content.classList.add('hidden'));
        
        // Activate clicked tab
        button.classList.remove('border-transparent', 'text-gray-500');
        button.classList.add('border-blue-500', 'text-blue-600');
        
        // Show corresponding content
        document.getElementById(`tab-${tabName}`).classList.remove('hidden');
    });
});

// Initialize on load
init();
