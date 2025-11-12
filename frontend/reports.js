// Auto-detect environment and use appropriate API URL
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://arrivapp.onrender.com';
const API_URL = `${API_BASE_URL}/api`;
let currentUser = null;
let dailyChart = null;
let distChart = null;
let weeklyChart = null;
let longTermTrendChart = null;
let monthlyComparisonChart = null;
let weekdayPatternChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    setupDefaultDates();
    setupEventListeners();
});

async function checkAuth() {
    const token = localStorage.getItem('arrivapp_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Authentication failed');
        }

        currentUser = await response.json();
        document.getElementById('userInfo').textContent = `${currentUser.username} (${currentUser.role})`;

        // Show school filter only for admin
        if (currentUser.role === 'admin') {
            document.getElementById('schoolFilterContainer').classList.remove('hidden');
            await loadSchools();
        }
    } catch (error) {
        console.error('Auth error:', error);
        localStorage.removeItem('arrivapp_token');
        window.location.href = 'login.html';
    }
}

async function loadSchools() {
    const token = localStorage.getItem('arrivapp_token');
    try {
        const response = await fetch(`${API_URL}/schools`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const schools = await response.json();
            const select = document.getElementById('schoolFilter');
            schools.forEach(school => {
                const option = document.createElement('option');
                option.value = school.id;
                option.textContent = school.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading schools:', error);
    }
}

function setupDefaultDates() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);

    document.getElementById('endDate').valueAsDate = today;
    document.getElementById('startDate').valueAsDate = thirtyDaysAgo;
}

function setupEventListeners() {
    document.getElementById('reportType').addEventListener('change', updateReportView);
}

function updateReportView() {
    const reportType = document.getElementById('reportType').value;
    
    // Hide all sections
    document.querySelectorAll('.report-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const sectionMap = {
        'statistics': 'statisticsSection',
        'history': 'historySection',
        'tardiness': 'tardinessSection',
        'analytics': 'analyticsSection'
    };

    const sectionId = sectionMap[reportType];
    if (sectionId) {
        document.getElementById(sectionId).classList.add('active');
    }
}

async function generateReport() {
    const reportType = document.getElementById('reportType').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const schoolId = document.getElementById('schoolFilter')?.value || null;

    if (!startDate || !endDate) {
        alert('Por favor selecciona un rango de fechas');
        return;
    }

    // Show loading
    document.getElementById('loadingSpinner').classList.remove('hidden');

    // Show the appropriate section FIRST so elements are in DOM
    updateReportView();

    try {
        if (reportType === 'statistics') {
            await generateStatistics(startDate, endDate, schoolId);
        } else if (reportType === 'history') {
            await generateHistory(startDate, endDate, schoolId);
        } else if (reportType === 'tardiness') {
            await generateTardinessAnalysis(startDate, endDate, schoolId);
        } else if (reportType === 'analytics') {
            await generateHistoricalAnalytics(startDate, endDate, schoolId);
        }
    } catch (error) {
        console.error('Error generating report:', error);
        alert('Error al generar el reporte. Por favor intenta de nuevo.');
    } finally {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }
}

async function generateStatistics(startDate, endDate, schoolId) {
    const token = localStorage.getItem('arrivapp_token');
    let url = `${API_URL}/reports/statistics?period=monthly&start_date=${startDate}&end_date=${endDate}`;
    if (schoolId) {
        url += `&school_id=${schoolId}`;
    }

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch statistics');
    }

    const data = await response.json();

    // Update summary cards
    document.getElementById('totalStudents').textContent = data.total_students;
    document.getElementById('totalAttendance').textContent = data.total_attendance;
    document.getElementById('attendanceRate').textContent = `${data.attendance_rate}%`;
    document.getElementById('lateRate').textContent = `${data.late_rate}%`;

    // Update daily breakdown table
    const tbody = document.getElementById('dailyBreakdownTable');
    tbody.innerHTML = '';

    if (data.daily_breakdown.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No hay datos para este período</td></tr>';
    } else {
        data.daily_breakdown.forEach(day => {
            const latePercentage = day.total > 0 ? ((day.late / day.total) * 100).toFixed(1) : 0;
            const row = `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${day.date}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${day.total}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-orange-600">${day.late}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${latePercentage}%</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }

    // Create daily trend chart
    createDailyTrendChart(data.daily_breakdown);

    // Create attendance distribution chart
    createAttendanceDistChart(data);
}

async function generateHistory(startDate, endDate, schoolId) {
    try {
        console.log('generateHistory called with:', { startDate, endDate, schoolId });
        const token = localStorage.getItem('arrivapp_token');
        let url = `${API_URL}/reports/attendance-history?start_date=${startDate}&end_date=${endDate}`;
        if (schoolId) {
            url += `&school_id=${schoolId}`;
        }

        console.log('Fetching from URL:', url);

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error:', errorText);
            throw new Error(`Failed to fetch history: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received data:', { total: data.total, recordCount: data.records.length });

        // Update total
        document.getElementById('historyTotal').textContent = data.total;

        // Update table
        const tbody = document.getElementById('historyTable');
        tbody.innerHTML = '';

        if (data.records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No hay registros para este período</td></tr>';
        } else {
            data.records.forEach(record => {
                const checkInTime = new Date(record.checkin_time); // Fixed: checkin_time not check_in_time
                const checkOutTime = record.checkout_time ? new Date(record.checkout_time) : null; // Fixed: checkout_time not check_out_time
                const status = record.is_late ?  // Fixed: is_late not late
                    '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800"> Tarde</span>' :
                    '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">✓ Puntual</span>';

                const row = `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${checkInTime.toLocaleDateString()}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${record.student_name}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${record.school_name || '-'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${checkInTime.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${checkOutTime ? checkOutTime.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'}) : '-'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">${status}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
        console.log('History generation complete!');
    } catch (error) {
        console.error('Error in generateHistory:', error);
        throw error; // Re-throw to be caught by generateReport
    }
}

async function generateTardinessAnalysis(startDate, endDate, schoolId) {
    const token = localStorage.getItem('arrivapp_token');
    let url = `${API_URL}/reports/tardiness-analysis?start_date=${startDate}&end_date=${endDate}`;
    if (schoolId) {
        url += `&school_id=${schoolId}`;
    }

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch tardiness analysis');
    }

    const data = await response.json();

    // Update top tardy students table
    const tbody = document.getElementById('tardyStudentsTable');
    tbody.innerHTML = '';

    if (data.top_tardy_students.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No hay datos para este período</td></tr>';
    } else {
        data.top_tardy_students.forEach((student, index) => {
            const badgeColor = student.late_percentage > 50 ? 'bg-red-100 text-red-800' :
                              student.late_percentage > 25 ? 'bg-orange-100 text-orange-800' :
                              'bg-yellow-100 text-yellow-800';

            const row = `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">${index + 1}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.student_name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.total_attendance}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-orange-600 font-semibold">${student.late_count}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span class="px-2 py-1 text-xs font-semibold rounded-full ${badgeColor}">${student.late_percentage}%</span>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }

    // Create weekly trends chart
    createWeeklyTrendsChart(data.weekly_trends);
}

function createDailyTrendChart(dailyData) {
    const ctx = document.getElementById('dailyTrendChart');
    
    // Destroy existing chart
    if (dailyChart) {
        dailyChart.destroy();
    }

    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(d => d.date),
            datasets: [
                {
                    label: 'Total Asistencia',
                    data: dailyData.map(d => d.total),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Llegadas Tardías',
                    data: dailyData.map(d => d.late),
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createAttendanceDistChart(stats) {
    const ctx = document.getElementById('attendanceDistChart');
    
    // Destroy existing chart
    if (distChart) {
        distChart.destroy();
    }

    distChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Presentes', 'Tardanzas', 'Salidas Tempranas'],
            datasets: [{
                data: [stats.present - stats.late, stats.late, stats.early_checkout],
                backgroundColor: [
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

function createWeeklyTrendsChart(weeklyData) {
    const ctx = document.getElementById('weeklyTrendsChart');
    
    // Destroy existing chart
    if (weeklyChart) {
        weeklyChart.destroy();
    }

    weeklyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.map(d => d.week),
            datasets: [
                {
                    label: 'Total Asistencia',
                    data: weeklyData.map(d => d.total),
                    backgroundColor: '#3b82f6',
                },
                {
                    label: 'Llegadas Tardías',
                    data: weeklyData.map(d => d.late),
                    backgroundColor: '#f59e0b',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function generateHistoricalAnalytics(startDate, endDate, schoolId) {
    try {
        const token = localStorage.getItem('arrivapp_token');
        let url = `${API_URL}/reports/historical-analytics?start_date=${startDate}&end_date=${endDate}`;
        if (schoolId) {
            url += `&school_id=${schoolId}`;
        }

        console.log('Fetching historical analytics from:', url);
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error response:', errorText);
            throw new Error(`Failed to fetch historical analytics: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Historical analytics data:', data);

        // Update summary metrics
        document.getElementById('avgMonthlyAttendance').textContent = data.avg_monthly_attendance.toFixed(1);
        document.getElementById('chronicAbsenteeCount').textContent = data.chronic_absentee_count;
        
        const trendIcon = data.overall_trend > 0 ? '' : data.overall_trend < 0 ? '📉' : '➡️';
        document.getElementById('overallTrend').textContent = `${trendIcon} ${Math.abs(data.overall_trend).toFixed(1)}%`;
        
        const punctualityIcon = data.punctuality_improvement > 0 ? '' : data.punctuality_improvement < 0 ? '📉' : '➡️';
        document.getElementById('punctualityTrend').textContent = `${punctualityIcon} ${Math.abs(data.punctuality_improvement).toFixed(1)}%`;

        // Create long-term trend chart
        console.log('Creating long-term trend chart...');
        try {
            createLongTermTrendChart(data.monthly_trends);
        } catch (e) {
            console.error('Error creating long-term trend chart:', e);
        }

        // Create monthly comparison chart
        console.log('Creating monthly comparison chart...');
        try {
            createMonthlyComparisonChart(data.monthly_comparison);
        } catch (e) {
            console.error('Error creating monthly comparison chart:', e);
        }

        // Update chronic absentees table
        console.log('Updating chronic absentees table...');
        try {
            updateChronicAbsenteesTable(data.chronic_absentees);
        } catch (e) {
            console.error('Error updating chronic absentees table:', e);
        }

        // Create weekday pattern chart
        console.log('Creating weekday pattern chart...');
        try {
            createWeekdayPatternChart(data.weekday_patterns);
        } catch (e) {
            console.error('Error creating weekday pattern chart:', e);
        }

        // Update improvement table
        console.log('Updating improvement table...');
        try {
            updateImprovementTable(data.top_improved_students);
        } catch (e) {
            console.error('Error updating improvement table:', e);
        };
        
        console.log('Historical analytics complete!');
    } catch (error) {
        console.error('Error in generateHistoricalAnalytics:', error);
        throw error; // Re-throw to be caught by generateReport
    }
}

function createLongTermTrendChart(monthlyData) {
    const ctx = document.getElementById('longTermTrendChart');
    console.log('longTermTrendChart element:', ctx);
    console.log('Monthly data for chart:', monthlyData);
    
    if (!ctx) {
        console.error('Chart canvas not found: longTermTrendChart');
        return;
    }
    
    if (longTermTrendChart) {
        longTermTrendChart.destroy();
    }

    longTermTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.map(d => d.month),
            datasets: [
                {
                    label: 'Tasa de Asistencia (%)',
                    data: monthlyData.map(d => d.attendance_rate),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Total Asistencias',
                    data: monthlyData.map(d => d.total_attendance),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                },
                {
                    label: 'Tardanzas',
                    data: monthlyData.map(d => d.late_count),
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.datasetIndex === 0) {
                                    label += context.parsed.y.toFixed(1) + '%';
                                } else {
                                    label += context.parsed.y;
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Tasa de Asistencia (%)'
                    },
                    beginAtZero: true,
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Cantidad'
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });
}

function createMonthlyComparisonChart(comparisonData) {
    const ctx = document.getElementById('monthlyComparisonChart');
    console.log('monthlyComparisonChart element:', ctx);
    console.log('Comparison data:', comparisonData);
    
    if (!ctx) {
        console.error('Chart canvas not found: monthlyComparisonChart');
        return;
    }
    
    if (monthlyComparisonChart) {
        monthlyComparisonChart.destroy();
    }

    monthlyComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: comparisonData.map(d => d.month),
            datasets: [
                {
                    label: 'Asistencias',
                    data: comparisonData.map(d => d.present),
                    backgroundColor: '#10b981',
                },
                {
                    label: 'Tardanzas',
                    data: comparisonData.map(d => d.late),
                    backgroundColor: '#f59e0b',
                },
                {
                    label: 'Ausencias',
                    data: comparisonData.map(d => d.absent),
                    backgroundColor: '#ef4444',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

function createWeekdayPatternChart(weekdayData) {
    const ctx = document.getElementById('weekdayPatternChart');
    console.log('weekdayPatternChart element:', ctx);
    console.log('Weekday data:', weekdayData);
    
    if (!ctx) {
        console.error('Chart canvas not found: weekdayPatternChart');
        return;
    }
    
    if (weekdayPatternChart) {
        weekdayPatternChart.destroy();
    }

    const weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];

    weekdayPatternChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: weekdays,
            datasets: [
                {
                    label: 'Tasa de Asistencia (%)',
                    data: weekdayData.map(d => d.attendance_rate),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                },
                {
                    label: 'Tasa de Puntualidad (%)',
                    data: weekdayData.map(d => d.punctuality_rate),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            }
        }
    });
}

function updateChronicAbsenteesTable(absentees) {
    const tbody = document.getElementById('chronicAbsenteesTable');
    console.log('chronicAbsenteesTable element:', tbody);
    console.log('Absentees data:', absentees);
    
    if (!tbody) {
        console.error('Table body not found: chronicAbsenteesTable');
        return;
    }
    
    tbody.innerHTML = '';

    if (absentees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">🎉 ¡No hay estudiantes con ausentismo crónico!</td></tr>';
        return;
    }

    absentees.forEach(student => {
        const riskLevel = student.attendance_rate < 50 ? 'Crítico' : 
                         student.attendance_rate < 70 ? 'Alto' : 'Moderado';
        const riskColor = student.attendance_rate < 50 ? 'bg-red-100 text-red-800' : 
                         student.attendance_rate < 70 ? 'bg-orange-100 text-orange-800' : 
                         'bg-yellow-100 text-yellow-800';

        const row = `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.student_name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${student.school_name || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.expected_days}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.attended_days}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${riskColor}">${student.attendance_rate.toFixed(1)}%</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${riskColor}">${riskLevel}</span>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function updateImprovementTable(improvedStudents) {
    const tbody = document.getElementById('improvementTable');
    console.log('improvementTable element:', tbody);
    console.log('Improved students data:', improvedStudents);
    
    if (!tbody) {
        console.error('Table body not found: improvementTable');
        return;
    }
    
    tbody.innerHTML = '';

    if (improvedStudents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No hay datos suficientes para comparar</td></tr>';
        return;
    }

    improvedStudents.forEach(student => {
        const improvementValue = student.improvement;
        const improvementColor = improvementValue > 20 ? 'bg-green-100 text-green-800' :
                                improvementValue > 10 ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800';

        const statusIcon = improvementValue > 20 ? '🌟' : improvementValue > 10 ? '' : '';

        const row = `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.student_name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.first_month_rate.toFixed(1)}%</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${student.last_month_rate.toFixed(1)}%</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${improvementColor}">+${improvementValue.toFixed(1)}%</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-2xl">${statusIcon}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

async function exportPDF() {
    const reportType = document.getElementById('reportType').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const schoolId = document.getElementById('schoolFilter')?.value || null;

    if (!startDate || !endDate) {
        alert('Por favor selecciona un rango de fechas');
        return;
    }

    const token = localStorage.getItem('arrivapp_token');
    let url = `${API_URL}/reports/export-pdf?report_type=${reportType}&start_date=${startDate}&end_date=${endDate}`;
    if (schoolId) {
        url += `&school_id=${schoolId}`;
    }

    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to export PDF');
        }

        // Download the PDF
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `arrivapp_${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();

        alert('PDF descargado exitosamente');
    } catch (error) {
        console.error('Error exporting PDF:', error);
        alert('Error al exportar PDF. Por favor intenta de nuevo.');
    }
}

function logout() {
    localStorage.removeItem('arrivapp_token');
    localStorage.removeItem('arrivapp_user');
    window.location.href = 'login.html';
}
