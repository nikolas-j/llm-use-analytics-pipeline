// API Configuration
const API_BASE_URL = 'https://XXXXXXXXX.execute-api.eu-north-1.amazonaws.com';

// DOM Elements
const dateInput = document.getElementById('date-input');
const metricsBtn = document.getElementById('metrics-btn');
const reportsBtn = document.getElementById('reports-btn');
const clearBtn = document.getElementById('clear-btn');
const resultsElement = document.getElementById('results');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');

// Event Listeners
metricsBtn.addEventListener('click', () => fetchData('/v1/metrics'));
reportsBtn.addEventListener('click', () => fetchData('/v1/reports'));
clearBtn.addEventListener('click', clearResults);

// Fetch data from API
async function fetchData(endpoint) {
    const date = dateInput.value;
    
    if (!date) {
        showError('Please select a date');
        return;
    }
    
    // Clear previous results and errors
    clearResults();
    showLoading(true);
    
    // Disable buttons during fetch
    toggleButtons(false);
    
    try {
        const url = `${API_BASE_URL}${endpoint}?date=${date}`;
        console.log('Fetching:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        displayResults(data, endpoint);
        
    } catch (error) {
        console.error('Error fetching data:', error);
        showError(`Failed to fetch data: ${error.message}`);
    } finally {
        showLoading(false);
        toggleButtons(true);
    }
}

// Display results in the results section
function displayResults(data, endpoint) {
    const endpointName = endpoint.split('/').pop();
    const header = `=== ${endpointName.toUpperCase()} (Date: ${dateInput.value}) ===\n\n`;
    resultsElement.textContent = header + JSON.stringify(data, null, 2);
}

// Show/hide loading indicator
function showLoading(show) {
    if (show) {
        loadingElement.classList.remove('hidden');
    } else {
        loadingElement.classList.add('hidden');
    }
}

// Show error message
function showError(message) {
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
}

// Clear results and errors
function clearResults() {
    resultsElement.textContent = '';
    errorElement.classList.add('hidden');
    errorElement.textContent = '';
}

// Enable/disable action buttons
function toggleButtons(enabled) {
    metricsBtn.disabled = !enabled;
    reportsBtn.disabled = !enabled;
}

// Initialize with today's date if none is set
document.addEventListener('DOMContentLoaded', () => {
    if (!dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});
