// API Configuration
// Automatically detects environment and uses the correct API URL
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://arrivapp.onrender.com';

console.log('API URL:', API_BASE_URL);
