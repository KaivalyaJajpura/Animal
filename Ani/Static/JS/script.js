/* ================================
   SHARED SCRIPT FOR ALL PAGES
   ================================ */

// Get current page name from filename
function getCurrentPage() {
    const path = window.location.pathname;
    return path.split('/').pop() || 'index.html';
}

/* ================================
   COMMON VALIDATION FUNCTIONS
   ================================ */

// Email validation regex
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateEmail(email) {
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function validatePasswordMatch(password, confirmPassword) {
    return password === confirmPassword;
}

/* ================================
   PASSWORD VISIBILITY TOGGLE
   ================================ */

function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('#togglePassword');
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling || this.parentElement.querySelector('input[type="password"], input[type="text"]');
            const eyeIcon = this.querySelector('#eyeIcon') || this.querySelector('.material-symbols-outlined');
            
            if (!input) return;
            
            if (input.type === 'password') {
                input.type = 'text';
                if (eyeIcon) eyeIcon.textContent = 'visibility_off';
            } else {
                input.type = 'password';
                if (eyeIcon) eyeIcon.textContent = 'visibility';
            }
        });
    });
}

/* ================================
   FORM VALIDATION
   ================================ */

function setupFormValidation() {
    const loginForm = document.querySelector('form');
    if (!loginForm) return;
    
    const emailInput = document.getElementById('emailInput');
    const passwordInput = document.getElementById('passwordInput');
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    
    const validateForm = () => {
        if (!submitBtn) return;
        
        const isEmailValid = emailInput ? validateEmail(emailInput.value) : true;
        const isPasswordValid = passwordInput ? validatePassword(passwordInput.value) : true;
        
        submitBtn.disabled = !(isEmailValid && isPasswordValid);
    };
    
    if (emailInput) {
        emailInput.addEventListener('input', validateForm);
        emailInput.addEventListener('blur', function() {
            const error = document.getElementById('emailError');
            if (error) {
                error.classList.toggle('hidden', validateEmail(this.value));
            }
        });
    }
    
    if (passwordInput) {
        passwordInput.addEventListener('input', validateForm);
    }
    
    validateForm();
}

/* ================================
   SIGNUP FORM VALIDATION
   ================================ */

function setupSignupValidation() {
    const signupForm = document.querySelector('form');
    if (!signupForm) return;
    
    const inputs = signupForm.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
    const submitBtn = signupForm.querySelector('button[type="submit"]');
    
    const validateSignupForm = () => {
        if (!submitBtn) return;
        
        let isValid = true;
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
            }
        });
        
        const passwordInput = document.getElementById('passwordInput');
        const confirmPasswordInput = document.getElementById('confirmPasswordInput');
        if (passwordInput && confirmPasswordInput) {
            if (!validatePasswordMatch(passwordInput.value, confirmPasswordInput.value)) {
                isValid = false;
            }
        }
        
        submitBtn.disabled = !isValid;
    };
    
    inputs.forEach(input => {
        input.addEventListener('input', validateSignupForm);
    });
    
    validateSignupForm();
}

/* ================================
   DROPDOWN AND SELECT HANDLING
   ================================ */

function setupDropdownToggle() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-dropdown-toggle');
            const dropdown = document.getElementById(targetId);
            
            if (dropdown) {
                dropdown.classList.toggle('hidden');
            }
        });
    });
    
    document.addEventListener('click', function(e) {
        dropdownToggles.forEach(toggle => {
            const dropdown = document.getElementById(toggle.getAttribute('data-dropdown-toggle'));
            if (dropdown && !toggle.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
    });
}

/* ================================
   FILTER FUNCTIONALITY
   ================================ */

function setupFilterSelect(selectId, filterFunction) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    select.addEventListener('change', function() {
        const selectedValue = this.value;
        if (filterFunction && typeof filterFunction === 'function') {
            filterFunction(selectedValue);
        }
    });
}

/* ================================
   TABLE FILTERING AND SEARCH
   ================================ */

function setupTableSearch(searchInputId, tableId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

/* ================================
   DASHBOARD SPECIFIC FUNCTIONS
   ================================ */

// Animal data for dashboard
const animalData = [
    // Healthy Animals
    {
        id: '#C-101',
        species: 'Cow (Holstein)',
        status: 'Healthy',
        healthIndex: 98,
        temperature: 38.5,
        heartRate: 72,
        movement: 'Active',
        bp: '120/80',
        readings: [
            { time: 'Just now', temp: 38.5, hr: 72, bp: '120/80', movement: 'Active', health: 98 },
            { time: '1 hour ago', temp: 38.4, hr: 71, bp: '119/79', movement: 'Active', health: 97 },
            { time: '2 hours ago', temp: 38.6, hr: 73, bp: '121/81', movement: 'Active', health: 98 },
            { time: '3 hours ago', temp: 38.5, hr: 72, bp: '120/80', movement: 'Resting', health: 96 },
            { time: '4 hours ago', temp: 38.3, hr: 70, bp: '118/78', movement: 'Normal', health: 99 }
        ]
    },
    {
        id: '#G-056',
        species: 'Goat (Boer)',
        status: 'Healthy',
        healthIndex: 92,
        temperature: 39.0,
        heartRate: 78,
        movement: 'Normal',
        bp: '122/82',
        readings: [
            { time: 'Just now', temp: 39.0, hr: 78, bp: '122/82', movement: 'Normal', health: 92 },
            { time: '1 hour ago', temp: 38.9, hr: 77, bp: '121/81', movement: 'Normal', health: 91 },
            { time: '2 hours ago', temp: 39.1, hr: 79, bp: '123/83', movement: 'Active', health: 93 },
            { time: '3 hours ago', temp: 39.0, hr: 78, bp: '122/82', movement: 'Normal', health: 92 },
            { time: '4 hours ago', temp: 38.8, hr: 76, bp: '120/80', movement: 'Resting', health: 94 }
        ]
    },
    {
        id: '#S-203',
        species: 'Sheep (Merino)',
        status: 'Healthy',
        healthIndex: 95,
        temperature: 39.1,
        heartRate: 75,
        movement: 'Resting',
        bp: '121/81',
        readings: [
            { time: 'Just now', temp: 39.1, hr: 75, bp: '121/81', movement: 'Resting', health: 95 },
            { time: '1 hour ago', temp: 39.0, hr: 74, bp: '120/80', movement: 'Normal', health: 96 },
            { time: '2 hours ago', temp: 39.2, hr: 76, bp: '122/82', movement: 'Resting', health: 94 },
            { time: '3 hours ago', temp: 39.1, hr: 75, bp: '121/81', movement: 'Resting', health: 95 },
            { time: '4 hours ago', temp: 38.9, hr: 73, bp: '119/79', movement: 'Resting', health: 97 }
        ]
    },
    // Warning Animals
    {
        id: '#C-102',
        species: 'Cow (Jersey)',
        status: 'Warning',
        healthIndex: 75,
        temperature: 39.2,
        heartRate: 85,
        movement: 'Low',
        bp: '125/85',
        readings: [
            { time: 'Just now', temp: 39.2, hr: 85, bp: '125/85', movement: 'Low', health: 75 },
            { time: '1 hour ago', temp: 39.1, hr: 84, bp: '124/84', movement: 'Low', health: 76 },
            { time: '2 hours ago', temp: 39.3, hr: 86, bp: '126/86', movement: 'Resting', health: 74 },
            { time: '3 hours ago', temp: 39.0, hr: 83, bp: '123/83', movement: 'Low', health: 77 },
            { time: '4 hours ago', temp: 39.2, hr: 85, bp: '125/85', movement: 'Low', health: 75 }
        ]
    },
    {
        id: '#P-089',
        species: 'Buffalo (Water)',
        status: 'Warning',
        healthIndex: 78,
        temperature: 39.4,
        heartRate: 88,
        movement: 'Low',
        bp: '128/88',
        readings: [
            { time: 'Just now', temp: 39.4, hr: 88, bp: '128/88', movement: 'Low', health: 78 },
            { time: '1 hour ago', temp: 39.3, hr: 87, bp: '127/87', movement: 'Resting', health: 79 },
            { time: '2 hours ago', temp: 39.5, hr: 89, bp: '129/89', movement: 'Low', health: 77 },
            { time: '3 hours ago', temp: 39.2, hr: 86, bp: '126/86', movement: 'Resting', health: 80 },
            { time: '4 hours ago', temp: 39.4, hr: 88, bp: '128/88', movement: 'Low', health: 78 }
        ]
    },
    // Critical Animals
    {
        id: '#C-103',
        species: 'Cow (Angus)',
        status: 'Critical',
        healthIndex: 45,
        temperature: 40.2,
        heartRate: 105,
        movement: 'Inactive',
        bp: '135/95',
        readings: [
            { time: 'Just now', temp: 40.2, hr: 105, bp: '135/95', movement: 'Inactive', health: 45 },
            { time: '1 hour ago', temp: 40.0, hr: 102, bp: '133/93', movement: 'Inactive', health: 48 },
            { time: '2 hours ago', temp: 40.3, hr: 107, bp: '137/97', movement: 'Lying down', health: 42 },
            { time: '3 hours ago', temp: 39.8, hr: 100, bp: '130/90', movement: 'Inactive', health: 50 },
            { time: '4 hours ago', temp: 40.1, hr: 104, bp: '134/94', movement: 'Lying down', health: 46 }
        ]
    },
    {
        id: '#H-067',
        species: 'Horse (Arabian)',
        status: 'Critical',
        healthIndex: 52,
        temperature: 40.5,
        heartRate: 110,
        movement: 'Inactive',
        bp: '138/98',
        readings: [
            { time: 'Just now', temp: 40.5, hr: 110, bp: '138/98', movement: 'Inactive', health: 52 },
            { time: '1 hour ago', temp: 40.3, hr: 108, bp: '136/96', movement: 'Lying down', health: 54 },
            { time: '2 hours ago', temp: 40.6, hr: 112, bp: '140/100', movement: 'Inactive', health: 50 },
            { time: '3 hours ago', temp: 40.2, hr: 106, bp: '134/94', movement: 'Lying down', health: 56 },
            { time: '4 hours ago', temp: 40.4, hr: 109, bp: '137/97', movement: 'Inactive', health: 53 }
        ]
    }
];

let currentAnimalIndex = 0;

// Function to get situation based on health index
function getSituation(health) {
    if (health >= 90) return 'Healthy';
    if (health >= 70) return 'Warning';
    return 'Critical';
}

// Function to get color based on health index
function getHealthColor(health) {
    if (health >= 90) return { bar: 'bg-green-500', text: 'text-green-600' };
    if (health >= 70) return { bar: 'bg-yellow-500', text: 'text-yellow-600' };
    return { bar: 'bg-red-500', text: 'text-red-600' };
}

// Function to get situation badge color
function getSituationBadgeColor(situation) {
    if (situation === 'Healthy') return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    if (situation === 'Warning') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
}

// Function to update the display with current animal data
function updateAnimalDisplay(animalIdOrIndex = null) {
    let animal;
    
    if (animalIdOrIndex !== null && typeof animalIdOrIndex === 'string') {
        // Find animal by ID
        animal = animalData.find(a => a.id === '#' + animalIdOrIndex || a.id === animalIdOrIndex);
    } else if (typeof animalIdOrIndex === 'number') {
        // Use index
        animal = animalData[animalIdOrIndex];
    } else {
        // Use current index (auto-cycle)
        animal = animalData[currentAnimalIndex];
        currentAnimalIndex = (currentAnimalIndex + 1) % animalData.length;
    }
    
    console.log('Updating display for animal:', animal.id);
    
    // Update biometric stat cards
    const hrValue = document.getElementById('hrValue');
    const bpValue = document.getElementById('bpValue');
    const movementValue = document.getElementById('movementValue');
    const tempValue = document.getElementById('tempValue');
    const tempAvg = document.getElementById('tempAvg');
    
    if (hrValue) hrValue.textContent = animal.heartRate + ' bpm';
    if (bpValue) bpValue.textContent = animal.bp;
    if (movementValue) movementValue.textContent = animal.movement;
    if (tempValue) tempValue.innerHTML = animal.temperature.toFixed(1) + ' <span class="text-lg font-normal text-gray-400">°C</span>';
    if (tempAvg) tempAvg.textContent = 'Avg: ' + (animal.temperature - 0.3).toFixed(1) + '°C today';
    
    // Update status badges
    const tempStatus = document.getElementById('tempStatus');
    const bpStatus = document.getElementById('bpStatus');
    const movementStatus = document.getElementById('movementStatus');
    
    if (tempStatus) tempStatus.textContent = animal.temperature <= 38.8 ? 'Stable' : animal.temperature <= 39.5 ? 'Elevated' : 'High';
    if (bpStatus) bpStatus.textContent = 'Normal';
    if (movementStatus) movementStatus.textContent = animal.movement;
    
    // Update animal identity and vital signs in Live Health Status
    const animalId = document.getElementById('animalId');
    const animalSpecies = document.getElementById('animalSpecies');
    const temperature = document.getElementById('temperature');
    const heartRate = document.getElementById('heartRate');
    
    if (animalId) animalId.textContent = animal.id;
    if (animalSpecies) animalSpecies.textContent = animal.species;
    if (temperature) temperature.textContent = animal.temperature + '°C';
    if (heartRate) heartRate.textContent = animal.heartRate + ' bpm';
    
    // Update health status
    const healthStatus = document.getElementById('healthStatus');
    const situation = getSituation(animal.healthIndex);
    if (healthStatus) {
        healthStatus.textContent = situation;
        const statusColor = situation === 'Healthy' 
            ? 'text-green-600' 
            : situation === 'Warning'
            ? 'text-yellow-600'
            : 'text-red-600';
        healthStatus.className = `text-lg font-bold ${statusColor}`;
    }
    
    // Update health index
    const healthIndexElem = document.getElementById('healthIndex');
    if (healthIndexElem) {
        healthIndexElem.textContent = animal.healthIndex + '%';
        const healthColor = getHealthColor(animal.healthIndex);
        healthIndexElem.className = `text-lg font-bold ${healthColor.text}`;
    }
    
    // Update last update time
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
        const now = new Date();
        lastUpdate.textContent = now.toLocaleTimeString();
    }
    
    // Update Health Summary based on selected animal
    updateHealthSummary(animal);
    
    // Update table with readings
    const tableBody = document.getElementById('readingsTable');
    if (tableBody) {
        tableBody.innerHTML = '';
        
        animal.readings.forEach(reading => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors';
            
            const situation = getSituation(reading.health);
            const healthColor = getHealthColor(reading.health);
            const badgeColor = getSituationBadgeColor(situation);
            
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-700 dark:text-gray-300">${reading.time}</td>
                <td class="px-6 py-4 font-mono text-gray-700 dark:text-gray-300">${reading.temp}°C</td>
                <td class="px-6 py-4 font-mono text-gray-700 dark:text-gray-300">${reading.hr} bpm</td>
                <td class="px-6 py-4 font-mono text-gray-700 dark:text-gray-300">${reading.bp}</td>
                <td class="px-6 py-4 text-gray-700 dark:text-gray-300">${reading.movement}</td>
                <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                        <div class="w-12 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div class="h-full ${healthColor.bar}" style="width: ${reading.health}%"></div>
                        </div>
                        <span class="font-bold ${healthColor.text}">${reading.health}%</span>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${badgeColor}">
                        ${situation}
                    </span>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
}

// Function to update Health Summary box based on selected animal
function updateHealthSummary(animal) {
    const healthSummary = document.querySelector('.bg-primary');
    const bookAppointmentContainer = document.getElementById('bookAppointmentContainer');
    
    if (healthSummary) {
        const situation = getSituation(animal.healthIndex);
        const summaryText = situation === 'Healthy' 
            ? `Overall animal is in excellent health. All vital signs are within normal parameters.`
            : situation === 'Warning'
            ? `This animal requires attention. Some vital signs are elevated and should be monitored.`
            : `This animal is in critical condition. Immediate veterinary care is required.`;
        
        // Update summary text
        const summaryTextElem = healthSummary.querySelector('p:nth-of-type(2)');
        if (summaryTextElem) {
            summaryTextElem.textContent = summaryText;
        }
        
        // Update status indicators
        const statusDivs = healthSummary.querySelectorAll('.bg-white\\/20');
        if (statusDivs.length >= 3) {
            // For single animal view, show the key metrics
            statusDivs[0].innerHTML = '<span class="text-sm font-bold">Temperature</span><span class="text-lg font-bold">' + animal.temperature + '°C</span>';
            statusDivs[1].innerHTML = '<span class="text-sm font-bold">Heart Rate</span><span class="text-lg font-bold">' + animal.heartRate + ' bpm</span>';
            statusDivs[2].innerHTML = '<span class="text-sm font-bold">Health Index</span><span class="text-lg font-bold">' + animal.healthIndex + '%</span>';
        }
    }
    
    // Show or hide Book Appointment button based on health status
    if (bookAppointmentContainer) {
        const situation = getSituation(animal.healthIndex);
        if (situation === 'Warning' || situation === 'Critical') {
            bookAppointmentContainer.classList.remove('hidden');
        } else {
            bookAppointmentContainer.classList.add('hidden');
        }
    }
}

// Update trend chart based on selected period
// NOTE: This function is now overridden by real data loading in dashboard.html
// Keeping this as fallback for non-dashboard pages
function updateTrendChart(period) {
    const chartSvg = document.getElementById('trendChart');
    const xAxisLabels = document.getElementById('xAxisLabels');
    
    if (!chartSvg || !xAxisLabels) return;
    
    // Check if loadTrendData function exists (real data loader from dashboard.html)
    if (typeof loadTrendData === 'function') {
        // Let the dashboard handle it with real data
        return;
    }
    
    // Fallback static charts for non-dashboard pages
    if (period === '7days') {
        // 7 days view
        chartSvg.innerHTML = `
            <path d="M0 70 Q 10 65 20 50 T 40 45 T 60 30 T 80 40 T 100 20" fill="none" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke"></path>
            <defs>
            <lineargradient id="gradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#13ec5b" stop-opacity="0.5"></stop>
            <stop offset="100%" stop-color="#13ec5b" stop-opacity="0"></stop>
            </lineargradient>
            </defs>
            <path d="M0 70 Q 10 65 20 50 T 40 45 T 60 30 T 80 40 T 100 20 V 100 H 0 Z" fill="url(#gradient)" opacity="0.2" stroke="none"></path>
        `;
        xAxisLabels.innerHTML = `<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>`;
    } else if (period === '1month') {
        // 1 month view with different curve
        chartSvg.innerHTML = `
            <path d="M0 75 Q 5 70 10 65 Q 15 60 20 55 Q 25 48 30 52 Q 35 45 40 40 Q 45 35 50 38 Q 55 32 60 28 Q 65 25 70 30 Q 75 22 80 25 Q 85 20 90 18 Q 95 15 100 10" fill="none" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke"></path>
            <defs>
            <lineargradient id="gradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#13ec5b" stop-opacity="0.5"></stop>
            <stop offset="100%" stop-color="#13ec5b" stop-opacity="0"></stop>
            </lineargradient>
            </defs>
            <path d="M0 75 Q 5 70 10 65 Q 15 60 20 55 Q 25 48 30 52 Q 35 45 40 40 Q 45 35 50 38 Q 55 32 60 28 Q 65 25 70 30 Q 75 22 80 25 Q 85 20 90 18 Q 95 15 100 10 V 100 H 0 Z" fill="url(#gradient)" opacity="0.2" stroke="none"></path>
        `;
        xAxisLabels.innerHTML = `<span>Week 1</span><span>Week 2</span><span>Week 3</span><span>Week 4</span>`;
    }
}

/* ================================
   DASHBOARD SPECIFIC FUNCTIONS
   ================================ */

/* ================================
   VET SETTINGS SPECIFIC
   ================================ */

function setupAudibleAlertsSlider() {
    const slider = document.querySelector('.slider');
    if (!slider) return;
    
    slider.addEventListener('input', function() {
        const value = (this.value - this.min) / (this.max - this.min) * 100;
        this.style.setProperty('--value', value + '%');
        
        // Update display if it exists
        const display = this.parentElement?.querySelector('[data-display]');
        if (display) {
            display.textContent = this.value + '%';
        }
    });
    
    // Initialize
    const initialValue = (slider.value - slider.min) / (slider.max - slider.min) * 100;
    slider.style.setProperty('--value', initialValue + '%');
}

function setupRadioOptions() {
    const radioOptions = document.querySelectorAll('.radio-option input[type="radio"]');
    
    radioOptions.forEach(radio => {
        radio.addEventListener('change', function() {
            // Handle radio option change
            const radioGroup = this.name;
            const radios = document.querySelectorAll(`input[name="${radioGroup}"]`);
            
            radios.forEach(r => {
                const label = r.nextElementSibling;
                if (label && label.tagName === 'LABEL') {
                    if (r.checked) {
                        label.classList.add('active');
                    } else {
                        label.classList.remove('active');
                    }
                }
            });
        });
    });
}

/* ================================
   DASHBOARD FILTERS AND CHARTS
   ================================ */

function setupDashboardFilters() {
    const petFilter = document.getElementById('petFilter');
    if (!petFilter) return;
    
    petFilter.addEventListener('change', function() {
        const selectedValue = this.value;
        if (selectedValue === 'all') {
            // Auto-cycle through animals
            updateAnimalDisplay();
        } else {
            // Show selected animal
            updateAnimalDisplay(selectedValue);
        }
    });
}

function setupTrendChartButtons() {
    const trend7days = document.getElementById('trend7days');
    const trend1month = document.getElementById('trend1month');
    
    // If these buttons don't exist or we're on the dashboard (which handles its own buttons), skip
    if (!trend7days || !trend1month) return;
    
    // Check if loadTrendData exists (dashboard page has its own handler via onclick)
    if (typeof loadTrendData === 'function') {
        // Dashboard handles its own trend buttons, don't attach duplicate listeners
        return;
    }
    
    trend7days.addEventListener('click', function(e) {
        e.preventDefault();
        trend7days.classList.add('bg-white', 'dark:bg-gray-600', 'font-bold', 'shadow-sm');
        trend7days.classList.remove('font-medium', 'text-gray-500', 'dark:text-gray-400');
        
        trend1month.classList.remove('bg-white', 'dark:bg-gray-600', 'font-bold', 'shadow-sm');
        trend1month.classList.add('font-medium', 'text-gray-500', 'dark:text-gray-400');
        
        updateTrendChart('7days');
    });
    
    trend1month.addEventListener('click', function(e) {
        e.preventDefault();
        trend1month.classList.add('bg-white', 'dark:bg-gray-600', 'font-bold', 'shadow-sm');
        trend1month.classList.remove('font-medium', 'text-gray-500', 'dark:text-gray-400');
        
        trend7days.classList.remove('bg-white', 'dark:bg-gray-600', 'font-bold', 'shadow-sm');
        trend7days.classList.add('font-medium', 'text-gray-500', 'dark:text-gray-400');
        
        updateTrendChart('1month');
    });
}

/* ================================
   THEME TOGGLE
   ================================ */

function setupThemeToggle() {
    const htmlElement = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    if (savedTheme === 'dark') {
        htmlElement.classList.add('dark');
    } else {
        htmlElement.classList.remove('dark');
    }
    
    const themeToggle = document.querySelector('[data-theme-toggle]');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            if (htmlElement.classList.contains('dark')) {
                htmlElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            } else {
                htmlElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }
        });
    }
}

/* ================================
   INITIALIZATION
   ================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Setup common features
    setupPasswordToggle();
    setupFormValidation();
    setupSignupValidation();
    setupDropdownToggle();
    setupThemeToggle();
    
    // Page-specific setup
    const currentPage = getCurrentPage();
    
    if (currentPage.includes('dashboard') && !currentPage.includes('vet')) {
        setupDashboardFilters();
        setupTrendChartButtons();
        // NOTE: Dashboard display is now handled by inline JavaScript in dashboard.html
        // which loads real data from the database for the logged-in user's animals.
        // The mock data functions (updateAnimalDisplay) are no longer used here.
        
        // Check if there's a filter parameter in the URL
        const urlParams = new URLSearchParams(window.location.search);
        const filterParam = urlParams.get('filter');
        if (filterParam) {
            const filterSelect = document.getElementById('petFilter');
            if (filterSelect) {
                filterSelect.value = filterParam;
                filterSelect.dispatchEvent(new Event('change'));
            }
        }
    }
    
    if (currentPage.includes('vet-settings')) {
        setupAudibleAlertsSlider();
        setupRadioOptions();
    }
    
    if (currentPage.includes('history') || currentPage.includes('vet-history')) {
        setupTableSearch('searchInput', 'table');
    }
});

// Utility function to show toast notifications
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white font-medium ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    }`;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function for throttling
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Local storage helper
const storage = {
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
    get: (key) => JSON.parse(localStorage.getItem(key)),
    remove: (key) => localStorage.removeItem(key),
    clear: () => localStorage.clear()
};

// Export functions for global access
window.showToast = showToast;
window.debounce = debounce;
window.throttle = throttle;
window.storage = storage;
window.getCurrentPage = getCurrentPage;
