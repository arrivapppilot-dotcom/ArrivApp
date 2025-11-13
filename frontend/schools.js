<<<<<<< HEAD
// Auto-detect if running on Cloudflare or localhost
const API_URL = window.location.hostname.includes('trycloudflare.com') 
    ? 'https://enhancement-organizations-herb-patio.trycloudflare.com'
    : 'http://127.0.0.1:8088';
=======
// Auto-detect environment and use appropriate API URL
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : 'https://arrivapp.onrender.com';
>>>>>>> 9f15d0eae153ab3b33a76af26bd9d0987270a37e

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('arrivapp_token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }
    return token;
}

// Get user email
async function getUserInfo() {
    const token = checkAuth();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const user = await response.json();
            document.getElementById('userEmail').textContent = user.email;
        }
    } catch (error) {
        console.error('Error getting user info:', error);
    }
}

// Load schools
async function loadSchools() {
    const token = checkAuth();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/schools/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const schools = await response.json();
            displaySchools(schools);
        } else {
            console.error('Error loading schools');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Display schools
function displaySchools(schools) {
    const container = document.getElementById('schoolsList');
    
    if (schools.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-16">
                <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                <p class="mt-4 text-gray-600 text-lg">No hay colegios registrados</p>
                <p class="text-gray-500">Haz clic en "Añadir Colegio" para crear uno</p>
            </div>
        `;
        return;
    }

    container.innerHTML = schools.map(school => `
        <div class="school-card bg-white rounded-xl shadow-lg overflow-hidden">
            <!-- Card Header -->
            <div class="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
                <div class="flex justify-between items-start">
                    <div class="flex items-center space-x-2">
                        <span class="text-3xl"></span>
                        <h3 class="text-lg font-bold text-white">${school.name}</h3>
                    </div>
                    <span class="px-3 py-1 rounded-full text-xs font-semibold ${school.is_active ? 'bg-green-400 text-green-900' : 'bg-red-400 text-red-900'}">
                        ${school.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                </div>
            </div>
            
            <!-- Card Body -->
            <div class="p-6">
                <div class="space-y-3">
                    <div class="flex items-center text-gray-600">
                        <span class="font-semibold text-sm text-gray-500 w-12">ID:</span>
                        <span class="text-sm">${school.id}</span>
                    </div>
                    ${school.address ? `
                    <div class="flex items-start text-gray-600">
                        <span class="text-lg mr-2">📍</span>
                        <span class="text-sm">${school.address}</span>
                    </div>
                    ` : ''}
                    ${school.contact_email ? `
                    <div class="flex items-center text-gray-600">
                        <span class="text-lg mr-2"></span>
                        <a href="mailto:${school.contact_email}" class="text-sm text-indigo-600 hover:underline">${school.contact_email}</a>
                    </div>
                    ` : ''}
                    ${school.contact_phone ? `
                    <div class="flex items-center text-gray-600">
                        <span class="text-lg mr-2">📞</span>
                        <span class="text-sm">${school.contact_phone}</span>
                    </div>
                    ` : ''}
                    <div class="flex items-center text-gray-600">
                        <span class="text-lg mr-2">🌍</span>
                        <span class="text-sm">${school.timezone}</span>
                    </div>
                    <div class="pt-2 border-t border-gray-200">
                        <p class="text-xs text-gray-500">Creado: ${new Date(school.created_at).toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                    </div>
                </div>
            </div>
            
            <!-- Card Actions -->
            <div class="bg-gray-50 px-6 py-4 flex space-x-3">
                <button onclick="editSchool(${school.id})" class="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2.5 rounded-lg font-semibold transition flex items-center justify-center space-x-2 shadow-md">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                    <span>Editar</span>
                </button>
                <button onclick="viewSchoolStudents(${school.id})" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 rounded-lg font-semibold transition flex items-center justify-center space-x-2 shadow-md">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                    </svg>
                    <span>Ver Alumnos</span>
                </button>
            </div>
        </div>
    `).join('');
}

// Show add school modal
function showAddSchoolModal() {
    document.getElementById('addSchoolModal').classList.remove('hidden');
}

// Close add school modal
function closeAddSchoolModal() {
    document.getElementById('addSchoolModal').classList.add('hidden');
    document.getElementById('addSchoolForm').reset();
}

// Add school
async function addSchool(event) {
    event.preventDefault();
    const token = checkAuth();
    if (!token) return;

    const schoolData = {
        name: document.getElementById('schoolName').value,
        address: document.getElementById('schoolAddress').value || null,
        contact_email: document.getElementById('schoolEmail').value || null,
        contact_phone: document.getElementById('schoolPhone').value || null,
        timezone: document.getElementById('schoolTimezone').value
    };

    try {
        const response = await fetch(`${API_URL}/api/schools/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schoolData)
        });

        if (response.ok) {
            alert(' Colegio creado exitosamente');
            closeAddSchoolModal();
            loadSchools();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al crear el colegio');
    }
}

// View school students
function viewSchoolStudents(schoolId) {
    localStorage.setItem('selectedSchoolId', schoolId);
    window.location.href = 'dashboard.html';
}

// Edit school
async function editSchool(schoolId) {
    const token = checkAuth();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/schools/${schoolId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const school = await response.json();
            showEditSchoolModal(school);
        } else {
            alert('Error al cargar los datos del colegio');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los datos del colegio');
    }
}

// Show edit school modal
function showEditSchoolModal(school) {
    document.getElementById('editSchoolId').value = school.id;
    document.getElementById('editSchoolName').value = school.name;
    document.getElementById('editSchoolAddress').value = school.address || '';
    document.getElementById('editSchoolEmail').value = school.contact_email || '';
    document.getElementById('editSchoolPhone').value = school.contact_phone || '';
    document.getElementById('editSchoolTimezone').value = school.timezone;
    document.getElementById('editSchoolActive').checked = school.is_active;
    document.getElementById('editSchoolModal').classList.remove('hidden');
}

// Close edit school modal
function closeEditSchoolModal() {
    document.getElementById('editSchoolModal').classList.add('hidden');
    document.getElementById('editSchoolForm').reset();
}

// Update school
async function updateSchool(event) {
    event.preventDefault();
    const token = checkAuth();
    if (!token) return;

    const schoolId = document.getElementById('editSchoolId').value;
    const schoolData = {
        name: document.getElementById('editSchoolName').value,
        address: document.getElementById('editSchoolAddress').value || null,
        contact_email: document.getElementById('editSchoolEmail').value || null,
        contact_phone: document.getElementById('editSchoolPhone').value || null,
        timezone: document.getElementById('editSchoolTimezone').value,
        is_active: document.getElementById('editSchoolActive').checked
    };

    try {
        const response = await fetch(`${API_URL}/api/schools/${schoolId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schoolData)
        });

        if (response.ok) {
            alert(' Colegio actualizado exitosamente');
            closeEditSchoolModal();
            loadSchools();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al actualizar el colegio');
    }
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('selectedSchoolId');
    window.location.href = 'login.html';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    getUserInfo();
    loadSchools();
});
