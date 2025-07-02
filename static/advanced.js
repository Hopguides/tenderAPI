// Advanced Tender API Testing Features
class AdvancedTesterUI {
    constructor() {
        this.isAdvancedMode = false;
        this.testHistory = [];
        this.init();
    }

    init() {
        this.createAdvancedUI();
        this.setupAdvancedEventListeners();
    }

    createAdvancedUI() {
        // Add advanced testing button to quick actions
        const quickActions = document.querySelector('.quick-actions');
        const advancedBtn = document.createElement('button');
        advancedBtn.className = 'quick-btn';
        advancedBtn.innerHTML = '<i class="fas fa-flask"></i> Advanced';
        advancedBtn.onclick = () => this.toggleAdvancedMode();
        quickActions.appendChild(advancedBtn);

        // Create advanced panel (initially hidden)
        this.createAdvancedPanel();
    }

    createAdvancedPanel() {
        const mainContent = document.querySelector('.main-content');
        
        const advancedPanel = document.createElement('div');
        advancedPanel.id = 'advancedPanel';
        advancedPanel.className = 'testing-panel';
        advancedPanel.style.display = 'none';
        advancedPanel.style.gridColumn = '1 / -1';
        
        advancedPanel.innerHTML = `
            <div class="panel-header">
                <i class="fas fa-flask panel-icon"></i>
                <h2 class="panel-title">Advanced Testing</h2>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <!-- Benchmark Testing -->
                <div class="advanced-section">
                    <h3><i class="fas fa-stopwatch"></i> Benchmark Testing</h3>
                    <div class="form-group">
                        <label class="form-label">Platform:</label>
                        <select class="form-select" id="benchmarkPlatform">
                            <option value="">Select platform...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Iterations:</label>
                        <input type="number" class="form-input" id="benchmarkIterations" value="5" min="1" max="20">
                    </div>
                    <button class="btn btn-secondary" onclick="advancedTester.runBenchmark()">
                        <i class="fas fa-play"></i> Run Benchmark
                    </button>
                </div>

                <!-- Stress Testing -->
                <div class="advanced-section">
                    <h3><i class="fas fa-fire"></i> Stress Testing</h3>
                    <div class="form-group">
                        <label class="form-label">Platform:</label>
                        <select class="form-select" id="stressPlatform">
                            <option value="">Select platform...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Concurrent Requests:</label>
                        <input type="number" class="form-input" id="stressConcurrent" value="10" min="1" max="50">
                    </div>
                    <button class="btn btn-secondary" onclick="advancedTester.runStressTest()">
                        <i class="fas fa-bolt"></i> Stress Test
                    </button>
                </div>

                <!-- API Analytics -->
                <div class="advanced-section">
                    <h3><i class="fas fa-chart-bar"></i> API Analytics</h3>
                    <div class="form-group">
                        <label class="form-label">Analysis Type:</label>
                        <select class="form-select" id="analyticsType">
                            <option value="response_times">Response Times</option>
                            <option value="success_rates">Success Rates</option>
                            <option value="error_patterns">Error Patterns</option>
                        </select>
                    </div>
                    <button class="btn btn-success" onclick="advancedTester.generateAnalytics()">
                        <i class="fas fa-chart-line"></i> Generate Report
                    </button>
                </div>

                <!-- Test History -->
                <div class="advanced-section">
                    <h3><i class="fas fa-history"></i> Test History</h3>
                    <div class="form-group">
                        <button class="btn" onclick="advancedTester.showHistory()">
                            <i class="fas fa-list"></i> View History
                        </button>
                        <button class="btn btn-secondary" onclick="advancedTester.exportHistory()">
                            <i class="fas fa-download"></i> Export
                        </button>
                        <button class="btn btn-secondary" onclick="advancedTester.clearHistory()">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                    </div>
                </div>
            </div>

            <!-- Advanced Results -->
            <div id="advancedResults" class="results-content" style="margin-top: 20px; max-height: 400px; overflow-y: auto;">
                <div class="info-message">
                    <i class="fas fa-info-circle"></i> 
                    Advanced testing tools ready. Select a test type above to begin.
                </div>
            </div>
        `;

        mainContent.appendChild(advancedPanel);
    }

    setupAdvancedEventListeners() {
        // Populate platform selects when platforms are loaded
        document.addEventListener('platformsLoaded', () => {
            this.populateAdvancedSelects();
        });
    }

    populateAdvancedSelects() {
        const platforms = window.testerApp.platforms;
        const selects = ['benchmarkPlatform', 'stressPlatform'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Select platform...</option>';
                platforms.forEach(platform => {
                    const option = document.createElement('option');
                    option.value = platform.name;
                    option.textContent = platform.display_name || platform.name;
                    select.appendChild(option);
                });
            }
        });
    }

    toggleAdvancedMode() {
        this.isAdvancedMode = !this.isAdvancedMode;
        const panel = document.getElementById('advancedPanel');
        
        if (this.isAdvancedMode) {
            panel.style.display = 'block';
            this.populateAdvancedSelects();
        } else {
            panel.style.display = 'none';
        }
    }

    async runBenchmark() {
        const platform = document.getElementById('benchmarkPlatform').value;
        const iterations = parseInt(document.getElementById('benchmarkIterations').value);
        
        if (!platform) {
            this.showAdvancedError('Please select a platform for benchmark testing');
            return;
        }

        this.showAdvancedLoading(`Running benchmark test on ${platform} (${iterations} iterations)...`);
        
        try {
            const results = await AdvancedTester.benchmarkPlatform(platform, iterations);
            this.showAdvancedResults(results, 'Benchmark Test Results');
            
            // Add to history
            this.addToHistory('benchmark', {
                platform,
                iterations,
                results,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            this.showAdvancedError(`Benchmark test failed: ${error.message}`);
        }
    }

    async runStressTest() {
        const platform = document.getElementById('stressPlatform').value;
        const concurrent = parseInt(document.getElementById('stressConcurrent').value);
        
        if (!platform) {
            this.showAdvancedError('Please select a platform for stress testing');
            return;
        }

        this.showAdvancedLoading(`Running stress test on ${platform} (${concurrent} concurrent requests)...`);
        
        try {
            const results = await AdvancedTester.stressTest(platform, concurrent);
            this.showAdvancedResults(results, 'Stress Test Results');
            
            // Add to history
            this.addToHistory('stress', {
                platform,
                concurrent,
                results,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            this.showAdvancedError(`Stress test failed: ${error.message}`);
        }
    }

    generateAnalytics() {
        const type = document.getElementById('analyticsType').value;
        
        if (this.testHistory.length === 0) {
            this.showAdvancedError('No test history available. Run some tests first.');
            return;
        }

        const analytics = this.analyzeTestHistory(type);
        this.showAdvancedResults(analytics, `Analytics Report: ${type.replace('_', ' ').toUpperCase()}`);
    }

    analyzeTestHistory(type) {
        const history = this.testHistory;
        
        switch (type) {
            case 'response_times':
                return this.analyzeResponseTimes(history);
            case 'success_rates':
                return this.analyzeSuccessRates(history);
            case 'error_patterns':
                return this.analyzeErrorPatterns(history);
            default:
                return { error: 'Unknown analysis type' };
        }
    }

    analyzeResponseTimes(history) {
        const benchmarkTests = history.filter(h => h.type === 'benchmark');
        const analysis = {};

        benchmarkTests.forEach(test => {
            const platform = test.data.platform;
            if (!analysis[platform]) {
                analysis[platform] = {
                    tests: 0,
                    totalResponseTime: 0,
                    minResponseTime: Infinity,
                    maxResponseTime: 0,
                    responseTimes: []
                };
            }

            const avgResponseTime = test.data.results.averageResponseTime;
            analysis[platform].tests++;
            analysis[platform].totalResponseTime += avgResponseTime;
            analysis[platform].responseTimes.push(avgResponseTime);
            analysis[platform].minResponseTime = Math.min(analysis[platform].minResponseTime, avgResponseTime);
            analysis[platform].maxResponseTime = Math.max(analysis[platform].maxResponseTime, avgResponseTime);
        });

        // Calculate averages
        Object.keys(analysis).forEach(platform => {
            const data = analysis[platform];
            data.averageResponseTime = data.totalResponseTime / data.tests;
            data.medianResponseTime = this.calculateMedian(data.responseTimes);
        });

        return {
            type: 'Response Time Analysis',
            platforms: analysis,
            summary: {
                totalTests: benchmarkTests.length,
                fastestPlatform: this.getFastestPlatform(analysis),
                slowestPlatform: this.getSlowestPlatform(analysis)
            }
        };
    }

    analyzeSuccessRates(history) {
        const allTests = history;
        const analysis = {};

        allTests.forEach(test => {
            const platform = test.data.platform;
            if (!analysis[platform]) {
                analysis[platform] = {
                    totalTests: 0,
                    successfulTests: 0,
                    failedTests: 0
                };
            }

            analysis[platform].totalTests++;
            
            if (test.type === 'benchmark') {
                const successRate = test.data.results.successRate;
                if (successRate === 100) {
                    analysis[platform].successfulTests++;
                } else {
                    analysis[platform].failedTests++;
                }
            } else if (test.type === 'stress') {
                if (test.data.results.successful > test.data.results.failed) {
                    analysis[platform].successfulTests++;
                } else {
                    analysis[platform].failedTests++;
                }
            }
        });

        // Calculate success rates
        Object.keys(analysis).forEach(platform => {
            const data = analysis[platform];
            data.successRate = (data.successfulTests / data.totalTests) * 100;
        });

        return {
            type: 'Success Rate Analysis',
            platforms: analysis,
            summary: {
                totalTests: allTests.length,
                overallSuccessRate: this.calculateOverallSuccessRate(analysis)
            }
        };
    }

    analyzeErrorPatterns(history) {
        const errors = {};
        
        history.forEach(test => {
            if (test.type === 'benchmark') {
                test.data.results.results.forEach(result => {
                    if (result.error) {
                        const errorKey = result.error;
                        if (!errors[errorKey]) {
                            errors[errorKey] = {
                                count: 0,
                                platforms: new Set(),
                                firstSeen: test.timestamp,
                                lastSeen: test.timestamp
                            };
                        }
                        errors[errorKey].count++;
                        errors[errorKey].platforms.add(test.data.platform);
                        errors[errorKey].lastSeen = test.timestamp;
                    }
                });
            }
        });

        // Convert Sets to Arrays for JSON serialization
        Object.keys(errors).forEach(errorKey => {
            errors[errorKey].platforms = Array.from(errors[errorKey].platforms);
        });

        return {
            type: 'Error Pattern Analysis',
            errors: errors,
            summary: {
                totalUniqueErrors: Object.keys(errors).length,
                mostCommonError: this.getMostCommonError(errors),
                totalErrorOccurrences: Object.values(errors).reduce((sum, error) => sum + error.count, 0)
            }
        };
    }

    // Utility functions
    calculateMedian(arr) {
        const sorted = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    }

    getFastestPlatform(analysis) {
        let fastest = null;
        let minTime = Infinity;
        
        Object.keys(analysis).forEach(platform => {
            if (analysis[platform].averageResponseTime < minTime) {
                minTime = analysis[platform].averageResponseTime;
                fastest = platform;
            }
        });
        
        return fastest;
    }

    getSlowestPlatform(analysis) {
        let slowest = null;
        let maxTime = 0;
        
        Object.keys(analysis).forEach(platform => {
            if (analysis[platform].averageResponseTime > maxTime) {
                maxTime = analysis[platform].averageResponseTime;
                slowest = platform;
            }
        });
        
        return slowest;
    }

    calculateOverallSuccessRate(analysis) {
        let totalTests = 0;
        let totalSuccessful = 0;
        
        Object.values(analysis).forEach(data => {
            totalTests += data.totalTests;
            totalSuccessful += data.successfulTests;
        });
        
        return totalTests > 0 ? (totalSuccessful / totalTests) * 100 : 0;
    }

    getMostCommonError(errors) {
        let mostCommon = null;
        let maxCount = 0;
        
        Object.keys(errors).forEach(errorKey => {
            if (errors[errorKey].count > maxCount) {
                maxCount = errors[errorKey].count;
                mostCommon = errorKey;
            }
        });
        
        return mostCommon;
    }

    addToHistory(type, data) {
        this.testHistory.push({
            type,
            data,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 100 tests
        if (this.testHistory.length > 100) {
            this.testHistory = this.testHistory.slice(-100);
        }
        
        // Save to localStorage
        localStorage.setItem('tenderApiTestHistory', JSON.stringify(this.testHistory));
    }

    loadHistory() {
        const saved = localStorage.getItem('tenderApiTestHistory');
        if (saved) {
            try {
                this.testHistory = JSON.parse(saved);
            } catch (error) {
                console.error('Error loading test history:', error);
                this.testHistory = [];
            }
        }
    }

    showHistory() {
        if (this.testHistory.length === 0) {
            this.showAdvancedError('No test history available');
            return;
        }

        const historyData = {
            totalTests: this.testHistory.length,
            testTypes: this.getTestTypeCounts(),
            platforms: this.getPlatformCounts(),
            recentTests: this.testHistory.slice(-10).reverse()
        };

        this.showAdvancedResults(historyData, 'Test History');
    }

    getTestTypeCounts() {
        const counts = {};
        this.testHistory.forEach(test => {
            counts[test.type] = (counts[test.type] || 0) + 1;
        });
        return counts;
    }

    getPlatformCounts() {
        const counts = {};
        this.testHistory.forEach(test => {
            const platform = test.data.platform;
            counts[platform] = (counts[platform] || 0) + 1;
        });
        return counts;
    }

    exportHistory() {
        if (this.testHistory.length === 0) {
            this.showAdvancedError('No test history to export');
            return;
        }

        const dataStr = JSON.stringify(this.testHistory, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `tender-api-test-history-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    clearHistory() {
        this.testHistory = [];
        localStorage.removeItem('tenderApiTestHistory');
        this.showAdvancedInfo('Test history cleared');
    }

    showAdvancedLoading(message) {
        const content = document.getElementById('advancedResults');
        content.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
    }

    showAdvancedResults(data, title) {
        const content = document.getElementById('advancedResults');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i> 
                <strong>${title}</strong> - ${timestamp}
            </div>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
    }

    showAdvancedError(message) {
        const content = document.getElementById('advancedResults');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Error</strong> - ${timestamp}
                <br><br>${message}
            </div>
        `;
    }

    showAdvancedInfo(message) {
        const content = document.getElementById('advancedResults');
        const timestamp = new Date().toLocaleString();
        
        content.innerHTML = `
            <div class="info-message">
                <i class="fas fa-info-circle"></i> 
                <strong>Info</strong> - ${timestamp}
                <br><br>${message}
            </div>
        `;
    }
}

// Initialize advanced tester when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.advancedTester = new AdvancedTesterUI();
    window.advancedTester.loadHistory();
});

// Add CSS for advanced sections
const advancedStyles = `
    .advanced-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    .advanced-section h3 {
        margin-bottom: 15px;
        color: #333;
        font-size: 1.2rem;
    }
    
    .advanced-section h3 i {
        margin-right: 8px;
        color: #667eea;
    }
`;

// Inject advanced styles
const styleSheet = document.createElement('style');
styleSheet.textContent = advancedStyles;
document.head.appendChild(styleSheet);

