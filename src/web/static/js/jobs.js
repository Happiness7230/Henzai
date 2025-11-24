/**
 * Job Search Page Logic
 */

let currentPage = 1;
let allJobs = [];
let currentFilters = {
    q: '',
    location: '',
    jobType: [],
    experienceLevel: '',
    remote: false,
    hybrid: false,
    minSalary: null,
    maxSalary: null,
    datePosted: ''
};
let pageSize = 12;
let selectedJob = null;
let currentSort = 'relevance';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadJobAlerts();
    
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        document.getElementById('darkModeBtn').querySelector('i').classList.replace('fa-moon', 'fa-sun');
    }
});

function setupEventListeners() {
    // Search form
    const searchForm = document.getElementById('jobSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            performJobSearch();
        });
    }

    // Filter listeners
    document.getElementById('resetFilters')?.addEventListener('click', resetFilters);
    document.getElementById('sortBy')?.addEventListener('change', (e) => {
        currentSort = e.target.value;
        sortJobs();
        displayJobs();
    });

    // Modal controls
    document.getElementById('closeJobModal')?.addEventListener('click', () => {
        document.getElementById('jobModal').classList.add('hidden');
    });

    document.getElementById('jobModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'jobModal') {
            document.getElementById('jobModal').classList.add('hidden');
        }
    });

    // Alert modal
    document.getElementById('closeAlertModal')?.addEventListener('click', () => {
        document.getElementById('jobAlertModal').classList.add('hidden');
    });

    document.getElementById('cancelAlert')?.addEventListener('click', () => {
        document.getElementById('jobAlertModal').classList.add('hidden');
    });

    document.getElementById('createAlert')?.addEventListener('click', createJobAlert);

    // Alerts button
    document.getElementById('alertsBtn')?.addEventListener('click', showAlertsList);

    // Dark mode toggle
    document.getElementById('darkModeBtn')?.addEventListener('click', toggleDarkMode);

    // Pagination
    document.getElementById('prevPage')?.addEventListener('click', previousPage);
    document.getElementById('nextPage')?.addEventListener('click', nextPage);
}

async function performJobSearch() {
    const query = document.getElementById('jobTitle')?.value.trim() || '';
    const location = document.getElementById('jobLocation')?.value.trim() || '';

    if (!query) {
        Utils.showToast('Please enter a job title or keywords', 'warning');
        return;
    }

    // Update filters
    currentFilters.q = query;
    currentFilters.location = location;
    currentFilters.jobType = Array.from(document.querySelectorAll('input[name="jobType"]:checked')).map(cb => cb.value);
    currentFilters.experienceLevel = document.getElementById('experienceLevel')?.value || '';
    currentFilters.remote = document.getElementById('remoteOnly')?.checked || false;
    currentFilters.hybrid = document.getElementById('hybridOk')?.checked || false;
    currentFilters.minSalary = parseInt(document.getElementById('minSalary')?.value) || null;
    currentFilters.maxSalary = parseInt(document.getElementById('maxSalary')?.value) || null;
    currentFilters.datePosted = document.getElementById('datePosted')?.value || '';

    showLoading();
    currentPage = 1;

    try {
        const response = await fetch('/api/jobs/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                q: currentFilters.q,
                location: currentFilters.location,
                job_type: currentFilters.jobType.length > 0 ? currentFilters.jobType : undefined,
                experience_level: currentFilters.experienceLevel || undefined,
                remote_only: currentFilters.remote,
                min_salary: currentFilters.minSalary,
                max_salary: currentFilters.maxSalary,
                max_results: 30
            })
        });

        if (!response.ok) {
            throw new Error('HTTP ' + response.status);
        }

        const data = await response.json();

        if (data.status === 'success') {
            allJobs = data.data.results || [];
            sortJobs();
            displayJobs();
            updateResultsInfo();
        } else {
            throw new Error(data.error || 'Search failed');
        }

    } catch (error) {
        console.error('Job search error:', error);
        Utils.showToast('Search failed: ' + error.message, 'error');
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function sortJobs() {
    switch (currentSort) {
        case 'date':
            allJobs.sort((a, b) => new Date(b.date_posted || 0) - new Date(a.date_posted || 0));
            break;
        case 'salary':
            allJobs.sort((a, b) => (b.salary_max || 0) - (a.salary_max || 0));
            break;
        case 'company':
            allJobs.sort((a, b) => (a.company || '').localeCompare(b.company || ''));
            break;
        case 'relevance':
        default:
            // Keep original order (API sorted by relevance)
            break;
    }
}

function displayJobs() {
    const grid = document.getElementById('jobsGrid');
    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = startIdx + pageSize;
    const paginatedJobs = allJobs.slice(startIdx, endIdx);

    if (!paginatedJobs || paginatedJobs.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-briefcase"></i>
                <h3>No jobs found</h3>
                <p>Try adjusting your search filters or keywords</p>
            </div>
        `;
        hidePagination();
        return;
    }

    grid.innerHTML = '';
    paginatedJobs.forEach(job => {
        const card = createJobCard(job);
        grid.appendChild(card);
    });

    // Show pagination if needed
    if (allJobs.length > pageSize) {
        showPagination();
    } else {
        hidePagination();
    }
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';

    const salary = job.salary_min && job.salary_max
        ? `$${(job.salary_min / 1000).toFixed(0)}k - $${(job.salary_max / 1000).toFixed(0)}k`
        : job.salary_max
        ? `$${(job.salary_max / 1000).toFixed(0)}k+`
        : 'Competitive';

    let metaHtml = `
        <div class="job-meta-item">
            <i class="fas fa-map-marker-alt"></i>
            <span>${escapeHtml(job.location || 'Remote')}</span>
        </div>
        <div class="job-meta-item">
            <i class="fas fa-briefcase"></i>
            <span>${escapeHtml(job.job_type || 'Full-time')}</span>
        </div>
        <div class="job-meta-item job-salary">
            <i class="fas fa-dollar-sign"></i>
            <span>${salary}</span>
        </div>
    `;

    if (job.date_posted) {
        metaHtml += `
            <div class="job-meta-item">
                <i class="fas fa-calendar"></i>
                <span>${formatDate(job.date_posted)}</span>
            </div>
        `;
    }

    let tagsHtml = '';
    if (job.tags && Array.isArray(job.tags)) {
        tagsHtml = `
            <div class="job-tags">
                ${job.tags.slice(0, 3).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        `;
    }

    card.innerHTML = `
        <div class="job-info">
            <h3 class="job-title" onclick="viewJobDetails('${escapeAttr(job.id)}')">
                ${escapeHtml(job.title || 'Job Title')}
            </h3>
            <div class="job-company">
                <i class="fas fa-building"></i>
                <span>${escapeHtml(job.company || 'Company')}</span>
            </div>
            <div class="job-meta">
                ${metaHtml}
            </div>
            ${tagsHtml}
        </div>
        <div class="job-actions">
            <a href="${escapeAttr(job.url || '#')}" target="_blank" class="btn btn-primary btn-sm">
                <i class="fas fa-external-link-alt"></i> Apply
            </a>
            <button class="btn-icon" onclick="saveJob('${escapeAttr(job.id)}')" title="Save job">
                <i class="far fa-bookmark"></i>
            </button>
            <button class="btn-icon" onclick="showJobAlert('${escapeAttr(job.id)}', '${escapeAttr(job.title)}', '${escapeAttr(job.company)}')" title="Create alert">
                <i class="fas fa-bell"></i>
            </button>
        </div>
    `;

    return card;
}

function viewJobDetails(jobId) {
    const job = allJobs.find(j => j.id === jobId);
    if (!job) return;

    selectedJob = job;

    const salary = job.salary_min && job.salary_max
        ? `$${(job.salary_min / 1000).toFixed(0)}k - $${(job.salary_max / 1000).toFixed(0)}k`
        : job.salary_max
        ? `$${(job.salary_max / 1000).toFixed(0)}k+`
        : 'Competitive';

    let detailsHtml = `
        <h2>${escapeHtml(job.title)}</h2>
        <div class="job-meta">
            <div class="job-meta-item">
                <i class="fas fa-building"></i>
                <strong>${escapeHtml(job.company)}</strong>
            </div>
            <div class="job-meta-item">
                <i class="fas fa-map-marker-alt"></i>
                <span>${escapeHtml(job.location)}</span>
            </div>
            <div class="job-meta-item">
                <i class="fas fa-briefcase"></i>
                <span>${escapeHtml(job.job_type)}</span>
            </div>
            <div class="job-meta-item job-salary">
                <i class="fas fa-dollar-sign"></i>
                <span>${salary}</span>
            </div>
        </div>

        <hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-color);">

        <h3>Job Description</h3>
        <p>${escapeHtml(job.description || 'No description available')}</p>

        ${job.requirements ? `
            <h3>Requirements</h3>
            <ul>
                ${job.requirements.map(req => `<li>${escapeHtml(req)}</li>`).join('')}
            </ul>
        ` : ''}

        ${job.benefits ? `
            <h3>Benefits</h3>
            <ul>
                ${job.benefits.map(benefit => `<li>${escapeHtml(benefit)}</li>`).join('')}
            </ul>
        ` : ''}
    `;

    document.getElementById('jobModalBody').innerHTML = detailsHtml;
    document.getElementById('jobApplyLink').href = job.url || '#';
    document.getElementById('jobModal').classList.remove('hidden');
}

function showJobAlert(jobId, jobTitle, company) {
    document.getElementById('alertKeywords').textContent = `${escapeHtml(jobTitle)} at ${escapeHtml(company)}`;
    document.getElementById('jobAlertModal').classList.remove('hidden');
}

async function createJobAlert() {
    const email = document.getElementById('alertEmail')?.value.trim();
    const alertName = document.getElementById('alertName')?.value.trim();
    const frequency = document.getElementById('alertFrequency')?.value || 'daily';

    if (!email || !Utils.isValidEmail(email)) {
        Utils.showToast('Please enter a valid email', 'error');
        return;
    }

    if (!alertName) {
        Utils.showToast('Please enter an alert name', 'error');
        return;
    }

    Utils.showLoading();

    try {
        const response = await fetch('/api/jobs/alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                keywords: currentFilters.q,
                location: currentFilters.location,
                remote_only: currentFilters.remote,
                min_salary: currentFilters.minSalary
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            Utils.showToast('✓ Job alert created! You\'ll receive updates.', 'success', 5000);
            document.getElementById('jobAlertModal').classList.add('hidden');
            document.getElementById('alertEmail').value = '';
            document.getElementById('alertName').value = '';
            loadJobAlerts();
        } else {
            Utils.showToast('Failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Alert creation error:', error);
        Utils.showToast('Failed to create alert: ' + error.message, 'error');
    } finally {
        Utils.hideLoading();
    }
}

async function loadJobAlerts() {
    try {
        const email = localStorage.getItem('userEmail');
        if (!email) return;

        const response = await fetch(`/api/jobs/alerts?email=${encodeURIComponent(email)}`);
        const data = await response.json();

        if (data.status === 'success') {
            const alerts = data.data || [];
            document.getElementById('alertCount').textContent = alerts.length;
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function showAlertsList() {
    const alertsList = document.getElementById('alertsList');
    // This would be populated with actual alerts from the API
    alertsList.innerHTML = '<p class="empty-state">No alerts configured yet</p>';
    document.getElementById('alertsListModal').classList.remove('hidden');
}

document.getElementById('closeAlertsModal')?.addEventListener('click', () => {
    document.getElementById('alertsListModal').classList.add('hidden');
});

function saveJob(jobId) {
    const job = allJobs.find(j => j.id === jobId);
    if (!job) return;

    let saved = JSON.parse(localStorage.getItem('savedJobs') || '[]');
    const index = saved.findIndex(j => j.id === jobId);

    if (index > -1) {
        saved.splice(index, 1);
        Utils.showToast('Job removed from saved', 'info');
    } else {
        saved.push(job);
        Utils.showToast('Job saved!', 'success');
    }

    localStorage.setItem('savedJobs', JSON.stringify(saved));
}

function resetFilters() {
    document.getElementById('jobTitle').value = '';
    document.getElementById('jobLocation').value = '';
    document.querySelectorAll('input[name="jobType"]').forEach(cb => cb.checked = false);
    document.getElementById('experienceLevel').value = '';
    document.getElementById('remoteOnly').checked = false;
    document.getElementById('hybridOk').checked = false;
    document.getElementById('minSalary').value = '';
    document.getElementById('maxSalary').value = '';
    document.getElementById('datePosted').value = '';
    
    currentPage = 1;
    allJobs = [];
    document.getElementById('jobsGrid').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-briefcase"></i>
            <h3>Filters Reset</h3>
            <p>Enter search terms to get started</p>
        </div>
    `;
    hidePagination();
}

function updateResultsInfo() {
    const count = allJobs.length;
    document.getElementById('resultsInfo').innerHTML = `
        Found <strong>${count}</strong> job${count !== 1 ? 's' : ''} for "${escapeHtml(currentFilters.q)}"
        ${currentFilters.location ? ` in ${escapeHtml(currentFilters.location)}` : ''}
    `;
}

function showLoading() {
    document.getElementById('jobsGrid').innerHTML = `
        <div class="skeleton-loader">
            <div class="job-skeleton"></div>
            <div class="job-skeleton"></div>
            <div class="job-skeleton"></div>
        </div>
    `;
}

function hideLoading() {
    // Loading state replaced by results
}

function showError(message) {
    document.getElementById('jobsGrid').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

function showPagination() {
    const totalPages = Math.ceil(allJobs.length / pageSize);
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    document.getElementById('pagination').classList.remove('hidden');
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
}

function hidePagination() {
    document.getElementById('pagination').classList.add('hidden');
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayJobs();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function nextPage() {
    const totalPages = Math.ceil(allJobs.length / pageSize);
    if (currentPage < totalPages) {
        currentPage++;
        displayJobs();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const icon = document.getElementById('darkModeBtn').querySelector('i');

    if (document.body.classList.contains('dark-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        localStorage.setItem('darkMode', 'disabled');
    }
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        return date.toLocaleDateString();
    } catch {
        return dateString;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}

// Make functions globally accessible
window.viewJobDetails = viewJobDetails;
window.saveJob = saveJob;
window.showJobAlert = showJobAlert;
window.performJobSearch = performJobSearch;
