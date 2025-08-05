// AI News Control Center - Complete JavaScript Integration
// Day 6: Full Dashboard Implementation with Backend API Integration

// =======================
// CORE CONFIGURATION
// =======================

const API_BASE_URL = 'http://localhost:8001/api/monitoring';
const WS_URL = 'ws://localhost:8001/ws';

// Global state management
let globalState = {
    currentTab: 'control',
    websocket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    isConnected: false,
    logsPaused: false,
    refreshInterval: null,
    charts: {
        resourceChart: null,
        processChart: null
    },
    resourceTimeRange: '6h',
    currentData: {
        control: {},
        articles: { data: [], pagination: {}, sources: [] },
        memory: { processes: [], totalMemory: 0 },
        systemResources: { history: [] },
        errors: { recent: [], stats: {} },
        logs: []
    }
};

// =======================
// INITIALIZATION
// =======================

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI News Control Center - Initializing...');
    initializeDashboard();
});

function initializeDashboard() {
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    switchTab('control');
    
    // Start refresh cycle
    startRefreshCycle();
    
    console.log('Dashboard initialized successfully');
}

// =======================
// WEBSOCKET CONNECTION
// =======================

function initializeWebSocket() {
    try {
        globalState.websocket = new WebSocket(WS_URL);
        
        globalState.websocket.onopen = function(event) {
            console.log('WebSocket connected');
            globalState.isConnected = true;
            globalState.reconnectAttempts = 0;
            updateConnectionStatus(true);
            
            // Send ping to keep connection alive
            sendWebSocketMessage({ type: 'ping' });
        };
        
        globalState.websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        globalState.websocket.onclose = function(event) {
            console.log('WebSocket disconnected');
            globalState.isConnected = false;
            updateConnectionStatus(false);
            
            // Attempt to reconnect
            if (globalState.reconnectAttempts < globalState.maxReconnectAttempts) {
                globalState.reconnectAttempts++;
                console.log(`Reconnection attempt ${globalState.reconnectAttempts}/${globalState.maxReconnectAttempts}`);
                setTimeout(initializeWebSocket, 2000 * globalState.reconnectAttempts);
            }
        };
        
        globalState.websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus(false);
    }
}

function sendWebSocketMessage(message) {
    if (globalState.websocket && globalState.websocket.readyState === WebSocket.OPEN) {
        globalState.websocket.send(JSON.stringify(message));
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'metrics_update':
            if (data.rss_metrics) {
                updateRSSMetrics(data.rss_metrics);
            }
            break;
        case 'process_status_update':
            updateProcessStatus(data.status);
            break;
        case 'article_processed':
            incrementArticleCount();
            break;
        case 'error_occurred':
            handleNewError(data.error);
            break;
        case 'log_entry':
            handleLogEntry(data.log);
            break;
        case 'memory_alert':
            handleMemoryAlert(data.alert);
            break;
        case 'system_resources':
            handleSystemResourcesUpdate(data.resources);
            break;
        case 'parsing_progress':
            handleParsingProgressUpdate(data.state);
            break;
        case 'parsing_phase_update':
            handleParsingPhaseUpdate(data);
            break;
        case 'source_progress':
            handleSourceProgressUpdate(data);
            break;
        case 'speed_metrics':
            handleSpeedMetricsUpdate(data);
            break;
        case 'pipeline_state':
            handlePipelineStateUpdate(data);
            break;
        case 'initial':
            console.log('WebSocket initial connection established');
            break;
        case 'pong':
            // Response to ping - connection is alive
            console.log('WebSocket pong received');
            break;
        case 'ping':
            // Send pong response
            sendWebSocketMessage({ type: 'pong' });
            break;
        default:
            console.log('Unknown WebSocket message:', data.type, data);
    }
}

function updateRSSMetrics(rssMetrics) {
    if (globalState.currentTab === 'rss' && rssMetrics.summary) {
        // Update RSS summary if currently viewing RSS tab
        const summary = rssMetrics.summary;
        const totalFeedsEl = document.getElementById('total-rss-feeds');
        const avgFetchTimeEl = document.getElementById('avg-fetch-time');
        
        if (totalFeedsEl) totalFeedsEl.textContent = summary.total_rss_feeds || 0;
        if (avgFetchTimeEl) avgFetchTimeEl.textContent = Math.round(summary.avg_fetch_time_ms || 0);
        
        // Update status breakdown
        if (summary.status_breakdown) {
            const healthyEl = document.getElementById('healthy-rss-feeds');
            const errorEl = document.getElementById('error-rss-feeds');
            
            if (healthyEl) healthyEl.textContent = summary.status_breakdown.healthy || 0;
            if (errorEl) errorEl.textContent = summary.status_breakdown.error || 0;
        }
    }
}

// =======================
// TAB MANAGEMENT
// =======================

function switchTab(tabName) {
    console.log(`Switching to tab: ${tabName}`);
    
    // Prevent switching if already on this tab
    if (globalState.currentTab === tabName) {
        return;
    }
    
    // First, remove fade-in class from all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('fade-in');
    });
    
    // Small delay to ensure previous animations finish
    setTimeout(() => {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // Show selected tab content
        const selectedTab = document.getElementById(tabName + '-tab');
        if (selectedTab) {
            selectedTab.classList.remove('hidden');
            // Force reflow before adding animation class
            selectedTab.offsetHeight;
            selectedTab.classList.add('fade-in');
        } else {
            console.error(`Tab content not found: ${tabName}-tab`);
            return;
        }
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('tab-active');
            button.classList.add('tab-inactive');
            button.setAttribute('aria-selected', 'false');
        });
        
        const selectedButton = document.getElementById(tabName + '-tab-button');
        if (selectedButton) {
            selectedButton.classList.remove('tab-inactive');
            selectedButton.classList.add('tab-active');
            selectedButton.setAttribute('aria-selected', 'true');
        } else {
            console.error(`Tab button not found: ${tabName}-tab-button`);
        }
        
        globalState.currentTab = tabName;
        
        // Load tab-specific data
        loadTabData(tabName);
    }, 50);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'control':
            loadControlData();
            break;
        case 'articles':
            loadArticlesData();
            break;
        case 'memory':
            loadMemoryData();
            break;
        case 'rss':
            loadRSSData();
            break;
        case 'errors':
            loadErrorsData();
            break;
        case 'logs':
            loadLogsData();
            break;
    }
}

// =======================
// CONTROL TAB FUNCTIONS
// =======================

async function loadControlData() {
    try {
        // Get process status
        const statusResponse = await makeAPICall('/control/status');
        
        // Extract the nested status object
        if (statusResponse && statusResponse.status) {
            updateProcessStatus(statusResponse.status);
            
            // Update UI elements with full response for capabilities
            updateControlInterface(statusResponse);
        }
        
        // Get active parsing status
        const parsingResponse = await makeAPICall('/parsing/active');
        if (parsingResponse) {
            updateParsingPipeline(parsingResponse);
        }
        
        // Load last parsed date if function exists
        if (typeof loadLastParsed === 'function') {
            loadLastParsed();
        }
        
        // Load database stats if function exists
        if (typeof loadDatabaseStats === 'function') {
            loadDatabaseStats();
        }
        
    } catch (error) {
        console.error('Error loading control data:', error);
        showNotification('Failed to load control data', 'error');
    }
}

async function startParser() {
    try {
        const daysBack = parseInt(document.getElementById('crawl-days').value) || 7;
        
        showNotification('Starting AI News Parser...', 'info');
        updateButtonState('start-parser', true);
        
        const response = await makeAPICall('/control/start', 'POST', { days_back: daysBack });
        
        if (response.success) {
            showNotification('AI News Parser started successfully', 'success');
            setTimeout(loadControlData, 1000); // Refresh status after delay
        } else {
            throw new Error(response.message || 'Failed to start parser');
        }
        
    } catch (error) {
        console.error('Error starting parser:', error);
        showNotification(`Failed to start parser: ${error.message}`, 'error');
    } finally {
        updateButtonState('start-parser', false);
    }
}

async function stopParser() {
    try {
        showNotification('Stopping AI News Parser...', 'warning');
        updateButtonState('stop-parser', true);
        
        const response = await makeAPICall('/control/stop', 'POST');
        
        if (response.success) {
            showNotification('AI News Parser stopped', 'success');
            setTimeout(loadControlData, 1000);
        } else {
            throw new Error(response.message || 'Failed to stop parser');
        }
        
    } catch (error) {
        console.error('Error stopping parser:', error);
        showNotification(`Failed to stop parser: ${error.message}`, 'error');
    } finally {
        updateButtonState('stop-parser', false);
    }
}

async function pauseParser() {
    try {
        showNotification('Pausing AI News Parser...', 'warning');
        updateButtonState('pause-parser', true);
        
        const response = await makeAPICall('/control/pause', 'POST');
        
        if (response.success) {
            showNotification('AI News Parser paused', 'success');
            setTimeout(loadControlData, 1000);
        } else {
            throw new Error(response.message || 'Failed to pause parser');
        }
        
    } catch (error) {
        console.error('Error pausing parser:', error);
        showNotification(`Failed to pause parser: ${error.message}`, 'error');
    } finally {
        updateButtonState('pause-parser', false);
    }
}

async function restartParser() {
    try {
        showNotification('Restarting AI News Parser...', 'info');
        updateButtonState('restart-parser', true);
        
        // Stop first, then start
        await makeAPICall('/control/stop', 'POST');
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        
        const daysBack = parseInt(document.getElementById('crawl-days').value) || 7;
        const response = await makeAPICall('/control/start', 'POST', { days_back: daysBack });
        
        if (response.success) {
            showNotification('AI News Parser restarted successfully', 'success');
            setTimeout(loadControlData, 1000);
        } else {
            throw new Error(response.message || 'Failed to restart parser');
        }
        
    } catch (error) {
        console.error('Error restarting parser:', error);
        showNotification(`Failed to restart parser: ${error.message}`, 'error');
    } finally {
        updateButtonState('restart-parser', false);
    }
}

function updateProcessStatus(status) {
    const statusElement = document.getElementById('parser-status');
    const currentSourceElement = document.getElementById('current-source');
    const articlesProcessedElement = document.getElementById('articles-processed');
    const processingRateElement = document.getElementById('processing-rate');
    
    if (statusElement) {
        statusElement.textContent = status.status || 'Unknown';
        statusElement.className = `px-2 py-1 text-xs font-medium rounded-full ${getStatusClass(status.status)}`;
    }
    
    if (currentSourceElement) {
        currentSourceElement.textContent = status.current_source || '-';
    }
    
    if (articlesProcessedElement) {
        articlesProcessedElement.textContent = status.articles_processed || '0';
    }
    
    if (processingRateElement) {
        processingRateElement.textContent = status.processing_rate || '-';
    }
}

function updateControlInterface(statusData) {
    // This function is for the OLD interface with start-parser buttons
    // The current HTML uses rss-toggle, parse-toggle, media-toggle
    // So we just return without errors
    const startBtn = document.getElementById('start-parser');
    const stopBtn = document.getElementById('stop-parser');
    const pauseBtn = document.getElementById('pause-parser');
    const restartBtn = document.getElementById('restart-parser');
    
    if (!startBtn || !stopBtn || !pauseBtn || !restartBtn) {
        // Buttons don't exist in current HTML
        return;
    }
    
    // Enable/disable buttons based on capabilities
    if (statusData.capabilities) {
        startBtn.disabled = !statusData.capabilities.can_start;
        stopBtn.disabled = !statusData.capabilities.can_stop;
        pauseBtn.disabled = !statusData.capabilities.can_pause;
        restartBtn.disabled = false;
    } else {
        // Fallback to status-based logic
        const status = statusData.status?.status || statusData.status;
        const isRunning = status === 'running';
        const isPaused = status === 'paused';
        
        startBtn.disabled = isRunning;
        stopBtn.disabled = !isRunning && !isPaused;
        pauseBtn.disabled = !isRunning;
        restartBtn.disabled = false;
    }
}

function updateParsingPipeline(parsingData) {
    const progress = parsingData.parsing_progress || {};
    const processStatus = parsingData.process_status || {};
    
    // Update pipeline stage indicators
    updatePipelineStage('fetch', progress.stage === 'fetching', progress.fetch_count || 0, progress.fetch_progress || 0);
    updatePipelineStage('parse', progress.stage === 'parsing', progress.parse_count || 0, progress.parse_progress || 0);
    updatePipelineStage('store', progress.stage === 'storing', progress.store_count || 0, progress.store_progress || 0);
    
    // Update activity stats
    updateElement('success-rate', `${Math.round(progress.success_rate || 0)}%`);
    
    // Update processing rate with better formatting
    const rate = progress.processing_rate || processStatus.processing_rate;
    if (rate && rate !== '-') {
        updateElement('processing-rate', rate.includes('/') ? rate : `${rate} art/min`);
    } else {
        updateElement('processing-rate', '-');
    }
    
    // Update ETA
    if (progress.eta) {
        const eta = new Date(progress.eta);
        updateElement('pipeline-eta', `ETA: ${eta.toLocaleTimeString()}`);
    } else {
        updateElement('pipeline-eta', 'ETA: -');
    }
    
    // Update overall progress
    const overallProgress = progress.overall_progress || 0;
    updateElement('overall-progress-text', `${Math.round(overallProgress)}%`);
    const progressBar = document.getElementById('overall-progress');
    if (progressBar) {
        progressBar.style.width = `${Math.min(100, overallProgress)}%`;
    }
}

function updatePipelineStage(stageName, isActive, count, progressPercent) {
    const indicator = document.getElementById(`${stageName}-indicator`);
    const countElement = document.getElementById(`${stageName}-count`);
    const progressBar = document.getElementById(`${stageName}-progress`);
    
    if (indicator) {
        indicator.style.backgroundColor = isActive ? '#22c55e' : '#6b7280'; // Green if active, gray if not
        if (isActive) {
            indicator.classList.add('animate-pulse');
        } else {
            indicator.classList.remove('animate-pulse');
        }
    }
    
    if (countElement) {
        countElement.textContent = count;
    }
    
    if (progressBar) {
        progressBar.style.width = `${Math.min(100, progressPercent)}%`;
    }
}

function handleParsingProgressUpdate(progress) {
    if (globalState.currentTab === 'control') {
        updateParsingPipeline({ parsing_progress: progress });
        // Update overall progress if component exists
        if (window.overallProgress) {
            window.overallProgress.update(progress);
        }
    }
}

// New event handlers for enhanced parsing progress
function handleParsingPhaseUpdate(data) {
    if (globalState.currentTab === 'control') {
        // Update overall progress with phase data
        if (window.overallProgress && data.all_phases) {
            window.overallProgress.update({
                phases: data.all_phases,
                phase_progress: data.phase_data
            });
        }
    }
}

function handleSourceProgressUpdate(data) {
    // Source progress is now handled within overall progress
}

function handleSpeedMetricsUpdate(data) {
    // Speed metrics removed to reduce memory usage
}

function handlePipelineStateUpdate(data) {
    if (globalState.currentTab === 'control' && window.overallProgress) {
        // Update overall progress with pipeline data
        window.overallProgress.update({
            phase_progress: { overall: data.overall_progress },
            pipeline: data.pipeline
        });
    }
}

// Helper functions removed - now handled by OverallProgress component

// =======================
// ARTICLES TAB FUNCTIONS
// =======================

async function loadArticlesData() {
    try {
        // For now, skip loading sources as endpoint doesn't exist
        // Just load articles
        await loadArticles();
        
    } catch (error) {
        console.error('Error loading articles data:', error);
        showNotification('Failed to load articles data', 'error');
    }
}

async function loadArticles(page = 1) {
    try {
        const searchTerm = document.getElementById('article-search').value;
        const sourceFilter = document.getElementById('source-filter').value;
        const dateFilter = document.getElementById('date-filter').value;
        
        const params = new URLSearchParams({
            page: page,
            limit: 50,
            search: searchTerm,
            source_filter: sourceFilter,
            date_filter: dateFilter,
            sort_by: 'created_at',
            sort_order: 'desc'
        });
        
        // Use the correct API endpoint - articles router is mounted directly at /api/articles
        const articlesResponse = await fetch(`http://localhost:8001/api/articles?${params}`);
        if (!articlesResponse.ok) {
            throw new Error(`HTTP ${articlesResponse.status}: ${articlesResponse.statusText}`);
        }
        const response = await articlesResponse.json();
        
        globalState.currentData.articles = response;
        renderArticlesTable(response.articles || []);
        updatePagination(response.pagination || {});
        
    } catch (error) {
        console.error('Error loading articles:', error);
        document.getElementById('articles-table-body').innerHTML = 
            '<tr><td colspan="6" class="px-4 py-8 text-center text-sm text-red-500">Error loading articles</td></tr>';
    }
}

function renderArticlesTable(articles) {
    const tbody = document.getElementById('articles-table-body');
    
    if (!articles || articles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-sm" style="color: oklch(var(--muted-foreground));">No articles found</td></tr>';
        return;
    }
    
    tbody.innerHTML = articles.map(article => `
        <tr class="hover:bg-gray-50 cursor-pointer" onclick="viewArticle('${article.article_id || article.id}')">
            <td class="px-4 py-3">
                <div class="font-medium text-sm">${escapeHtml(article.title || 'No title')}</div>
                <div class="text-xs text-gray-500 mt-1">${escapeHtml((article.description || '').substring(0, 100))}${article.description && article.description.length > 100 ? '...' : ''}</div>
            </td>
            <td class="px-4 py-3 text-sm">${escapeHtml(article.source_name || article.source_id || 'Unknown')}</td>
            <td class="px-4 py-3 text-sm">${formatDate(article.created_at)}</td>
            <td class="px-4 py-3 text-sm">
                ${article.url ? `<a href="${article.url}" target="_blank" class="text-blue-500 hover:underline" onclick="event.stopPropagation()"><i class="ri-external-link-line"></i></a>` : '-'}
            </td>
            <td class="px-4 py-3 text-sm">
                ${article.media_count && article.media_count > 0 ? 
                    `<button class="inline-flex items-center text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded cursor-pointer transition-colors" 
                            onclick="event.stopPropagation(); viewArticleMedia('${article.article_id}')">
                        <i class="ri-image-line text-blue-500"></i>
                        <span class="ml-1 font-medium">${article.media_count}</span>
                    </button>` : 
                    '<span class="text-gray-400">-</span>'
                }
            </td>
            <td class="px-4 py-3">
                <span class="px-2 py-1 text-xs font-medium rounded-full ${getStatusClass(article.content_status || article.status)}">
                    ${article.content_status || article.status || 'unknown'}
                </span>
            </td>
            <td class="py-3 px-4 text-center">
                <button class="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded transition-colors" 
                        onclick="event.stopPropagation(); deleteArticle('${article.article_id || article.id}', '${escapeHtml(article.title || 'No title')}')"
                        title="Delete article">
                    <i class="ri-close-line text-lg"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteArticle(articleId, articleTitle) {
    try {
        if (!confirm(`Are you sure you want to delete this article?\n\n"${articleTitle}"\n\nThis action cannot be undone and will also delete any associated media files.`)) {
            return;
        }
        
        const response = await makeAPICall(`/articles/${articleId}`, 'DELETE');
        
        if (response.success) {
            showNotification(`Article deleted successfully: "${articleTitle}"`, 'success');
            // Reload articles
            loadArticlesData();
        } else {
            throw new Error(response.message || 'Failed to delete article');
        }
    } catch (error) {
        console.error('Error deleting article:', error);
        showNotification(`Failed to delete article: ${error.message}`, 'error');
    }
}

async function viewArticle(articleId) {
    try {
        const response = await makeAPICall(`/articles/${articleId}/content`);
        showArticleModal(response);
    } catch (error) {
        console.error('Error loading article content:', error);
        showNotification('Failed to load article content', 'error');
    }
}

async function viewArticleMedia(articleId) {
    try {
        const response = await makeAPICall(`/articles/${articleId}/media`);
        showMediaModal(response);
    } catch (error) {
        console.error('Error loading article media:', error);
        showNotification('Failed to load article media', 'error');
    }
}

function showArticleModal(article) {
    // Create modal HTML
    const modalHTML = `
        <div id="article-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="card max-w-4xl w-full max-h-[90vh] overflow-hidden">
                <div class="p-6 border-b" style="border-color: oklch(var(--border));">
                    <div class="flex justify-between items-start">
                        <div class="flex-1 mr-4">
                            <h2 class="text-xl font-bold mb-2" style="color: oklch(var(--foreground));">${escapeHtml(article.title || 'No title')}</h2>
                            <div class="text-sm text-gray-500">
                                <span>${escapeHtml(article.source_name || 'Unknown source')}</span> • 
                                <span>${formatDate(article.created_at)}</span>
                                ${article.url ? ` • <a href="${article.url}" target="_blank" class="text-blue-500 hover:underline">View Original</a>` : ''}
                            </div>
                        </div>
                        <button onclick="closeArticleModal()" class="btn-secondary p-2" aria-label="Close modal">
                            <i class="ri-close-line text-lg"></i>
                        </button>
                    </div>
                </div>
                <div class="p-6 overflow-y-auto max-h-[60vh]">
                    <div class="prose max-w-none" style="color: oklch(var(--foreground));">
                        ${article.content ? article.content.replace(/\n/g, '<br>') : 'No content available'}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add escape key listener
    document.addEventListener('keydown', handleModalEscape);
}

function closeArticleModal() {
    const modal = document.getElementById('article-modal');
    if (modal) {
        modal.remove();
        document.removeEventListener('keydown', handleModalEscape);
    }
}

function showMediaModal(mediaData) {
    if (!mediaData.media_files || mediaData.media_files.length === 0) {
        showNotification('No media files found for this article', 'info');
        return;
    }

    // Create media gallery HTML
    const mediaHTML = mediaData.media_files.map(media => {
        const isImage = media.type === 'image' || (media.mime_type && media.mime_type.startsWith('image/'));
        
        return `
            <div class="media-item mb-4 p-4 border rounded-lg" style="border-color: oklch(var(--border));">
                <div class="flex items-start space-x-4">
                    <div class="flex-shrink-0">
                        ${isImage ? 
                            `<img src="${media.url}" alt="${escapeHtml(media.alt_text || 'Media file')}" 
                                 class="w-32 h-24 object-cover rounded cursor-pointer"
                                 onclick="openImagePreview('${media.url}', '${escapeHtml(media.alt_text || 'Media file')}')"
                                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9Ijk2IiB2aWV3Qm94PSIwIDAgMTI4IDk2IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMjgiIGhlaWdodD0iOTYiIGZpbGw9IiNmM2Y0ZjYiLz48cGF0aCBkPSJNNDggNDBINDBWNDhINDhWNDBaIiBmaWxsPSIjOWNhM2FmIi8+PHBhdGggZD0iTTQwIDU2SDQ4VjQ4SDQwVjU2WiIgZmlsbD0iIzljYTNhZiIvPjwvc3ZnPg=='">`
                            : `<div class="w-32 h-24 bg-gray-200 rounded flex items-center justify-center">
                                 <i class="ri-file-line text-2xl text-gray-400"></i>
                               </div>`
                        }
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-gray-900 mb-1">
                            ${media.alt_text ? escapeHtml(media.alt_text) : `${media.type || 'Unknown'} file`}
                        </div>
                        <div class="text-xs text-gray-500 space-y-1">
                            <div>Type: ${media.mime_type || media.type || 'Unknown'}</div>
                            ${media.file_size ? `<div>Size: ${formatFileSize(media.file_size)}</div>` : ''}
                            ${media.width && media.height ? `<div>Dimensions: ${media.width}×${media.height}px</div>` : ''}
                            <div>Status: <span class="px-2 py-1 text-xs rounded-full ${media.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">${media.status}</span></div>
                        </div>
                        <div class="mt-2">
                            <a href="${media.url}" target="_blank" class="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm">
                                <i class="ri-external-link-line mr-1"></i>
                                View Original
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    const modalHTML = `
        <div id="media-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="card max-w-4xl w-full max-h-[90vh] overflow-hidden">
                <div class="p-6 border-b" style="border-color: oklch(var(--border));">
                    <div class="flex justify-between items-start">
                        <div class="flex-1 mr-4">
                            <h2 class="text-xl font-bold mb-2" style="color: oklch(var(--foreground));">
                                Media Files (${mediaData.media_count})
                            </h2>
                            <div class="text-sm text-gray-500">
                                Article ID: ${mediaData.article_id}
                            </div>
                        </div>
                        <button onclick="closeMediaModal()" class="btn-secondary p-2" aria-label="Close modal">
                            <i class="ri-close-line text-lg"></i>
                        </button>
                    </div>
                </div>
                <div class="p-6 overflow-y-auto max-h-[60vh]">
                    ${mediaHTML}
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add escape key listener
    document.addEventListener('keydown', handleMediaModalEscape);
}

function closeMediaModal() {
    const modal = document.getElementById('media-modal');
    if (modal) {
        modal.remove();
        document.removeEventListener('keydown', handleMediaModalEscape);
    }
}

function handleMediaModalEscape(event) {
    if (event.key === 'Escape') {
        closeMediaModal();
    }
}

function openImagePreview(url, altText) {
    const previewHTML = `
        <div id="image-preview" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60 p-4" onclick="closeImagePreview()">
            <div class="max-w-full max-h-full flex flex-col items-center">
                <img src="${url}" alt="${escapeHtml(altText)}" class="max-w-full max-h-[80vh] object-contain rounded">
                <div class="mt-4 text-white text-center">
                    <div class="text-lg font-medium">${escapeHtml(altText)}</div>
                    <div class="text-sm opacity-75 mt-1">Click anywhere to close</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', previewHTML);
}

function closeImagePreview() {
    const preview = document.getElementById('image-preview');
    if (preview) {
        preview.remove();
    }
}

function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function handleModalEscape(event) {
    if (event.key === 'Escape') {
        closeArticleModal();
    }
}

function updateSourcesFilter(sources) {
    const select = document.getElementById('source-filter');
    select.innerHTML = '<option value="">All Sources</option>' + 
        sources.map(source => `<option value="${source.id}">${escapeHtml(source.name)} (${source.article_count})</option>`).join('');
}

function updatePagination(pagination) {
    // Simple pagination implementation
    // In a production system, you would implement proper pagination UI
    console.log('Pagination info:', pagination);
}

// =======================
// MEMORY TAB FUNCTIONS
// =======================

async function loadMemoryData() {
    try {
        // Load system resources
        const resourcesResponse = await makeAPICall('/system/resources');
        globalState.currentData.systemResources = resourcesResponse;
        updateSystemResourcesDisplay(resourcesResponse);
        
        // Load memory/process data
        const memoryResponse = await makeAPICall('/memory');
        globalState.currentData.memory = memoryResponse;
        renderProcessTable(memoryResponse.processes || []);
        
        // Initialize or update charts
        await initializeResourceCharts();
        
    } catch (error) {
        console.error('Error loading memory data:', error);
        showNotification('Failed to load memory data', 'error');
    }
}

function updateMemoryOverview(memoryData) {
    const totalMemoryElement = document.getElementById('total-memory');
    const processCountElement = document.getElementById('process-count');
    const memoryUsagePercentElement = document.getElementById('memory-usage-percent');
    
    if (totalMemoryElement) {
        totalMemoryElement.textContent = formatBytes(memoryData.total_ainews_memory || 0);
    }
    
    if (processCountElement) {
        processCountElement.textContent = (memoryData.processes || []).length;
    }
    
    if (memoryUsagePercentElement) {
        const percentage = memoryData.system_memory_percent || 0;
        memoryUsagePercentElement.textContent = `${percentage.toFixed(1)}%`;
        
        // Update color based on usage
        if (percentage > 80) {
            memoryUsagePercentElement.style.color = 'oklch(var(--destructive))';
        } else if (percentage > 60) {
            memoryUsagePercentElement.style.color = 'oklch(0.7451 0.1294 89.1022)'; // Warning color
        } else {
            memoryUsagePercentElement.style.color = 'oklch(var(--foreground))';
        }
    }
}

function renderProcessTable(processes) {
    const tbody = document.getElementById('processes-table-body');
    
    if (!processes || processes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-sm" style="color: oklch(var(--muted-foreground));">No AI News processes found</td></tr>';
        return;
    }
    
    tbody.innerHTML = processes.map(process => `
        <tr>
            <td class="px-4 py-3 text-sm font-mono">${process.pid}</td>
            <td class="px-4 py-3 text-sm">${escapeHtml(process.name || 'Unknown')}</td>
            <td class="px-4 py-3 text-sm">${formatBytes(process.memory || 0)}</td>
            <td class="px-4 py-3 text-sm">${(process.cpu_percent || 0).toFixed(1)}%</td>
            <td class="px-4 py-3">
                <button onclick="killProcess(${process.pid})" class="btn-destructive px-3 py-1 text-xs">
                    Kill Process
                </button>
            </td>
        </tr>
    `).join('');
}

async function killProcess(pid) {
    if (!confirm(`Are you sure you want to kill process ${pid}?`)) {
        return;
    }
    
    try {
        showNotification(`Killing process ${pid}...`, 'warning');
        
        const response = await makeAPICall(`/memory/kill-process/${pid}`, 'POST');
        
        if (response.success) {
            showNotification(`Process ${pid} killed successfully`, 'success');
            setTimeout(loadMemoryData, 1000); // Refresh after delay
        } else {
            throw new Error(response.message || 'Failed to kill process');
        }
        
    } catch (error) {
        console.error('Error killing process:', error);
        showNotification(`Failed to kill process ${pid}: ${error.message}`, 'error');
    }
}

async function killAllAINewsProcesses() {
    if (!confirm('Are you sure you want to kill ALL AI News processes? This will stop all parsing activity.')) {
        return;
    }
    
    try {
        showNotification('Killing all AI News processes...', 'warning');
        
        const response = await makeAPICall('/memory/kill-all-ainews', 'POST');
        
        if (response.success) {
            showNotification(`Killed ${response.killed_count || 0} processes`, 'success');
            setTimeout(loadMemoryData, 1000); // Refresh after delay
        } else {
            throw new Error(response.message || 'Failed to kill processes');
        }
        
    } catch (error) {
        console.error('Error killing all processes:', error);
        showNotification(`Failed to kill processes: ${error.message}`, 'error');
    }
}

// =======================
// ERRORS TAB FUNCTIONS
// =======================

async function loadErrorsData() {
    try {
        // Get filter values
        const errorType = document.getElementById('error-type-filter')?.value || '';
        const errorSource = document.getElementById('error-source-filter')?.value || '';
        const timeFilter = document.getElementById('error-time-filter')?.value || '24h';
        
        // Convert time filter to hours
        const hoursMap = { '24h': 24, '7d': 168, '30d': 720 };
        const hours = hoursMap[timeFilter] || 24;
        
        const response = await makeAPICall(`/error-breakdown?hours=${hours}`);
        
        globalState.currentData.errors = response;
        updateErrorsOverview(response);
        
        // Filter errors based on UI filters
        let filteredErrors = response.errors || [];
        if (errorType) {
            filteredErrors = filteredErrors.filter(e => e.level === errorType);
        }
        if (errorSource) {
            filteredErrors = filteredErrors.filter(e => e.source_id === errorSource);
        }
        
        renderErrorsList(filteredErrors);
        updateErrorSourceFilter(response.errors || []);
        
    } catch (error) {
        console.error('Error loading errors data:', error);
        showNotification('Failed to load errors data', 'error');
    }
}

function updateErrorsOverview(errorsData) {
    const totalErrorsElement = document.getElementById('total-errors');
    const errorSourcesCountElement = document.getElementById('error-sources-count');
    const lastErrorTimeElement = document.getElementById('last-error-time');
    
    if (totalErrorsElement) {
        totalErrorsElement.textContent = errorsData.total_count || 0;
    }
    
    if (errorSourcesCountElement) {
        const uniqueSources = new Set((errorsData.errors || []).map(e => e.source_id).filter(Boolean));
        errorSourcesCountElement.textContent = uniqueSources.size;
    }
    
    if (lastErrorTimeElement) {
        const errors = errorsData.errors || [];
        if (errors.length > 0) {
            lastErrorTimeElement.textContent = formatDate(errors[0].timestamp);
        } else {
            lastErrorTimeElement.textContent = 'No recent errors';
        }
    }
}

function renderErrorsList(errors) {
    const container = document.getElementById('errors-list');
    
    if (!errors || errors.length === 0) {
        container.innerHTML = '<div class="text-center py-8 text-sm" style="color: oklch(var(--muted-foreground));">No recent errors found</div>';
        document.getElementById('errors-pagination').style.display = 'none';
        return;
    }
    
    container.innerHTML = errors.map(error => `
        <div class="card p-4 border-l-4 ${getErrorBorderClass(error.level)}">
            <div class="flex justify-between items-start mb-2">
                <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium ${getErrorTextClass(error.level)}">${error.level || 'ERROR'}</span>
                    <span class="text-sm text-gray-500">${formatDate(error.timestamp)}</span>
                    ${error.source_id ? `<span class="text-sm text-gray-500">• ${escapeHtml(error.source_id)}</span>` : ''}
                </div>
                <div class="flex space-x-1">
                    <button onclick="copyErrorToClipboard('${error.id}')" class="btn-secondary px-2 py-1 text-xs" title="Copy error details">
                        <i class="ri-file-copy-line"></i>
                    </button>
                    ${error.source_id ? `<button onclick="retryErrorSource('${error.source_id}')" class="btn-secondary px-2 py-1 text-xs" title="Retry source">
                        <i class="ri-refresh-line"></i>
                    </button>` : ''}
                </div>
            </div>
            <div class="text-sm font-medium mb-1" style="color: oklch(var(--foreground));">
                ${escapeHtml(error.message || 'No message')}
            </div>
            ${error.context ? `
                <div class="text-xs text-gray-600 mb-2">
                    <strong>Context:</strong> ${escapeHtml(error.context)}
                </div>
            ` : ''}
            ${error.traceback ? `
                <details class="text-xs text-gray-600 mt-2">
                    <summary class="cursor-pointer hover:text-gray-800">Show full stack trace</summary>
                    <pre class="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${escapeHtml(error.traceback)}</pre>
                </details>
            ` : ''}
        </div>
    `).join('');
    
    // Update pagination info
    updateErrorsPagination(errors.length);
}

function getErrorBorderClass(level) {
    switch (level) {
        case 'CRITICAL': return 'border-red-600';
        case 'ERROR': return 'border-red-500';
        case 'WARNING': return 'border-yellow-500';
        default: return 'border-gray-500';
    }
}

function getErrorTextClass(level) {
    switch (level) {
        case 'CRITICAL': return 'text-red-700 font-bold';
        case 'ERROR': return 'text-red-600';
        case 'WARNING': return 'text-yellow-600';
        default: return 'text-gray-600';
    }
}

function updateErrorSourceFilter(errors) {
    const select = document.getElementById('error-source-filter');
    if (!select) return;
    
    const sources = [...new Set(errors.map(e => e.source_id).filter(Boolean))];
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">All Sources</option>' + 
        sources.map(source => `<option value="${escapeHtml(source)}">${escapeHtml(source)}</option>`).join('');
    
    // Restore previous selection if still valid
    if (sources.includes(currentValue)) {
        select.value = currentValue;
    }
}

function updateErrorsPagination(totalCount) {
    const paginationDiv = document.getElementById('errors-pagination');
    const infoDiv = document.getElementById('errors-info');
    
    if (totalCount > 0) {
        paginationDiv.style.display = 'flex';
        infoDiv.textContent = `Showing ${totalCount} errors`;
    } else {
        paginationDiv.style.display = 'none';
    }
}

function refreshErrorFilters() {
    loadErrorsData();
    showNotification('Error filters refreshed', 'success', 1500);
}

function loadErrorsPage(direction) {
    // Placeholder for pagination functionality
    showNotification('Pagination not yet implemented', 'info');
}

async function retryErrorSource(sourceId) {
    try {
        showNotification(`Retrying source ${sourceId}...`, 'info');
        const response = await makeAPICall(`/errors/${sourceId}/retry`, 'POST');
        
        if (response.success) {
            showNotification(`Retry initiated for ${sourceId}`, 'success');
        } else {
            throw new Error(response.message || 'Retry failed');
        }
        
    } catch (error) {
        console.error('Error retrying source:', error);
        showNotification(`Failed to retry source: ${error.message}`, 'error');
    }
}

async function copyAllErrorsForDebug() {
    try {
        // Use the new errors export endpoint
        const response = await makeAPICall('/errors/export?format=json&days=7');
        
        if (response.errors && response.errors.length > 0) {
            const debugText = formatErrorsForDebug(response.errors);
            await navigator.clipboard.writeText(debugText);
            showNotification(`Copied ${response.errors.length} errors to clipboard for debugging`, 'success');
        } else {
            showNotification('No errors to copy', 'info');
        }
        
    } catch (error) {
        console.error('Error copying errors:', error);
        showNotification('Failed to copy errors to clipboard', 'error');
    }
}

async function exportErrorsAsText() {
    try {
        const response = await makeAPICall('/errors/export?format=text&days=7');
        
        if (response.export_text) {
            // Create download
            const blob = new Blob([response.export_text], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `ai-news-errors-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            showNotification('Error report downloaded successfully', 'success');
        } else {
            showNotification('No errors to export', 'info');
        }
        
    } catch (error) {
        console.error('Error exporting errors:', error);
        showNotification('Failed to export errors', 'error');
    }
}

async function copyErrorToClipboard(errorId) {
    try {
        const error = globalState.currentData.errors.errors.find(e => e.id === errorId);
        if (!error) {
            showNotification('Error not found', 'error');
            return;
        }
        
        const debugText = formatSingleErrorForDebug(error);
        await navigator.clipboard.writeText(debugText);
        showNotification('Error details copied to clipboard', 'success');
        
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showNotification('Failed to copy to clipboard', 'error');
    }
}

function formatErrorsForDebug(errors) {
    return `AI News Parser - Debug Report
Generated: ${new Date().toISOString()}
Total Errors: ${errors.length}

${'='.repeat(50)}

${errors.map(error => formatSingleErrorForDebug(error)).join('\n\n' + '-'.repeat(30) + '\n\n')}`;
}

function formatSingleErrorForDebug(error) {
    return `[${error.level || 'ERROR'}] ${formatDate(error.timestamp)}
Source: ${error.source_id || 'Unknown'}
Message: ${error.message || 'No message'}
${error.traceback ? `\nTraceback:\n${error.traceback}` : ''}`;
}

// =======================
// LOGS TAB FUNCTIONS
// =======================

async function loadLogsData() {
    // For now, just display a simple log stream
    // In production, this would connect to a real log streaming endpoint
    if (!globalState.logsPaused) {
        displayLogMessage('System initialized', 'INFO');
        displayLogMessage('Loading logs data...', 'DEBUG');
    }
}

function handleLogEntry(logEntry) {
    if (!globalState.logsPaused && globalState.currentTab === 'logs') {
        displayLogMessage(logEntry.message, logEntry.level, logEntry.timestamp);
    }
}

function displayLogMessage(message, level = 'INFO', timestamp = null) {
    const logStream = document.getElementById('log-stream');
    if (!logStream) return;
    
    const time = timestamp ? new Date(timestamp) : new Date();
    const timeStr = time.toLocaleTimeString();
    
    const levelClass = {
        'DEBUG': 'text-gray-400',
        'INFO': 'text-blue-400',
        'WARNING': 'text-yellow-400',
        'ERROR': 'text-red-400',
        'CRITICAL': 'text-red-600 font-bold'
    }[level] || 'text-gray-300';
    
    const logEntry = document.createElement('div');
    logEntry.className = 'mb-1';
    logEntry.innerHTML = `<span class="text-gray-500">${timeStr}</span> <span class="${levelClass}">[${level}]</span> <span class="text-gray-300">${escapeHtml(message)}</span>`;
    
    logStream.appendChild(logEntry);
    
    // Keep only last 100 log entries
    while (logStream.children.length > 100) {
        logStream.removeChild(logStream.firstChild);
    }
    
    // Auto-scroll to bottom
    logStream.scrollTop = logStream.scrollHeight;
}

function clearLogs() {
    const logStream = document.getElementById('log-stream');
    if (logStream) {
        logStream.innerHTML = '<div class="text-center py-8" style="color: oklch(var(--muted-foreground));">Logs cleared</div>';
    }
}

function toggleLogPause() {
    globalState.logsPaused = !globalState.logsPaused;
    const btn = document.getElementById('log-pause-btn');
    const icon = btn.querySelector('i');
    const text = btn.querySelector('span');
    
    if (globalState.logsPaused) {
        icon.className = 'ri-play-line';
        text.textContent = 'Resume';
        showNotification('Log streaming paused', 'info');
    } else {
        icon.className = 'ri-pause-line';
        text.textContent = 'Pause';
        showNotification('Log streaming resumed', 'info');
    }
}

// =======================
// SYSTEM RESOURCES FUNCTIONS
// =======================

function updateSystemResourcesDisplay(resources) {
    // Update CPU usage
    const cpuUsage = Math.round(resources.cpu_percent || 0);
    updateElement('cpu-usage', `${cpuUsage}%`);
    updateProgressBar('cpu-progress', cpuUsage, cpuUsage > 80 ? 'bg-red-500' : cpuUsage > 60 ? 'bg-yellow-500' : 'bg-blue-500');
    
    // Update Memory usage
    const memoryPercent = Math.round(resources.memory_percent || 0);
    const memoryGB = (resources.memory_used_gb || 0).toFixed(1);
    updateElement('memory-usage', `${memoryGB}GB (${memoryPercent}%)`);
    updateProgressBar('memory-progress', memoryPercent, memoryPercent > 80 ? 'bg-red-500' : memoryPercent > 60 ? 'bg-yellow-500' : 'bg-green-500');
    
    // Update Process count
    updateElement('total-processes', resources.total_processes || 0);
    updateElement('ai-news-processes', `${resources.ainews_processes || 0} AI News`);
    
    // Update Disk usage
    const diskPercent = Math.round(resources.disk_percent || 0);
    updateElement('disk-usage', `${diskPercent}%`);
    updateProgressBar('disk-progress', diskPercent, diskPercent > 90 ? 'bg-red-500' : diskPercent > 70 ? 'bg-yellow-500' : 'bg-orange-500');
    
    // Check for alerts
    checkResourceAlerts(resources);
    
    // Store in history for charts
    storeResourceHistory(resources);
}

function updateProgressBar(id, percentage, colorClass) {
    const progressBar = document.getElementById(id);
    if (progressBar) {
        progressBar.style.width = `${Math.min(100, percentage)}%`;
        progressBar.className = `h-2 rounded-full ${colorClass}`;
    }
}

function checkResourceAlerts(resources) {
    const alerts = [];
    
    if (resources.cpu_percent > 80) {
        alerts.push(`High CPU usage: ${Math.round(resources.cpu_percent)}%`);
    }
    
    if (resources.memory_used_gb > 7) {
        alerts.push(`High memory usage: ${resources.memory_used_gb.toFixed(1)}GB`);
    }
    
    if (resources.disk_percent > 90) {
        alerts.push(`High disk usage: ${Math.round(resources.disk_percent)}%`);
    }
    
    const alertContainer = document.getElementById('resource-alerts');
    const alertMessages = document.getElementById('alert-messages');
    
    if (alerts.length > 0) {
        alertContainer.style.display = 'block';
        alertMessages.innerHTML = alerts.join('<br>');
    } else {
        alertContainer.style.display = 'none';
    }
}

function storeResourceHistory(resources) {
    const timestamp = new Date().toISOString();
    const dataPoint = {
        timestamp,
        cpu: resources.cpu_percent || 0,
        memory: resources.memory_percent || 0,
        processes: resources.total_processes || 0
    };
    
    // Store in global state
    if (!globalState.currentData.systemResources.history) {
        globalState.currentData.systemResources.history = [];
    }
    
    globalState.currentData.systemResources.history.push(dataPoint);
    
    // Keep only recent data based on time range
    const now = new Date();
    const timeRanges = {
        '1h': 60 * 60 * 1000,
        '6h': 6 * 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000
    };
    
    const cutoff = new Date(now.getTime() - timeRanges[globalState.resourceTimeRange]);
    globalState.currentData.systemResources.history = globalState.currentData.systemResources.history.filter(
        point => new Date(point.timestamp) > cutoff
    );
    
    // Update chart if visible
    if (globalState.currentTab === 'memory' && globalState.charts.resourceChart) {
        updateResourceChart();
    }
}

async function initializeResourceCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded, cannot initialize charts');
        showNotification('Chart.js failed to load - charts unavailable', 'error');
        return;
    }
    
    // Initialize resource trend chart
    if (globalState.charts.resourceChart) {
        globalState.charts.resourceChart.destroy();
    }
    
    const resourceCtx = document.getElementById('resource-chart');
    if (resourceCtx) {
        try {
            globalState.charts.resourceChart = new Chart(resourceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Memory %',
                        data: [],
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
        } catch (error) {
            console.error('Error initializing resource chart:', error);
            showNotification('Failed to initialize resource chart', 'error');
        }
    }
    
    // Initialize process memory chart
    if (globalState.charts.processChart) {
        globalState.charts.processChart.destroy();
    }
    
    const processCtx = document.getElementById('process-chart');
    if (processCtx) {
        updateProcessChart();
    }
}

function updateResourceChart() {
    if (!globalState.charts.resourceChart) return;
    
    const history = globalState.currentData.systemResources.history || [];
    const labels = history.map(point => new Date(point.timestamp).toLocaleTimeString());
    const cpuData = history.map(point => point.cpu);
    const memoryData = history.map(point => point.memory);
    
    globalState.charts.resourceChart.data.labels = labels;
    globalState.charts.resourceChart.data.datasets[0].data = cpuData;
    globalState.charts.resourceChart.data.datasets[1].data = memoryData;
    globalState.charts.resourceChart.update('none');
}

function updateProcessChart() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded, cannot update process chart');
        return;
    }
    
    const processes = globalState.currentData.memory?.processes || [];
    const aiNewsProcesses = processes.filter(p => 
        p.name && (p.name.includes('python') || p.name.includes('ai-news') || p.name.includes('main.py'))
    );
    
    if (globalState.charts.processChart) {
        globalState.charts.processChart.destroy();
    }
    
    const processCtx = document.getElementById('process-chart');
    if (processCtx && aiNewsProcesses.length > 0) {
        try {
            globalState.charts.processChart = new Chart(processCtx, {
            type: 'doughnut',
            data: {
                labels: aiNewsProcesses.map(p => `${p.name} (${p.pid})`),
                datasets: [{
                    data: aiNewsProcesses.map(p => p.memory || 0),
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(34, 197, 94)',
                        'rgb(249, 115, 22)',
                        'rgb(239, 68, 68)',
                        'rgb(168, 85, 247)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        } catch (error) {
            console.error('Error creating process chart:', error);
        }
    } else {
        // Show empty state
        if (processCtx) {
            processCtx.getContext('2d').clearRect(0, 0, processCtx.width, processCtx.height);
        const ctx = processCtx.getContext('2d');
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#6b7280';
        ctx.fillText('No AI News processes running', processCtx.width / 2, processCtx.height / 2);
        }
    }
}

function changeResourceTimeRange(range) {
    globalState.resourceTimeRange = range;
    
    // Update button states
    document.querySelectorAll('.resource-time-btn').forEach(btn => {
        if (btn.dataset.range === range) {
            btn.className = btn.className.replace('btn-secondary', 'btn-primary');
        } else {
            btn.className = btn.className.replace('btn-primary', 'btn-secondary');
        }
    });
    
    // Refresh chart with new time range
    updateResourceChart();
}

function refreshProcessChart() {
    updateProcessChart();
    showNotification('Process chart refreshed', 'success', 1500);
}

function handleSystemResourcesUpdate(resources) {
    if (globalState.currentTab === 'memory') {
        updateSystemResourcesDisplay(resources);
    }
}

// =======================
// LAST PARSED MANAGEMENT
// =======================

function getLastParsedAge(lastParsed) {
    if (!lastParsed) {
        return { text: 'Never', class: 'bg-gray-100 text-gray-800' };
    }
    
    const now = new Date();
    const parsed = new Date(lastParsed);
    const diffHours = (now - parsed) / (1000 * 60 * 60);
    
    if (diffHours < 24) {
        return { text: `${Math.round(diffHours)}h ago`, class: 'bg-green-100 text-green-800' };
    } else if (diffHours < 168) { // 7 days
        return { text: `${Math.round(diffHours / 24)}d ago`, class: 'bg-yellow-100 text-yellow-800' };
    } else {
        return { text: `${Math.round(diffHours / 168)}w ago`, class: 'bg-red-100 text-red-800' };
    }
}

async function setAllLastParsed(timeRange) {
    const confirmMessage = `Set all sources' last parsed time to ${timeRange} ago?`;
    if (!confirm(confirmMessage)) return;
    
    try {
        const now = new Date();
        let targetDate;
        
        switch (timeRange) {
            case '24h':
                targetDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                break;
            case '7d':
                targetDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30d':
                targetDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
            default:
                throw new Error('Invalid time range');
        }
        
        // Get all sources first
        const sourcesResponse = await makeAPICall('/sources/last-parsed');
        const updates = sourcesResponse.sources.map(source => ({
            source_id: source.source_id,
            last_parsed: targetDate.toISOString()
        }));
        
        // Bulk update
        const response = await makeAPICall('/sources/last-parsed/bulk', 'POST', updates);
        
        if (response.success) {
            showNotification(`Updated ${response.updated_count} sources to ${timeRange} ago`, 'success');
            // Call the function from HTML inline script
            if (typeof refreshLastParsed === 'function') {
                refreshLastParsed();
            }
        } else {
            throw new Error(response.message || 'Bulk update failed');
        }
        
    } catch (error) {
        console.error('Error in bulk update:', error);
        showNotification(`Failed to update sources: ${error.message}`, 'error');
    }
}

async function resetAllLastParsed() {
    if (!confirm('Reset ALL sources to fetch from the beginning? This will cause a full re-crawl.')) return;
    
    try {
        const sourcesResponse = await makeAPICall('/sources/last-parsed');
        const updates = sourcesResponse.sources.map(source => ({
            source_id: source.source_id,
            last_parsed: '2020-01-01T00:00:00Z'
        }));
        
        const response = await makeAPICall('/sources/last-parsed/bulk', 'POST', updates);
        
        if (response.success) {
            showNotification(`Reset ${response.updated_count} sources`, 'success');
            if (typeof refreshLastParsed === 'function') {
                refreshLastParsed();
            }
        } else {
            throw new Error(response.message || 'Bulk reset failed');
        }
        
    } catch (error) {
        console.error('Error in bulk reset:', error);
        showNotification(`Failed to reset sources: ${error.message}`, 'error');
    }
}

function showBulkUpdateModal() {
    const modalHtml = `
        <div id="bulk-update-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="card max-w-lg w-full mx-4">
                <div class="p-6">
                    <h3 class="text-lg font-semibold mb-4" style="color: oklch(var(--foreground));">Bulk Update Last Parsed</h3>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Update Mode</label>
                            <select id="bulk-mode" class="w-full px-3 py-2 rounded-md" style="background-color: oklch(var(--input)); border: 1px solid oklch(var(--border)); color: oklch(var(--foreground));">
                                <option value="relative">Relative to now</option>
                                <option value="absolute">Specific date/time</option>
                            </select>
                        </div>
                        
                        <div id="relative-options">
                            <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Time Range</label>
                            <select id="time-range" class="w-full px-3 py-2 rounded-md" style="background-color: oklch(var(--input)); border: 1px solid oklch(var(--border)); color: oklch(var(--foreground));">
                                <option value="1h">1 hour ago</option>
                                <option value="6h">6 hours ago</option>
                                <option value="24h">24 hours ago</option>
                                <option value="7d">7 days ago</option>
                                <option value="30d">30 days ago</option>
                            </select>
                        </div>
                        
                        <div id="absolute-options" style="display: none;">
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Date</label>
                                    <input type="date" id="bulk-date" class="w-full px-3 py-2 rounded-md" style="background-color: oklch(var(--input)); border: 1px solid oklch(var(--border)); color: oklch(var(--foreground));">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Time</label>
                                    <input type="time" id="bulk-time" class="w-full px-3 py-2 rounded-md" style="background-color: oklch(var(--input)); border: 1px solid oklch(var(--border)); color: oklch(var(--foreground));">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex justify-end space-x-3 mt-6">
                        <button onclick="closeBulkUpdateModal()" class="btn-secondary px-4 py-2 text-sm">Cancel</button>
                        <button onclick="executeBulkUpdate()" class="btn-primary px-4 py-2 text-sm">Update All</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Setup mode toggle
    document.getElementById('bulk-mode').addEventListener('change', function() {
        const relativeOptions = document.getElementById('relative-options');
        const absoluteOptions = document.getElementById('absolute-options');
        
        if (this.value === 'absolute') {
            relativeOptions.style.display = 'none';
            absoluteOptions.style.display = 'block';
            // Set default to current date/time
            const now = new Date();
            document.getElementById('bulk-date').value = now.toISOString().split('T')[0];
            document.getElementById('bulk-time').value = now.toTimeString().slice(0, 5);
        } else {
            relativeOptions.style.display = 'block';
            absoluteOptions.style.display = 'none';
        }
    });
}

function closeBulkUpdateModal() {
    const modal = document.getElementById('bulk-update-modal');
    if (modal) modal.remove();
}

function closeDateTimeModal() {
    const modal = document.getElementById('datetime-modal');
    if (modal) modal.remove();
}

async function executeBulkUpdate() {
    try {
        const mode = document.getElementById('bulk-mode').value;
        let targetDate;
        
        if (mode === 'relative') {
            const timeRange = document.getElementById('time-range').value;
            const now = new Date();
            
            const timeMap = {
                '1h': 60 * 60 * 1000,
                '6h': 6 * 60 * 60 * 1000,
                '24h': 24 * 60 * 60 * 1000,
                '7d': 7 * 24 * 60 * 60 * 1000,
                '30d': 30 * 24 * 60 * 60 * 1000
            };
            
            targetDate = new Date(now.getTime() - timeMap[timeRange]);
        } else {
            const date = document.getElementById('bulk-date').value;
            const time = document.getElementById('bulk-time').value;
            targetDate = new Date(`${date}T${time}`);
        }
        
        // Get all sources
        const sourcesResponse = await makeAPICall('/sources/last-parsed');
        const updates = sourcesResponse.sources.map(source => ({
            source_id: source.source_id,
            last_parsed: targetDate.toISOString()
        }));
        
        // Execute bulk update
        const response = await makeAPICall('/sources/last-parsed/bulk', 'POST', updates);
        
        if (response.success) {
            showNotification(`Updated ${response.updated_count} sources`, 'success');
            if (typeof refreshLastParsed === 'function') {
                refreshLastParsed();
            }
            closeBulkUpdateModal();
        } else {
            throw new Error(response.message || 'Bulk update failed');
        }
        
    } catch (error) {
        console.error('Error executing bulk update:', error);
        showNotification(`Failed to update sources: ${error.message}`, 'error');
    }
}

// =======================
// UTILITY FUNCTIONS
// ======================="

async function makeAPICall(endpoint, method = 'GET', data = null, timeout = 30000) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    // Add timeout handling
    const controller = new AbortController();
    options.signal = controller.signal;
    
    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeout);
    
    try {
        const response = await fetch(url, options);
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API call failed: ${response.status} ${response.statusText} - ${errorText}`);
        }
        
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timed out');
        }
        throw error;
    }
}

function showNotification(message, type = 'success', duration = 3000) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = {
        'success': 'ri-check-line',
        'error': 'ri-error-warning-line',
        'warning': 'ri-alert-line',
        'info': 'ri-information-line'
    }[type] || 'ri-information-line';
    
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="${icon} text-lg"></i>
            <span class="font-medium">${escapeHtml(message)}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
                <i class="ri-close-line"></i>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

function updateConnectionStatus(isConnected = null) {
    if (isConnected !== null) {
        globalState.isConnected = isConnected;
    }
    
    const indicator = document.getElementById('connection-indicator');
    const status = document.getElementById('connection-status');
    const lastUpdate = document.getElementById('last-update');
    
    if (globalState.isConnected) {
        indicator.className = 'w-2 h-2 rounded-full status-connected';
        status.className = 'text-sm font-medium status-connected';
        status.textContent = 'Connected';
        lastUpdate.textContent = new Date().toLocaleTimeString();
    } else {
        indicator.className = 'w-2 h-2 rounded-full status-error';
        status.className = 'text-sm font-medium status-error';
        status.textContent = 'Disconnected';
    }
}

function refreshDashboard() {
    showNotification('Refreshing dashboard...', 'info', 1500);
    loadTabData(globalState.currentTab);
    updateConnectionStatus();
}

function setupEventListeners() {
    // Search functionality with debounce
    const articleSearch = document.getElementById('article-search');
    if (articleSearch) {
        articleSearch.addEventListener('input', debounce(() => {
            if (globalState.currentTab === 'articles') {
                loadArticles();
            }
        }, 500));
    }
    
    // Filter dropdowns
    const sourceFilter = document.getElementById('source-filter');
    if (sourceFilter) {
        sourceFilter.addEventListener('change', () => {
            if (globalState.currentTab === 'articles') {
                loadArticles();
            }
        });
    }
    
    const dateFilter = document.getElementById('date-filter');
    if (dateFilter) {
        dateFilter.addEventListener('change', () => {
            if (globalState.currentTab === 'articles') {
                loadArticles();
            }
        });
    }
    
    // Log search
    const logSearch = document.getElementById('log-search');
    if (logSearch) {
        logSearch.addEventListener('input', debounce(() => {
            // Implement log search functionality
            console.log('Log search:', logSearch.value);
        }, 300));
    }
    
    // Error filters
    const errorTypeFilter = document.getElementById('error-type-filter');
    if (errorTypeFilter) {
        errorTypeFilter.addEventListener('change', () => {
            if (globalState.currentTab === 'errors') {
                loadErrorsData();
            }
        });
    }
    
    const errorSourceFilter = document.getElementById('error-source-filter');
    if (errorSourceFilter) {
        errorSourceFilter.addEventListener('change', () => {
            if (globalState.currentTab === 'errors') {
                loadErrorsData();
            }
        });
    }
    
    const errorTimeFilter = document.getElementById('error-time-filter');
    if (errorTimeFilter) {
        errorTimeFilter.addEventListener('change', () => {
            if (globalState.currentTab === 'errors') {
                loadErrorsData();
            }
        });
    }
}

function startRefreshCycle() {
    // Refresh current tab data every 30 seconds
    globalState.refreshInterval = setInterval(() => {
        if (globalState.isConnected) {
            loadTabData(globalState.currentTab);
        }
    }, 30000);
}

// Utility functions
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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatDateTime(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function getStatusClass(status) {
    const statusClasses = {
        'running': 'bg-green-100 text-green-800',
        'stopped': 'bg-red-100 text-red-800',
        'paused': 'bg-yellow-100 text-yellow-800',
        'parsed': 'bg-blue-100 text-blue-800',
        'error': 'bg-red-100 text-red-800',
        'pending': 'bg-gray-100 text-gray-800',
        'idle': 'bg-gray-100 text-gray-800',
        'unknown': 'bg-gray-100 text-gray-800'
    };
    return statusClasses[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
}

function updateButtonState(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.classList.add('opacity-50');
        const spinner = '<i class="ri-loader-4-line animate-spin mr-2"></i>';
        const originalContent = button.innerHTML;
        button.innerHTML = spinner + 'Processing...';
        button.dataset.originalContent = originalContent;
    } else {
        button.disabled = false;
        button.classList.remove('opacity-50');
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
        }
    }
}

function incrementArticleCount() {
    const element = document.getElementById('articles-processed');
    if (element) {
        const current = parseInt(element.textContent) || 0;
        element.textContent = current + 1;
    }
}

// Loading state management
function setLoadingState(elementId, isLoading, loadingText = 'Loading...') {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = `
            <div class="flex items-center justify-center py-4">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-3"></div>
                <span class="text-sm" style="color: oklch(var(--muted-foreground));">${loadingText}</span>
            </div>
        `;
        element.classList.add('opacity-75');
    } else {
        if (element.dataset.originalContent) {
            element.innerHTML = element.dataset.originalContent;
            delete element.dataset.originalContent;
        }
        element.classList.remove('opacity-75');
    }
}

// Error boundary wrapper for tab loading
function withErrorBoundary(tabName, loadFunction) {
    return async function() {
        const tabContent = document.getElementById(`${tabName}-tab`);
        if (!tabContent) return;
        
        try {
            setLoadingState(`${tabName}-tab`, true, `Loading ${tabName} data...`);
            await loadFunction();
        } catch (error) {
            console.error(`Error loading ${tabName} tab:`, error);
            
            // Show error state in tab
            const errorContent = `
                <div class="card p-6 border-red-500 bg-red-50">
                    <div class="flex items-center space-x-3">
                        <i class="ri-error-warning-line text-2xl text-red-500"></i>
                        <div>
                            <h3 class="font-semibold text-red-700">Failed to load ${tabName} data</h3>
                            <p class="text-sm text-red-600 mt-1">${error.message}</p>
                            <button onclick="loadTabData('${tabName}')" class="btn-secondary px-3 py-2 text-sm mt-3">
                                <i class="ri-refresh-line"></i> Retry
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            tabContent.innerHTML = errorContent;
            showNotification(`Failed to load ${tabName} data: ${error.message}`, 'error');
        } finally {
            setLoadingState(`${tabName}-tab`, false);
        }
    };
}

// Enhanced error handler with retry capability
function handleAPIError(error, context, retryFunction = null) {
    console.error(`API Error in ${context}:`, error);
    
    let message = error.message || 'Unknown error occurred';
    let type = 'error';
    
    if (message.includes('timeout')) {
        message = 'Request timed out. Please check your connection.';
        type = 'warning';
    } else if (message.includes('404')) {
        message = 'Endpoint not found. Please refresh the page.';
    } else if (message.includes('500')) {
        message = 'Server error. Please try again later.';
    }
    
    showNotification(message, type, 5000);
    
    // Update connection status if appropriate
    if (message.includes('timeout') || message.includes('500')) {
        updateConnectionStatus(false);
    }
}

function handleNewError(error) {
    if (globalState.currentTab === 'errors') {
        // Refresh errors tab if we're viewing it
        setTimeout(loadErrorsData, 1000);
    }
    
    // Show notification for critical errors
    if (error.level === 'CRITICAL') {
        showNotification(`Critical error: ${error.message}`, 'error', 5000);
    }
    
    // Update error count in tab if visible
    updateErrorTabCount();
}

function updateErrorTabCount() {
    // This could be enhanced to show error count in the tab title
    const errorsData = globalState.currentData.errors;
    if (errorsData && errorsData.total_count > 0) {
        const tabButton = document.getElementById('errors-tab-button');
        const span = tabButton.querySelector('span');
        if (span) {
            span.textContent = `Errors (${errorsData.total_count})`;
        }
    }
}

function handleMemoryAlert(alert) {
    showNotification(`Memory Alert: ${alert.message}`, 'warning', 5000);
    
    if (globalState.currentTab === 'memory') {
        setTimeout(loadMemoryData, 1000);
    }
}

// =======================
// GLOBAL EXPORTS FOR HTML
// =======================

// =======================
// RSS DATA LOADING
// =======================

async function loadRSSData() {
    try {
        console.log('Loading RSS data...');
        
        // Load RSS feeds status
        const response = await fetch('/api/rss/feeds');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // Update summary cards
        updateElement('total-rss-feeds', data.total_feeds || 0);
        updateElement('healthy-rss-feeds', data.healthy_feeds || 0);
        updateElement('error-rss-feeds', data.error_feeds || 0);
        
        // Get additional status data
        const statusResponse = await fetch('/api/rss/status');
        if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            updateElement('avg-fetch-time', Math.round(statusData.avg_fetch_time_ms || 0));
        }
        
        // Update RSS feeds table
        updateRSSTable(data.feeds || []);
        
        // Store in global state
        globalState.currentData.rss = data;
        
        console.log('RSS data loaded successfully');
        
    } catch (error) {
        console.error('Error loading RSS data:', error);
        showNotification('Failed to load RSS data', 'error');
        
        // Show error state
        updateElement('total-rss-feeds', 'Error');
        updateElement('healthy-rss-feeds', 'Error');
        updateElement('error-rss-feeds', 'Error');
        updateElement('avg-fetch-time', 'Error');
    }
}

function updateRSSTable(feeds) {
    const tbody = document.getElementById('rss-feeds-table');
    if (!tbody) return;
    
    if (feeds.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-8" style="color: oklch(var(--muted-foreground));">
                    No RSS feeds found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = feeds.map(feed => `
        <tr class="border-b hover:bg-gray-50" style="border-color: oklch(var(--border));">
            <td class="py-3 px-4">
                <div class="font-medium">${escapeHtml(feed.source_name)}</div>
                <div class="text-sm" style="color: oklch(var(--muted-foreground));">${escapeHtml(feed.source_id)}</div>
            </td>
            <td class="py-3 px-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRSSStatusClass(feed.status)}">
                    ${escapeHtml(feed.status)}
                </span>
            </td>
            <td class="py-3 px-4">
                <div class="text-sm">${feed.articles_in_feed || 0} total</div>
                <div class="text-xs" style="color: oklch(var(--muted-foreground));">${feed.new_articles_found || 0} new</div>
            </td>
            <td class="py-3 px-4">
                <div class="text-sm">${Math.round(feed.fetch_time_ms || 0)}ms</div>
            </td>
            <td class="py-3 px-4">
                <div class="text-sm">${Math.round(feed.pipeline_efficiency || 0)}%</div>
                <div class="text-xs" style="color: oklch(var(--muted-foreground));">${feed.scrape_successes || 0}/${feed.scrape_attempts || 0}</div>
            </td>
            <td class="py-3 px-4">
                <div class="text-sm">${formatDateTime(feed.last_check)}</div>
            </td>
            <td class="py-3 px-4">
                <button onclick="checkRSSFeed('${escapeHtml(feed.source_id)}')" 
                        class="btn-secondary px-2 py-1 text-xs hover:bg-gray-200 transition-colors">
                    <i class="ri-refresh-line"></i> Check
                </button>
            </td>
        </tr>
    `).join('');
}

function getRSSStatusClass(status) {
    switch (status) {
        case 'healthy': return 'bg-green-100 text-green-800';
        case 'error': return 'bg-red-100 text-red-800';
        case 'timeout': return 'bg-yellow-100 text-yellow-800';
        case 'stale': return 'bg-orange-100 text-orange-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

async function refreshRSSFeeds() {
    showNotification('Refreshing RSS feeds...', 'success');
    await loadRSSData();
}

async function checkRSSFeed(sourceId) {
    try {
        showNotification(`Checking RSS feed for ${sourceId}...`, 'success');
        
        const response = await fetch(`/api/rss/feed/${sourceId}/check`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        showNotification(`RSS feed check initiated for ${sourceId}`, 'success');
        
        // Refresh data after a short delay
        setTimeout(() => refreshRSSFeeds(), 2000);
        
    } catch (error) {
        console.error('Error checking RSS feed:', error);
        showNotification('Failed to check RSS feed', 'error');
    }
}

// Make functions available globally for HTML onclick handlers
// Don't override functions from index.html
// window.switchTab = switchTab;  // Already defined in index.html
window.startParser = startParser;
window.stopParser = stopParser;
window.pauseParser = pauseParser;
window.restartParser = restartParser;
window.killAllAINewsProcesses = killAllAINewsProcesses;
window.copyErrorsForDebug = copyErrorsForDebug;
window.clearLogs = clearLogs;
window.toggleLogPause = toggleLogPause;
// window.refreshDashboard = refreshDashboard;  // Already defined in index.html
window.viewArticle = viewArticle;
window.closeArticleModal = closeArticleModal;
window.killProcess = killProcess;
window.copyErrorToClipboard = copyErrorToClipboard;
window.loadRSSData = loadRSSData;
window.refreshRSSFeeds = refreshRSSFeeds;
window.checkRSSFeed = checkRSSFeed;
window.changeResourceTimeRange = changeResourceTimeRange;
window.refreshProcessChart = refreshProcessChart;
window.copyAllErrorsForDebug = copyAllErrorsForDebug;
window.exportErrorsAsText = exportErrorsAsText;
window.refreshErrorFilters = refreshErrorFilters;
window.loadErrorsPage = loadErrorsPage;
window.retryErrorSource = retryErrorSource;
window.setAllLastParsed = setAllLastParsed;
window.resetAllLastParsed = resetAllLastParsed;
window.showBulkUpdateModal = showBulkUpdateModal;
window.closeBulkUpdateModal = closeBulkUpdateModal;
window.closeDateTimeModal = closeDateTimeModal;
window.executeBulkUpdate = executeBulkUpdate;

console.log('AI News Control Center JavaScript loaded successfully');