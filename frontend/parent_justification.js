const API_BASE_URL = 'http://localhost:8000';
let studentsList = [];
let validatedEmail = null;

// Set default date to today
document.getElementById('absence_date').valueAsDate = new Date();

// Email validation on blur
document.getElementById('parent_email').addEventListener('blur', async function() {
    const email = this.value.trim();
    if (!email) return;

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Por favor ingrese un correo electrónico válido');
        return;
    }

    // Check if email exists in database
    await validateEmailAndLoadStudents(email);
});

async function validateEmailAndLoadStudents(email) {
    try {
        showError('Verificando correo electrónico...', 'info');
        
        // Fetch all students with this parent email (public endpoint)
        const response = await fetch(`${API_BASE_URL}/api/justifications/validate-email?email=${encodeURIComponent(email)}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showError(' Este correo electrónico no está registrado en el sistema. Por favor contacte con el colegio.');
                document.getElementById('studentsSection').classList.add('hidden');
                validatedEmail = null;
                return;
            }
            throw new Error('Error al validar el correo');
        }

        const data = await response.json();
        studentsList = data.students;
        validatedEmail = email;

        if (studentsList.length === 0) {
            showError('No se encontraron alumnos asociados a este correo electrónico');
            document.getElementById('studentsSection').classList.add('hidden');
            return;
        }

        // Populate students dropdown
        const select = document.getElementById('student_select');
        select.innerHTML = '<option value="">Selecciona un alumno/a</option>';
        
        studentsList.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = `${student.name}${student.class_name ? ' - ' + student.class_name : ''}`;
            select.appendChild(option);
        });

        document.getElementById('studentsSection').classList.remove('hidden');
        hideError();
        
    } catch (error) {
        console.error('Error validating email:', error);
        showError('Error al verificar el correo. Por favor intente nuevamente.');
        document.getElementById('studentsSection').classList.add('hidden');
        validatedEmail = null;
    }
}

// Form submission
document.getElementById('justificationForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const email = document.getElementById('parent_email').value.trim();

    // Validate email was checked
    if (!validatedEmail || validatedEmail !== email) {
        showError('Por favor verifique el correo electrónico primero (presione Tab o haga clic fuera del campo)');
        document.getElementById('parent_email').focus();
        return;
    }

    // Validate student selected
    const studentId = document.getElementById('student_select').value;
    if (!studentId) {
        showError('Por favor seleccione un alumno/a');
        return;
    }

    // Get form data
    const justificationType = document.getElementById('reason_type').value;
    const reasonSelect = document.getElementById('reason').value;
    const notes = document.getElementById('notes').value.trim();
    const date = document.getElementById('absence_date').value;

    // Build full reason text
    let fullReason = reasonSelect;
    if (notes) {
        fullReason += ` - ${notes}`;
    }

    const data = {
        student_id: parseInt(studentId),
        justification_type: justificationType,
        date: new Date(date).toISOString(),
        reason: fullReason,
        submitted_by: email
    };

    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Enviando...';
    hideError();
    hideSuccess();

    try {
        const response = await fetch(`${API_BASE_URL}/api/justifications/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al enviar la notificación');
        }

        const result = await response.json();
        
        // Show success message
        const student = studentsList.find(s => s.id === parseInt(studentId));
        showSuccess(` Notificación enviada correctamente para ${student.name}. El colegio ha sido informado.`);
        
        // Reset form
        document.getElementById('justificationForm').reset();
        document.getElementById('absence_date').valueAsDate = new Date();
        document.getElementById('studentsSection').classList.add('hidden');
        validatedEmail = null;
        studentsList = [];
        
        // Scroll to success message
        document.getElementById('successMessage').scrollIntoView({ behavior: 'smooth', block: 'center' });

    } catch (error) {
        console.error('Error submitting justification:', error);
        showError(` ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Enviar Notificación';
    }
});

function showError(message, type = 'error') {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    errorText.textContent = message;
    errorDiv.classList.remove('hidden');
    
    if (type === 'error') {
        errorDiv.className = 'bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg';
    } else if (type === 'info') {
        errorDiv.className = 'bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg';
    }
    
    hideSuccess();
}

function hideError() {
    document.getElementById('errorMessage').classList.add('hidden');
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    const successText = document.getElementById('successText');
    
    successText.textContent = message;
    successDiv.classList.remove('hidden');
    hideError();
}

function hideSuccess() {
    document.getElementById('successMessage').classList.add('hidden');
}
