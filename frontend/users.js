// Auto-detect environment and use appropriate API URL
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://arrivapp-backend.onrender.com';
let users = [];
let schools = [];
let editingUserId = null;

// Authentication check
function checkAuth() {
    const token = localStorage.getItem('arrivapp_token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }
    return token;
}

const token = checkAuth();

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
        localStorage.removeItem('arrivapp_token');
        localStorage.removeItem('arrivapp_user');
        window.location.href = 'login.html';
        return;
    }
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    
    if (response.status === 204) {
        return null;
    }
    
    return await response.json();
}

// Load schools for dropdown
async function loadSchools() {
    try {
        schools = await apiRequest('/api/schools/');
        const schoolSelect = document.getElementById('schoolId');
        schoolSelect.innerHTML = '<option value="">Seleccionar colegio...</option>';
        schools.forEach(school => {
            const option = document.createElement('option');
            option.value = school.id;
            option.textContent = school.name;
            schoolSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading schools:', error);
    }
}

// Load users
async function loadUsers() {
    try {
        users = await apiRequest('/api/users/');
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
        alert('Error al cargar usuarios: ' + error.message);
    }
}

// Render users table
function renderUsers() {
    const tbody = document.getElementById('usersTableBody');
    document.getElementById('userCount').textContent = users.length;
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                    No hay usuarios registrados
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const roleBadge = getRoleBadge(user.role);
        const schoolName = user.school ? user.school.name : '<span class="text-gray-400">Sin colegio</span>';
        const statusBadge = user.is_active 
            ? '<span class="badge badge-success">Activo</span>'
            : '<span class="badge badge-danger">Inactivo</span>';
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4">
                    <div class="font-semibold text-gray-900">${user.username}</div>
                    ${user.full_name ? `<div class="text-sm text-gray-500">${user.full_name}</div>` : ''}
                </td>
                <td class="px-6 py-4 text-sm text-gray-700">${user.email}</td>
                <td class="px-6 py-4">${roleBadge}</td>
                <td class="px-6 py-4 text-sm text-gray-700">${schoolName}</td>
                <td class="px-6 py-4">${statusBadge}</td>
                <td class="px-6 py-4 text-center">
                    <button onclick="editUser(${user.id})" class="text-blue-600 hover:text-blue-800 mr-3 font-semibold">
                        ✏️ Editar
                    </button>
                    <button onclick="deleteUser(${user.id}, '${user.username}')" class="text-red-600 hover:text-red-800 font-semibold">
                        🗑️ Eliminar
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Get role badge HTML
function getRoleBadge(role) {
    const badges = {
        'admin': '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">👑 Admin</span>',
        'director': '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800"> Director</span>',
        'teacher': '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800"> Profesor</span>'
    };
    return badges[role] || role;
}

// Show modal for adding user
function showAddUserModal() {
    editingUserId = null;
    document.getElementById('modalTitle').textContent = 'Añadir Usuario';
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';
    document.getElementById('password').required = true;
    document.getElementById('passwordRequired').style.display = 'inline';
    document.getElementById('userModal').style.display = 'flex';
    updateSchoolRequirement();
}

// Edit user
async function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    editingUserId = userId;
    document.getElementById('modalTitle').textContent = 'Editar Usuario';
    document.getElementById('userId').value = user.id;
    document.getElementById('username').value = user.username;
    document.getElementById('username').disabled = true; // Username can't be changed
    document.getElementById('email').value = user.email;
    document.getElementById('fullName').value = user.full_name || '';
    document.getElementById('role').value = user.role;
    document.getElementById('schoolId').value = user.school_id || '';
    document.getElementById('password').value = '';
    document.getElementById('password').required = false;
    document.getElementById('passwordRequired').style.display = 'none';
    
    updateSchoolRequirement();
    document.getElementById('userModal').style.display = 'flex';
}

// Delete user
async function deleteUser(userId, username) {
    if (!confirm(`¿Estás seguro de que deseas eliminar al usuario "${username}"?\n\nEsta acción no se puede deshacer.`)) {
        return;
    }
    
    try {
        await apiRequest(`/api/users/${userId}`, { method: 'DELETE' });
        alert('Usuario eliminado exitosamente');
        await loadUsers();
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error al eliminar usuario: ' + error.message);
    }
}

// Update school requirement based on role
function updateSchoolRequirement() {
    const role = document.getElementById('role').value;
    const schoolGroup = document.getElementById('schoolGroup');
    const schoolRequired = document.getElementById('schoolRequired');
    const schoolSelect = document.getElementById('schoolId');
    
    if (role === 'admin') {
        schoolRequired.style.display = 'none';
        schoolSelect.required = false;
        schoolGroup.style.opacity = '0.5';
    } else if (role === 'director' || role === 'teacher') {
        schoolRequired.style.display = 'inline';
        schoolSelect.required = true;
        schoolGroup.style.opacity = '1';
    } else {
        schoolRequired.style.display = 'none';
        schoolSelect.required = false;
        schoolGroup.style.opacity = '1';
    }
}

// Handle form submission
document.getElementById('userForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = document.getElementById('userId').value;
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const fullName = document.getElementById('fullName').value.trim();
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    const schoolId = document.getElementById('schoolId').value;
    
    // Validation
    if (!username || !email || !role) {
        alert('Por favor completa todos los campos requeridos');
        return;
    }
    
    if (!editingUserId && !password) {
        alert('La contraseña es requerida para nuevos usuarios');
        return;
    }
    
    if (password && password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres');
        return;
    }
    
    if ((role === 'director' || role === 'teacher') && !schoolId) {
        alert('El colegio es requerido para directores y profesores');
        return;
    }
    
    try {
        const userData = {
            email,
            full_name: fullName || null,
            role,
            school_id: schoolId ? parseInt(schoolId) : null
        };
        
        if (editingUserId) {
            // Update user
            if (password) {
                userData.password = password;
            }
            await apiRequest(`/api/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(userData)
            });
            alert('Usuario actualizado exitosamente');
        } else {
            // Create user
            userData.username = username;
            userData.password = password;
            await apiRequest('/api/users/', {
                method: 'POST',
                body: JSON.stringify(userData)
            });
            alert('Usuario creado exitosamente');
        }
        
        closeModal();
        await loadUsers();
    } catch (error) {
        console.error('Error saving user:', error);
        alert('Error al guardar usuario: ' + error.message);
    }
});

// Close modal
function closeModal() {
    document.getElementById('userModal').style.display = 'none';
    document.getElementById('userForm').reset();
    document.getElementById('username').disabled = false;
    editingUserId = null;
}

// Event listeners
document.getElementById('addUserBtn').addEventListener('click', showAddUserModal);
document.getElementById('cancelBtn').addEventListener('click', closeModal);
document.getElementById('role').addEventListener('change', updateSchoolRequirement);

// Close modal when clicking outside
document.getElementById('userModal').addEventListener('click', (e) => {
    if (e.target.id === 'userModal') {
        closeModal();
    }
});

// Logout function
function logout() {
    localStorage.removeItem('arrivapp_token');
    localStorage.removeItem('arrivapp_user');
    window.location.href = 'login.html';
}

// Initialize
loadSchools();
loadUsers();
