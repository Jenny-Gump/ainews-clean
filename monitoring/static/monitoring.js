// AI News Control Center - Complete JavaScript Integration
// Cleaned version - Control, Articles and Memory functionality only

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
        systemResources: { history: [] }
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
        case 'process_status_update':
            updateProcessStatus(data.status);
            break;
        case 'article_processed':
            incrementArticleCount();
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
                            <div>Status: <span class="px-2 py-1 text-xs rounded-full ${media.status === 'parsed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">${media.status}</span></div>
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

function handleMemoryAlert(alert) {
    showNotification(`Memory Alert: ${alert.message}`, 'warning');
}

// =======================
// UTILITY FUNCTIONS
// =======================

async function makeAPICall(endpoint, method = 'GET', data = null) {
    try {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

function updateElement(id, content) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = content;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch {
        return 'Invalid date';
    }
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function getStatusClass(status) {
    switch (status) {
        case 'running': case 'active': case 'healthy': case 'success': case 'parsed':
            return 'bg-green-100 text-green-800';
        case 'paused': case 'pending': case 'processing':
            return 'bg-yellow-100 text-yellow-800';
        case 'stopped': case 'inactive': case 'error': case 'failed':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

function updateButtonState(buttonId, disabled) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = disabled;
    }
}

function incrementArticleCount() {
    const element = document.getElementById('articles-processed');
    if (element) {
        const current = parseInt(element.textContent) || 0;
        element.textContent = current + 1;
    }
}

function updateConnectionStatus(connected) {
    // Find any connection status indicators and update them
    const indicators = document.querySelectorAll('.connection-status');
    indicators.forEach(indicator => {
        if (connected) {
            indicator.classList.remove('text-red-500');
            indicator.classList.add('text-green-500');
            indicator.textContent = 'Connected';
        } else {
            indicator.classList.remove('text-green-500');
            indicator.classList.add('text-red-500');
            indicator.textContent = 'Disconnected';
        }
    });
}

function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${getNotificationClass(type)}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, duration);
    
    console.log(`[${type.toUpperCase()}] ${message}`);
}

function getNotificationClass(type) {
    switch (type) {
        case 'success':
            return 'bg-green-100 text-green-800 border border-green-200';
        case 'error':
            return 'bg-red-100 text-red-800 border border-red-200';
        case 'warning':
            return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
        case 'info':
        default:
            return 'bg-blue-100 text-blue-800 border border-blue-200';
    }
}

function setupEventListeners() {
    // Set up global event listeners here
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+R or F5 - refresh current tab
        if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
            e.preventDefault();
            loadTabData(globalState.currentTab);
        }
        
        // Ctrl+1-3 for tab switching
        if (e.ctrlKey && ['1', '2', '3'].includes(e.key)) {
            e.preventDefault();
            const tabs = ['control', 'articles', 'memory'];
            const index = parseInt(e.key) - 1;
            if (tabs[index]) {
                switchTab(tabs[index]);
            }
        }
    });
}

function startRefreshCycle() {
    // Auto-refresh every 30 seconds
    if (globalState.refreshInterval) {
        clearInterval(globalState.refreshInterval);
    }
    
    globalState.refreshInterval = setInterval(() => {
        if (globalState.currentTab === 'control') {
            loadControlData();
        } else if (globalState.currentTab === 'memory') {
            loadMemoryData();
        }
        // Articles tab doesn't auto-refresh to avoid interrupting user actions
    }, 30000);
}

// =======================
// BULK UPDATE FUNCTIONS
// =======================

function showBulkUpdateModal() {
    const modalHTML = `
        <div id="bulk-update-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="card max-w-2xl w-full mx-4">
                <div class="p-6 border-b" style="border-color: oklch(var(--border));">
                    <h2 class="text-xl font-bold" style="color: oklch(var(--foreground));">Bulk Update Source Last Parsed</h2>
                </div>
                <div class="p-6">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Update Action</label>
                            <select id="bulk-update-action" class="input w-full">
                                <option value="set_all">Set all sources to specific date/time</option>
                                <option value="reset_all">Reset all sources (clear last_parsed)</option>
                            </select>
                        </div>
                        <div id="datetime-selector">
                            <label class="block text-sm font-medium mb-2" style="color: oklch(var(--foreground));">Date & Time</label>
                            <input type="datetime-local" id="bulk-datetime" class="input w-full">
                        </div>
                        <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
                            <p class="text-sm text-yellow-800">
                                <strong>Warning:</strong> This will update ALL RSS sources. Use with caution.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="p-6 border-t flex justify-end space-x-3" style="border-color: oklch(var(--border));">
                    <button onclick="closeBulkUpdateModal()" class="btn-secondary">Cancel</button>
                    <button onclick="executeBulkUpdate()" class="btn-destructive">Execute Update</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Set default datetime to 2 hours ago
    const defaultTime = new Date();
    defaultTime.setHours(defaultTime.getHours() - 2);
    document.getElementById('bulk-datetime').value = defaultTime.toISOString().slice(0, 16);
    
    // Handle action change
    document.getElementById('bulk-update-action').addEventListener('change', function() {
        const dateTimeSelector = document.getElementById('datetime-selector');
        if (this.value === 'reset_all') {
            dateTimeSelector.style.display = 'none';
        } else {
            dateTimeSelector.style.display = 'block';
        }
    });
}

function closeBulkUpdateModal() {
    const modal = document.getElementById('bulk-update-modal');
    if (modal) {
        modal.remove();
    }
}

function closeDateTimeModal() {
    // Legacy function - keeping for compatibility
    closeBulkUpdateModal();
}

async function executeBulkUpdate() {
    try {
        const action = document.getElementById('bulk-update-action').value;
        const datetime = document.getElementById('bulk-datetime').value;
        
        let confirmMessage = 'Are you sure you want to ';
        if (action === 'reset_all') {
            confirmMessage += 'reset ALL sources (clear their last_parsed timestamps)?';
        } else {
            confirmMessage += `set ALL sources to ${datetime}?`;
        }
        confirmMessage += '\n\nThis action affects all RSS sources and cannot be undone.';
        
        if (!confirm(confirmMessage)) {
            return;
        }
        
        showNotification('Executing bulk update...', 'info');
        
        const requestData = { action };
        if (action === 'set_all' && datetime) {
            requestData.datetime = datetime;
        }
        
        const response = await makeAPICall('/rss/bulk-update-last-parsed', 'POST', requestData);
        
        if (response.success) {
            showNotification(`Successfully updated ${response.updated_count} sources`, 'success');
            closeBulkUpdateModal();
            // Refresh RSS data if we're on that tab
            if (globalState.currentTab === 'rss') {
                loadRSSData();
            }
        } else {
            throw new Error(response.message || 'Bulk update failed');
        }
        
    } catch (error) {
        console.error('Error executing bulk update:', error);
        showNotification(`Failed to execute bulk update: ${error.message}`, 'error');
    }
}

async function setAllLastParsed() {
    try {
        // Set all sources to 2 hours ago
        const twoHoursAgo = new Date();
        twoHoursAgo.setHours(twoHoursAgo.getHours() - 2);
        
        if (!confirm(`Set ALL sources' last_parsed to ${twoHoursAgo.toLocaleString()}?\n\nThis affects all RSS sources.`)) {
            return;
        }
        
        const response = await makeAPICall('/rss/bulk-update-last-parsed', 'POST', {
            action: 'set_all',
            datetime: twoHoursAgo.toISOString()
        });
        
        if (response.success) {
            showNotification(`Set ${response.updated_count} sources to 2 hours ago`, 'success');
            if (globalState.currentTab === 'rss') {
                loadRSSData();
            }
        } else {
            throw new Error(response.message || 'Failed to set last parsed');
        }
        
    } catch (error) {
        console.error('Error setting all last parsed:', error);
        showNotification(`Failed to set last parsed: ${error.message}`, 'error');
    }
}

async function resetAllLastParsed() {
    try {
        if (!confirm('Reset ALL sources (clear their last_parsed timestamps)?\n\nThis will cause all sources to be parsed from the beginning.')) {
            return;
        }
        
        const response = await makeAPICall('/rss/bulk-update-last-parsed', 'POST', {
            action: 'reset_all'
        });
        
        if (response.success) {
            showNotification(`Reset ${response.updated_count} sources`, 'success');
            if (globalState.currentTab === 'rss') {
                loadRSSData();
            }
        } else {
            throw new Error(response.message || 'Failed to reset last parsed');
        }
        
    } catch (error) {
        console.error('Error resetting all last parsed:', error);
        showNotification(`Failed to reset last parsed: ${error.message}`, 'error');
    }
}

// Make functions available globally for HTML onclick handlers
window.startParser = startParser;
window.stopParser = stopParser;
window.pauseParser = pauseParser;
window.restartParser = restartParser;
window.killAllAINewsProcesses = killAllAINewsProcesses;
window.viewArticle = viewArticle;
window.closeArticleModal = closeArticleModal;
window.killProcess = killProcess;
window.changeResourceTimeRange = changeResourceTimeRange;
window.refreshProcessChart = refreshProcessChart;
window.setAllLastParsed = setAllLastParsed;
window.resetAllLastParsed = resetAllLastParsed;
window.showBulkUpdateModal = showBulkUpdateModal;
window.closeBulkUpdateModal = closeBulkUpdateModal;
window.closeDateTimeModal = closeDateTimeModal;
window.executeBulkUpdate = executeBulkUpdate;

console.log('AI News Control Center JavaScript loaded successfully');