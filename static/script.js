// Tender API Testing Interface JavaScript
class TenderAPITester {
    constructor() {
        this.baseURL = this.getBaseURL();
        this.selectedPlatform = null;
        this.platforms = [];
        this.init();
    }

    getBaseURL() {
        // Auto-detect base URL based on current location
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `${protocol}//${hostname}:8000`;
        } else {
            return `${protocol}//${hostname}${port ? ':' + port : ''}`;
        }
    }

    async init() {
        await this.loadPlatforms();
        this.setupEventListeners();
        this.updateStatus('Ready', 'warning');
    }

    async loadPlatforms() {
        try {
            this.updateStatus('Loading platforms...', 'warning');
            const response = await fetch(`${this.baseURL}/platforms`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.platforms = data.platforms || [];
            this.renderPlatforms();
            this.populatePlatformSelect();
            this.updateStatus('Platforms loaded', 'success');
            
        } catch (error) {
            console.error('Error loading platforms:', error);
            this.showError(`Failed to load platforms: ${error.message}`);
            this.updateStatus('Error loading platforms', 'error');
            
            // Fallback to default platforms
            this.platforms = [
                { name: 'ted', display_name: 'TED Europe', status: 'unknown' },
                { name: 'sam', display_name: 'SAM.gov', status: 'unknown' },
                { name: 'bonfire', display_name: 'Bonfire', status: 'unknown' }
            ];
            this.renderPlatforms();
            this.populatePlatformSelect();
        }
    }

    renderPlatforms() {
        const grid = document.getElementById('platformGrid');
        grid.innerHTML = '';

        this.platforms.forEach(platform => {
            const card = document.createElement('div');
            card.className = 'platform-card';
            card.dataset.platform = platform.name;
            
            card.innerHTML = `
                <div class="platform-name">${platform.display_name || platform.name}</div>
                <div class="platform-status">${this.getStatusText(platform.status)}</div>
            `;
            
            card.addEventListener('click', () => this.selectPlatform(platform.name));
            grid.appendChild(card);
        });
    }

    populatePlatformSelect() {
        const select = document.getElementById('platformSelect');
        select.innerHTML = '<option value="">Select a platform...</option>';
        
        this.platforms.forEach(platform => {
            const option = document.createElement('option');
            option.value = platform.name;
            option.textContent = platform.display_name || platform.name;
            select.appendChild(option);
        });
    }

    selectPlatform(platformName) {
        // Update visual selection
        document.querySelectorAll('.platform-card').forEach(card => {
            card.classList.remove('active');
        });
        
        const selectedCard = document.querySelector(`[data-platform="${platformName}"]`);
        if (selectedCard) {
            selectedCard.classList.add('active');
        }
        
        // Update form
        document.getElementById('platformSelect').value = platformName;
        this.selectedPlatform = platformName;
        
        this.showInfo(`Selected platform: ${platformName}`);
    }

    getStatusText(status) {
        switch (status) {
            case 'healthy': return '✅ Healthy';
            case 'error': return '❌ Error';
            case 'unknown': return '❓ Unknown';
            default: return '⚪ Ready';
        }
    }

    setupEventListeners() {
        // Search form submission
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });

        // Platform select change
        document.getElementById('platformSelect').addEventListener('change', (e) => {
            if (e.target.value) {
                this.selectPlatform(e.target.value);
            }
        });
    }

    async performSearch() {
        const platform = document.getElementById('platformSelect').value;
        if (!platform) {
            this.showError('Please select a platform first');
            return;
        }

        const params = this.getSearchParams();
        
        try {
            this.showLoading('Searching tenders...');
            this.updateStatus('Searching...', 'warning');
            
            const url = `${this.baseURL}/search/${platform}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            this.showResults(data, `Search results for ${platform}`);
            this.updateStatus(`Found ${data.tenders?.length || 0} tenders`, 'success');
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError(`Search failed: ${error.message}`);
            this.updateStatus('Search failed', 'error');
        }
    }

    getSearchParams() {
        const params = {};
        
        const organization = document.getElementById('organization').value.trim();
        if (organization) params.organization = organization;
        
        const keywords = document.getElementById('keywords').value.trim();
        if (keywords) params.keywords = keywords;
        
        const status = document.getElementById('status').value;
        if (status) params.status = status;
        
        const limit = parseInt(document.getElementById('limit').value);
        if (limit && limit > 0) params.limit = limit;
        
        // Add required date fields for SAM.gov platform
        const selectedPlatform = document.getElementById('platformSelect').value;
        if (selectedPlatform === 'sam') {
            // SAM.gov requires posted_from and posted_to dates
            const today = new Date();
            const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
            
            params.posted_from = thirtyDaysAgo.toISOString().split('T')[0]; // YYYY-MM-DD format
            params.posted_to = today.toISOString().split('T')[0]; // YYYY-MM-DD format
        }
        
        return params;
    }

    async testHealth() {
        try {
            this.showLoading('Checking API health...');
            this.updateStatus('Health check...', 'warning');
            
            const response = await fetch(`${this.baseURL}/health`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.showResults(data, 'Health Check Results');
            this.updateStatus('API healthy', 'success');
            
        } catch (error) {
            console.error('Health check error:', error);
            this.showError(`Health check failed: ${error.message}`);
            this.updateStatus('API unhealthy', 'error');
        }
    }

    async testAllPlatforms() {
        this.showLoading('Testing all platforms...');
        this.updateStatus('Testing all platforms...', 'warning');
        
        const results = {};
        
        for (const platform of this.platforms) {
            try {
                // Prepare platform-specific parameters
                let testParams = { limit: 1 };
                
                // Add required date fields for SAM.gov
                if (platform.name === 'sam') {
                    const today = new Date();
                    const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
                    
                    testParams.posted_from = thirtyDaysAgo.toISOString().split('T')[0];
                    testParams.posted_to = today.toISOString().split('T')[0];
                }
                
                const response = await fetch(`${this.baseURL}/search/${platform.name}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(testParams)
                });
                
                const data = await response.json();
                results[platform.name] = {
                    status: response.ok ? 'success' : 'error',
                    data: data,
                    response_time: 'N/A'
                };
                
            } catch (error) {
                results[platform.name] = {
                    status: 'error',
                    error: error.message,
                    response_time: 'N/A'
                };
            }
        }
        
        this.showResults(results, 'All Platforms Test Results');
        
        const successCount = Object.values(results).filter(r => r.status === 'success').length;
        this.updateStatus(`${successCount}/${this.platforms.length} platforms working`, 
                         successCount === this.platforms.length ? 'success' : 'warning');
    }

    showLoading(message) {
        const content = document.getElementById('resultsContent');
        content.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
    }

    showResults(data, title) {
        const content = document.getElementById('resultsContent');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i> 
                <strong>${title}</strong> - ${timestamp}
            </div>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
    }

    showError(message) {
        const content = document.getElementById('resultsContent');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Error</strong> - ${timestamp}
                <br><br>${message}
            </div>
        `;
    }

    showInfo(message) {
        const content = document.getElementById('resultsContent');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="info-message">
                <i class="fas fa-info-circle"></i> 
                <strong>Info</strong> - ${timestamp}
                <br><br>${message}
            </div>
        `;
    }

    updateStatus(message, type) {
        const indicator = document.getElementById('statusIndicator');
        const statusClass = `status-${type}`;
        
        indicator.innerHTML = `
            <span class="status-indicator ${statusClass}"></span>
            <span>${message}</span>
        `;
    }
    clearResults() {
        const content = document.getElementById('resultsContent');
        content.innerHTML = `
            <div class="info-message">
                <i class="fas fa-info-circle"></i> 
                Results cleared. Ready for new tests.
            </div>
        `;
    }

    async getLatestTenders() {
        const content = document.getElementById('resultsContent');
        content.innerHTML = `
            <div class="loading-message">
                <i class="fas fa-clock fa-spin"></i> 
                Fetching latest tenders from all platforms...
            </div>
        `;
        
        try {
            const startTime = performance.now();
            const response = await fetch(`${this.baseURL}/latest-tenders?limit=10`);
            const endTime = performance.now();
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Display results
            let html = `
                <div class="latest-tenders-header">
                    <h3><i class="fas fa-clock"></i> Latest Tenders from All Platforms</h3>
                    <div class="summary-stats">
                        <span class="stat"><i class="fas fa-stopwatch"></i> ${data.execution_time}s</span>
                        <span class="stat"><i class="fas fa-file-alt"></i> ${data.total_tenders} tenders</span>
                        <span class="stat"><i class="fas fa-globe"></i> ${Object.keys(data.platforms).length} platforms</span>
                    </div>
                </div>
            `;
            
            // Display results for each platform
            for (const [platformName, platformData] of Object.entries(data.platforms)) {
                const statusIcon = platformData.status === 'success' ? '✅' : '❌';
                const statusClass = platformData.status === 'success' ? 'success' : 'error';
                
                html += `
                    <div class="platform-results ${statusClass}">
                        <h4>${statusIcon} ${platformData.platform_info?.name || platformName.toUpperCase()}</h4>
                `;
                
                if (platformData.status === 'success') {
                    html += `
                        <div class="platform-summary">
                            <span>Found: ${platformData.total_count} tenders</span>
                            <span>Showing: ${platformData.tenders.length} latest</span>
                        </div>
                    `;
                    
                    if (platformData.tenders && platformData.tenders.length > 0) {
                        html += '<div class="tender-list">';
                        platformData.tenders.forEach((tender, index) => {
                            html += `
                                <div class="tender-item">
                                    <div class="tender-header">
                                        <span class="tender-number">#${index + 1}</span>
                                        <span class="tender-title">${tender.title || tender.name || 'No title'}</span>
                                    </div>
                                    <div class="tender-details">
                                        ${tender.department ? `<span><i class="fas fa-building"></i> ${tender.department}</span>` : ''}
                                        ${tender.posted_date ? `<span><i class="fas fa-calendar"></i> ${tender.posted_date}</span>` : ''}
                                        ${tender.response_deadline ? `<span><i class="fas fa-clock"></i> Deadline: ${tender.response_deadline}</span>` : ''}
                                        ${tender.solicitation_number ? `<span><i class="fas fa-hashtag"></i> ${tender.solicitation_number}</span>` : ''}
                                    </div>
                                    ${tender.url ? `<a href="${tender.url}" target="_blank" class="tender-link">View Details <i class="fas fa-external-link-alt"></i></a>` : ''}
                                </div>
                            `;
                        });
                        html += '</div>';
                    } else {
                        html += '<p class="no-results">No tenders found</p>';
                    }
                } else {
                    html += `<div class="error-message">❌ Error: ${platformData.error}</div>`;
                }
                
                html += '</div>';
            }
            
            // Add metadata
            html += `
                <div class="metadata">
                    <h4><i class="fas fa-info-circle"></i> Request Metadata</h4>
                    <div class="metadata-grid">
                        <span>Timestamp: ${new Date(data.metadata.timestamp).toLocaleString()}</span>
                        <span>Platforms: ${data.metadata.platforms_queried.join(', ')}</span>
                        <span>Supabase Storage: ${data.metadata.supabase_storage.enabled ? '✅ Enabled' : '❌ Disabled'}</span>
                        <span>Database Connected: ${data.metadata.supabase_storage.connected ? '✅ Yes' : '❌ No'}</span>
                    </div>
                </div>
            `;
            
            content.innerHTML = html;
            
        } catch (error) {
            console.error('Latest tenders error:', error);
            content.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>Failed to fetch latest tenders: ${error.message}</p>
                </div>
            `;
        }
    }
}

// Global functions for quick actions
function testHealth() {
    window.testerApp.testHealth();
}

function getLatestTenders() {
    window.testerApp.getLatestTenders();
}

function testAllPlatforms() {
    window.testerApp.testAllPlatforms();
}

function clearResults() {
    window.testerApp.clearResults();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.testerApp = new TenderAPITester();
});

// Add some utility functions for advanced testing
class AdvancedTester {
    static async benchmarkPlatform(platformName, iterations = 5) {
        const results = [];
        
        for (let i = 0; i < iterations; i++) {
            const startTime = performance.now();
            
            try {
                const response = await fetch(`${window.testerApp.baseURL}/search/${platformName}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ limit: 1 })
                });
                
                const endTime = performance.now();
                const responseTime = endTime - startTime;
                
                results.push({
                    iteration: i + 1,
                    success: response.ok,
                    responseTime: responseTime,
                    status: response.status
                });
                
            } catch (error) {
                const endTime = performance.now();
                results.push({
                    iteration: i + 1,
                    success: false,
                    responseTime: endTime - startTime,
                    error: error.message
                });
            }
        }
        
        return {
            platform: platformName,
            iterations: iterations,
            results: results,
            averageResponseTime: results.reduce((sum, r) => sum + r.responseTime, 0) / results.length,
            successRate: (results.filter(r => r.success).length / results.length) * 100
        };
    }

    static async stressTest(platformName, concurrentRequests = 10) {
        const promises = [];
        
        for (let i = 0; i < concurrentRequests; i++) {
            promises.push(
                fetch(`${window.testerApp.baseURL}/search/${platformName}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ limit: 1 })
                })
            );
        }
        
        const startTime = performance.now();
        const results = await Promise.allSettled(promises);
        const endTime = performance.now();
        
        return {
            platform: platformName,
            concurrentRequests: concurrentRequests,
            totalTime: endTime - startTime,
            successful: results.filter(r => r.status === 'fulfilled' && r.value.ok).length,
            failed: results.filter(r => r.status === 'rejected' || !r.value.ok).length,
            results: results
        };
    }
}

// Make AdvancedTester available globally
window.AdvancedTester = AdvancedTester;

