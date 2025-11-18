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
        // Use school-specific endpoint for directors, all users for admins
        const endpoint = getCurrentUserRole() === 'admin' ? '/api/users/' : '/api/users/school/users';
        users = await apiRequest(endpoint);
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
        // Don't show alert if it's just a 403 - let user see empty list
        if (error.message && !error.message.includes('403')) {
            alert('Error al cargar usuarios: ' + error.message);
        }
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
        'teacher': '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800"> Profesor</span>',
        'comedor': '<span class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">🍽️ Comedor</span>'
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

// Create Comedor User
async function createComedorUser() {
    const schoolId = document.getElementById('comedorSchool').value;
    const password = document.getElementById('comedorPassword').value;
    
    if (!schoolId) {
        alert('Por favor, selecciona un colegio');
        return;
    }
    
    if (!password || password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres');
        return;
    }
    
    try {
        const response = await apiRequest('/api/users/create-comedor', {
            method: 'POST',
            body: JSON.stringify({
                school_id: parseInt(schoolId),
                password: password
            })
        });
        
        alert('✅ Usuario Comedor creado exitosamente!\nUsuario: comedor\nContraseña: ' + password);
        closeComedorModal();
        loadUsers();
    } catch (error) {
        alert('Error al crear usuario comedor: ' + error.message);
    }
}

// Show Comedor Modal
function showComedorModal() {
    document.getElementById('comedorForm').reset();
    document.getElementById('comedorPassword').value = 'kitchen2025';
    
    // Populate schools
    const schoolSelect = document.getElementById('comedorSchool');
    schoolSelect.innerHTML = '<option value="">Seleccionar colegio...</option>';
    schools.forEach(school => {
        const option = document.createElement('option');
        option.value = school.id;
        option.textContent = school.name;
        schoolSelect.appendChild(option);
    });
    
    document.getElementById('comedorModal').style.display = 'flex';
}

// Close Comedor Modal
function closeComedorModal() {
    document.getElementById('comedorModal').style.display = 'none';
}

// Get current user's role
function getCurrentUserRole() {
    try {
        const userStr = localStorage.getItem('arrivapp_user');
        if (userStr) {
            const user = JSON.parse(userStr);
            return user.role;
        }
    } catch (e) {
        console.warn('Could not parse user role:', e);
    }
    return null;
}

// Get current user's school
function getCurrentUserSchool() {
    try {
        const userStr = localStorage.getItem('arrivapp_user');
        if (userStr) {
            const user = JSON.parse(userStr);
            return user.school_id;
        }
    } catch (e) {
        console.warn('Could not parse user school:', e);
    }
    return null;
}

// Load classes for teacher assignment
async function loadClassesForTeacher() {
    try {
        const response = await apiRequest('/api/users/classes');
        const select = document.getElementById('teacherClasses');
        select.innerHTML = '';
        
        if (response.classes && Array.isArray(response.classes)) {
            response.classes.forEach(className => {
                const option = document.createElement('option');
                option.value = className;
                option.textContent = className;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading classes:', error);
    }
}

// Create Teacher
async function createTeacher() {
    const fullName = document.getElementById('teacherName').value.trim();
    const email = document.getElementById('teacherEmail').value.trim();
    const password = document.getElementById('teacherPassword').value;
    const classSelect = document.getElementById('teacherClasses');
    const classes = Array.from(classSelect.selectedOptions).map(opt => opt.value);
    
    if (!fullName) {
        alert('Por favor, ingresa el nombre completo del profesor');
        return;
    }
    
    if (!email || !email.includes('@')) {
        alert('Por favor, ingresa un email válido');
        return;
    }
    
    if (!password || password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres');
        return;
    }
    
    try {
        const response = await apiRequest('/api/users/create-teacher', {
            method: 'POST',
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                password: password,
                classes: classes
            })
        });
        
        let message = `✅ Profesor creado exitosamente!\nNombre: ${response.full_name}\nEmail: ${response.email}\nColegio: ${response.school}`;
        if (response.assigned_classes && response.assigned_classes.length > 0) {
            message += `\nClases: ${response.assigned_classes.join(', ')}`;
        }
        alert(message);
        closeTeacherModal();
        loadUsers();
    } catch (error) {
        alert('Error al crear profesor: ' + error.message);
    }
}

// Show Teacher Modal
function showTeacherModal() {
    const userRole = getCurrentUserRole();
    
    // Only show for directors and admins
    if (userRole !== 'director' && userRole !== 'admin') {
        alert('Solo directores y administradores pueden crear profesores');
        return;
    }
    
    document.getElementById('teacherForm').reset();
    
    // Load available classes
    loadClassesForTeacher();
    
    // Set school display name
    let schoolName = 'Tu escuela';
    try {
        const userStr = localStorage.getItem('arrivapp_user');
        if (userStr) {
            const user = JSON.parse(userStr);
            const school = schools.find(s => s.id === user.school_id);
            schoolName = school ? school.name : 'Tu escuela';
        }
    } catch (e) {
        console.warn('Could not get school name:', e);
    }
    document.getElementById('teacherSchoolDisplay').textContent = schoolName;
    
    document.getElementById('teacherModal').style.display = 'flex';
}

// Close Teacher Modal
function closeTeacherModal() {
    document.getElementById('teacherModal').style.display = 'none';
}

// Event listeners
document.getElementById('addUserBtn').addEventListener('click', showAddUserModal);
document.getElementById('addComedorBtn').addEventListener('click', showComedorModal);
document.getElementById('createTeacherBtn').addEventListener('click', showTeacherModal);
document.getElementById('cancelBtn').addEventListener('click', closeModal);
document.getElementById('cancelComedorBtn').addEventListener('click', closeComedorModal);
document.getElementById('cancelTeacherBtn').addEventListener('click', closeTeacherModal);
document.getElementById('comedorForm').addEventListener('submit', (e) => {
    e.preventDefault();
    createComedorUser();
});
document.getElementById('teacherForm').addEventListener('submit', (e) => {
    e.preventDefault();
    createTeacher();
});
document.getElementById('role').addEventListener('change', updateSchoolRequirement);

// Close modal when clicking outside
document.getElementById('userModal').addEventListener('click', (e) => {
    if (e.target.id === 'userModal') {
        closeModal();
    }
});

// Close comedor modal when clicking outside
document.getElementById('comedorModal').addEventListener('click', (e) => {
    if (e.target.id === 'comedorModal') {
        closeComedorModal();
    }
});

// Close teacher modal when clicking outside
document.getElementById('teacherModal').addEventListener('click', (e) => {
    if (e.target.id === 'teacherModal') {
        closeTeacherModal();
    }
});

// Logout function
function logout() {
    localStorage.removeItem('arrivapp_token');
    localStorage.removeItem('arrivapp_user');
    window.location.href = 'login.html';
}

// Initialize
function initializeUI() {
    // Show/hide teacher button based on role
    let user = {};
    try {
        const userStr = localStorage.getItem('arrivapp_user');
        
        // Handle old format (plain string like "director_sj")
        if (userStr && !userStr.startsWith('{')) {
            console.log('Migrating old localStorage format...');
            // Old format detected - clear it and redirect to login
            localStorage.removeItem('arrivapp_token');
            localStorage.removeItem('arrivapp_user');
            localStorage.removeItem('arrivapp_user_role');
            alert('Por favor, inicia sesión nuevamente después de esta actualización.');
            window.location.href = 'login.html';
            return;
        }
        
        // Try to parse as JSON
        if (userStr) {
            user = JSON.parse(userStr);
        }
    } catch (e) {
        console.warn('Could not parse user from localStorage:', e);
        user = {};
    }
    
    const createTeacherBtn = document.getElementById('createTeacherBtn');
    
    if (user.role === 'director' || user.role === 'admin') {
        createTeacherBtn.style.display = 'block';
    } else {
        createTeacherBtn.style.display = 'none';
    }
    
    loadSchools();
    loadUsers();
}

initializeUI();
