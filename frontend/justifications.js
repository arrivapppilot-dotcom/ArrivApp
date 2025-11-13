const API_BASE_URL = 'http://localhost:8088';
const token = localStorage.getItem('arrivapp_token');
let currentUser = null;
let students = [];
let currentJustificationId = null;

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

// Fetch with auth
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

// Initialize
async function init() {
    try {
        // Get current user
        const userResponse = await apiRequest('/api/auth/me');
        currentUser = await userResponse.json();
        
        document.getElementById('userInfo').textContent = `${currentUser.full_name || currentUser.username}`;

        // Show review tab for staff
        if (currentUser.is_admin || currentUser.role !== 'teacher') {
            document.getElementById('tab-review').classList.remove('hidden');
        }

        // Load students for the form
        await loadStudents();

        // Set default date to today
        document.getElementById('justification_date').valueAsDate = new Date();

    } catch (error) {
        console.error('Error initializing:', error);
    }
}

// Load students
async function loadStudents() {
    try {
        const response = await apiRequest('/api/students/');
        students = await response.json();

        const select = document.getElementById('student_select');
        select.innerHTML = '<option value="">Selecciona un alumno</option>';
        
        students.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = `${student.name} (${student.class_name})`;
            option.dataset.email = student.parent_email;
            select.appendChild(option);
        });

        // Auto-fill parent email when student is selected
        select.addEventListener('change', (e) => {
            const selectedOption = e.target.options[e.target.selectedIndex];
            if (selectedOption.dataset.email) {
                document.getElementById('parent_email').value = selectedOption.dataset.email;
            }
        });

    } catch (error) {
        console.error('Error loading students:', error);
    }
}

// Submit justification form
document.getElementById('justificationForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitMessage = document.getElementById('submitMessage');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Enviando...';

    const data = {
        student_id: parseInt(document.getElementById('student_select').value),
        justification_type: document.getElementById('justification_type').value,
        date: new Date(document.getElementById('justification_date').value).toISOString(),
        reason: document.getElementById('reason').value.trim(),
        submitted_by: document.getElementById('parent_email').value.trim()
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/justifications/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            submitMessage.className = 'p-3 rounded-md bg-green-50 text-green-800 border border-green-200';
            submitMessage.textContent = ' Justificación enviada correctamente. Será revisada por el personal del colegio.';
            submitMessage.classList.remove('hidden');
            
            // Reset form
            document.getElementById('justificationForm').reset();
            document.getElementById('justification_date').valueAsDate = new Date();

            // Reload list if on that tab
            setTimeout(() => {
                submitMessage.classList.add('hidden');
            }, 5000);

        } else {
            const error = await response.json();
            submitMessage.className = 'p-3 rounded-md bg-red-50 text-red-800 border border-red-200';
            submitMessage.textContent = ` Error: ${error.detail || 'No se pudo enviar la justificación'}`;
            submitMessage.classList.remove('hidden');
        }

    } catch (error) {
        submitMessage.className = 'p-3 rounded-md bg-red-50 text-red-800 border border-red-200';
        submitMessage.textContent = ` Error de conexión: ${error.message}`;
        submitMessage.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Enviar Justificación';
    }
});

// Load my justifications (parent view)
async function loadMyJustifications() {
    const listContainer = document.getElementById('justificationsList');
    listContainer.innerHTML = '<p class="text-gray-500 text-center py-8">Cargando...</p>';

    try {
        const status = document.getElementById('filter_status').value;
        let url = '/api/justifications/';
        if (status) {
            url += `?status=${status}`;
        }

        const response = await apiRequest(url);
        const justifications = await response.json();

        if (justifications.length === 0) {
            listContainer.innerHTML = '<p class="text-gray-500 text-center py-8">No hay justificaciones registradas</p>';
            return;
        }

        listContainer.innerHTML = justifications.map(j => {
            const student = students.find(s => s.id === j.student_id);
            const statusClass = `status-${j.status}`;
            const statusText = {
                'pending': 'Pendiente',
                'approved': 'Aprobada',
                'rejected': 'Rechazada'
            };

            return `
                <div class="border border-gray-200 rounded-lg p-4">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <h4 class="font-semibold text-lg">${student ? student.name : 'Alumno #' + j.student_id}</h4>
                            <p class="text-sm text-gray-600">
                                ${typeLabels[j.justification_type]} - ${new Date(j.date).toLocaleDateString('es-ES')}
                            </p>
                        </div>
                        <span class="status-badge ${statusClass}">${statusText[j.status]}</span>
                    </div>
                    <p class="text-gray-700 mb-2">${j.reason}</p>
                    <p class="text-xs text-gray-500">Enviado: ${new Date(j.submitted_at).toLocaleString('es-ES')}</p>
                    ${j.notes ? `<p class="text-sm text-gray-600 mt-2 p-2 bg-gray-50 rounded"><strong>Notas:</strong> ${j.notes}</p>` : ''}
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading justifications:', error);
        listContainer.innerHTML = '<p class="text-red-500 text-center py-8">Error al cargar justificaciones</p>';
    }
}

// Load all justifications (staff view)
async function loadAllJustifications() {
    const listContainer = document.getElementById('reviewList');
    listContainer.innerHTML = '<p class="text-gray-500 text-center py-8">Cargando...</p>';

    try {
        const status = document.getElementById('review_filter_status').value;
        let url = '/api/justifications/';
        if (status) {
            url += `?status=${status}`;
        }

        const response = await apiRequest(url);
        const justifications = await response.json();

        if (justifications.length === 0) {
            listContainer.innerHTML = '<p class="text-gray-500 text-center py-8">No hay justificaciones para revisar</p>';
            return;
        }

        listContainer.innerHTML = justifications.map(j => {
            const student = students.find(s => s.id === j.student_id);
            const statusClass = `status-${j.status}`;
            const statusText = {
                'pending': 'Pendiente',
                'approved': 'Aprobada',
                'rejected': 'Rechazada'
            };

            return `
                <div class="border border-gray-200 rounded-lg p-4">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex-1">
                            <h4 class="font-semibold text-lg">${student ? student.name : 'Alumno #' + j.student_id}</h4>
                            <p class="text-sm text-gray-600">
                                ${typeLabels[j.justification_type]} - ${new Date(j.date).toLocaleDateString('es-ES')}
                            </p>
                            <p class="text-sm text-gray-500">Email: ${j.submitted_by}</p>
                        </div>
                        <span class="status-badge ${statusClass}">${statusText[j.status]}</span>
                    </div>
                    <p class="text-gray-700 mb-2"><strong>Motivo:</strong> ${j.reason}</p>
                    <p class="text-xs text-gray-500">Enviado: ${new Date(j.submitted_at).toLocaleString('es-ES')}</p>
                    ${j.notes ? `<p class="text-sm text-gray-600 mt-2 p-2 bg-gray-50 rounded"><strong>Notas:</strong> ${j.notes}</p>` : ''}
                    ${j.status === 'pending' ? `
                        <button onclick="openReviewModal(${j.id})" class="mt-3 px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">
                            Revisar
                        </button>
                    ` : ''}
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading justifications:', error);
        listContainer.innerHTML = '<p class="text-red-500 text-center py-8">Error al cargar justificaciones</p>';
    }
}

const typeLabels = {
    'absence': '🏠 Ausencia',
    'tardiness': ' Retraso',
    'early_dismissal': ' Salida anticipada'
};

// Open review modal
async function openReviewModal(justificationId) {
    currentJustificationId = justificationId;
    
    try {
        const response = await apiRequest(`/api/justifications/${justificationId}`);
        const j = await response.json();
        const student = students.find(s => s.id === j.student_id);

        const content = `
            <div class="space-y-3">
                <div><strong>Alumno:</strong> ${student ? student.name : 'Alumno #' + j.student_id}</div>
                <div><strong>Tipo:</strong> ${typeLabels[j.justification_type]}</div>
                <div><strong>Fecha:</strong> ${new Date(j.date).toLocaleDateString('es-ES')}</div>
                <div><strong>Motivo:</strong> ${j.reason}</div>
                <div><strong>Enviado por:</strong> ${j.submitted_by}</div>
                <div><strong>Fecha de envío:</strong> ${new Date(j.submitted_at).toLocaleString('es-ES')}</div>
            </div>
        `;

        document.getElementById('reviewContent').innerHTML = content;
        document.getElementById('review_notes').value = j.notes || '';
        document.getElementById('reviewModal').classList.remove('hidden');

    } catch (error) {
        console.error('Error loading justification:', error);
        alert('Error al cargar la justificación');
    }
}

// Close review modal
function closeReviewModal() {
    document.getElementById('reviewModal').classList.add('hidden');
    currentJustificationId = null;
}

// Update justification status
async function updateJustificationStatus(newStatus) {
    if (!currentJustificationId) return;

    const notes = document.getElementById('review_notes').value.trim();

    try {
        const response = await apiRequest(`/api/justifications/${currentJustificationId}`, {
            method: 'PUT',
            body: JSON.stringify({
                status: newStatus,
                notes: notes || null
            })
        });

        if (response.ok) {
            alert(`Justificación ${newStatus === 'approved' ? 'aprobada' : 'rechazada'} correctamente`);
            closeReviewModal();
            loadAllJustifications();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail || 'No se pudo actualizar'}`);
        }

    } catch (error) {
        console.error('Error updating justification:', error);
        alert('Error de conexión');
    }
}

// Tab switching
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
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
        const contentId = 'content-' + button.id.replace('tab-', '');
        document.getElementById(contentId).classList.remove('hidden');

        // Load data when switching tabs
        if (button.id === 'tab-list') {
            loadMyJustifications();
        } else if (button.id === 'tab-review') {
            loadAllJustifications();
        }
    });
});

// Filter change events
document.getElementById('filter_status').addEventListener('change', loadMyJustifications);
document.getElementById('review_filter_status').addEventListener('change', loadAllJustifications);

// Initialize on page load
init();
