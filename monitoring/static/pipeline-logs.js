/**
 * Simple Pipeline Logs JavaScript for Control tab
 * 
 * This provides a lightweight real-time logging display for single pipeline monitoring
 * without the complexity of the old Real-time Logs system.
 */

class PipelineLogs {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.operations = [];
        this.maxOperations = 50; // Keep only last 50 operations
        this.refreshInterval = null;
        this.isActive = false;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.warn('Pipeline logs container not found');
            return;
        }
        
        this.createUI();
        this.startRefresh();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="pipeline-logs-header flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium">Pipeline Activity</h4>
                <div class="flex items-center space-x-2">
                    <span id="pipeline-status" class="text-xs px-2 py-1 rounded bg-gray-100">Idle</span>
                    <button onclick="pipelineLogs.clear()" class="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200">
                        Clear
                    </button>
                </div>
            </div>
            <div id="pipeline-operations" class="pipeline-operations text-xs font-mono h-96 overflow-y-auto bg-gray-900 text-green-400 p-3 rounded">
                <div class="text-gray-500 text-center py-8">
                    <i class="ri-pulse-line text-lg mb-1"></i>
                    <p>Waiting for pipeline activity...</p>
                </div>
            </div>
        `;
    }
    
    async startRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Initial load
        await this.loadOperations();
        
        // Refresh every 2 seconds for more real-time updates
        this.refreshInterval = setInterval(() => {
            this.loadOperations();
        }, 2000);
    }
    
    async loadOperations() {
        try {
            // Try the new logs endpoint first (reads from files)
            const response = await fetch('/api/pipeline/logs?limit=50');
            if (response.ok) {
                const data = await response.json();
                if (data.operations) {
                    // Always update operations to show real-time changes
                    this.operations = data.operations.slice(0, this.maxOperations);
                    this.renderOperations();
                }
            } else {
                // Fallback to old database endpoint
                const fallbackResponse = await fetch('/api/pipeline/operations?limit=20');
                if (fallbackResponse.ok) {
                    const data = await fallbackResponse.json();
                    if (data.operations) {
                        this.operations = data.operations.slice(0, this.maxOperations);
                        this.renderOperations();
                    }
                }
            }
            
            // Get status
            const statusResponse = await fetch('/api/pipeline/status');
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                this.updateStatus(statusData);
            }
            
        } catch (error) {
            console.debug('Pipeline logs fetch error:', error);
        }
    }
    
    updateOperations(newOperations) {
        // Simply replace all operations for real-time update
        this.operations = newOperations.slice(0, this.maxOperations);
        this.renderOperations();
    }
    
    updateStatus(statusData) {
        const statusEl = document.getElementById('pipeline-status');
        if (!statusEl) return;
        
        if (statusData.is_running) {
            statusEl.textContent = 'Running';
            statusEl.className = 'text-xs px-2 py-1 rounded bg-green-100 text-green-800';
            
            if (statusData.latest_operation) {
                const phase = statusData.latest_operation.phase;
                statusEl.textContent = `Running: ${this.formatPhase(phase)}`;
            }
        } else {
            statusEl.textContent = 'Idle';
            statusEl.className = 'text-xs px-2 py-1 rounded bg-gray-100 text-gray-600';
        }
    }
    
    renderOperations() {
        const operationsEl = document.getElementById('pipeline-operations');
        if (!operationsEl) return;
        
        if (this.operations.length === 0) {
            operationsEl.innerHTML = `
                <div class="text-gray-500 text-center py-8">
                    <i class="ri-pulse-line text-lg mb-1"></i>
                    <p>Ожидание активности пайплайна...</p>
                </div>
            `;
            return;
        }
        
        const operationsHtml = this.operations.map(op => {
            const timestamp = new Date(op.timestamp).toLocaleTimeString();
            const statusColor = this.getStatusColor(op.status);
            const phaseIcon = this.getPhaseIcon(op.phase);
            const message = this.formatOperationMessage(op);
            
            return `
                <div class="flex items-start space-x-2 mb-1 text-xs">
                    <span class="text-gray-400 w-20 flex-shrink-0">${timestamp}</span>
                    <span class="w-4 flex-shrink-0">${phaseIcon}</span>
                    <span class="flex-1 ${statusColor}">${message}</span>
                </div>
            `;
        }).join('');
        
        operationsEl.innerHTML = operationsHtml;
        
        // Auto-scroll to top for newest operations
        operationsEl.scrollTop = 0;
    }
    
    formatOperationMessage(op) {
        const details = op.details || {};
        
        // RSS Discovery messages
        if (op.phase === 'rss_discovery') {
            switch(op.operation) {
                case 'rss_discovery_start':
                    return '🚀 RSS парсинг начался';
                    
                case 'phase_start':
                    return `📡 Начинаем проверку ${details.sources_count || 0} источников...`;
                    
                case 'rss_feed_processed':
                    const sourceName = this.getSourceName(details.source_id);
                    if (details.articles_found > 0) {
                        return `✅ ${sourceName}: найдено ${details.articles_found} статей`;
                    } else {
                        return `⚪ ${sourceName}: новых статей нет`;
                    }
                    
                case 'rss_article_discovered':
                    return `📰 Новая статья: "${this.truncateText(details.title, 50)}"`;
                    
                case 'phase_complete':
                case 'rss_discovery_complete':
                    return `✨ RSS парсинг завершён: ${details.sources_processed} источников, ${details.new_articles || 0} новых статей`;
                    
                default:
                    return op.operation;
            }
        }
        
        // Change Tracking messages
        if (op.phase && op.phase.startsWith('change_tracking')) {
            // If we have a message field with actual information, use it
            if (details.message) {
                return details.message;
            }
            
            // Fallback formatting for operations without message field
            switch(op.operation) {
                case 'change_tracking_start':
                    return '🔍 Change Tracking начался';
                    
                case 'scanning_source':
                    return `📡 Сканирование: ${details.source || 'источник'}`;
                    
                case 'changes_detected':
                    return `🔄 Обнаружены изменения на ${details.pages || 0} страницах`;
                    
                case 'urls_extracted':
                    return `🔍 Извлечено ${details.urls || 0} новых URL`;
                    
                case 'articles_exported':
                    return `📤 Экспортировано ${details.articles || 0} статей`;
                    
                default:
                    return op.operation;
            }
        }
        
        // Single Pipeline messages
        switch(op.operation) {
            case 'single_pipeline_start':
                return '🚀 Обработка статьи началась';
                
            case 'phase_start':
                return `⚙️ Фаза: ${this.formatPhase(details.phase)}`;
                
            case 'article_parsed':
                return `📄 Статья распарсена: "${this.truncateText(details.title, 50)}"`;
                
            case 'media_processed':
                return `🖼️ Обработано ${details.images_count || 0} изображений`;
                
            case 'article_translated':
                return `🌐 Статья переведена на русский`;
                
            case 'article_published':
                return `✅ Опубликовано в WordPress (ID: ${details.wordpress_id})`;
                
            case 'phase_complete':
                return `✓ Фаза ${this.formatPhase(details.phase)} завершена`;
                
            case 'single_pipeline_complete':
                return '🎉 Обработка статьи завершена';
                
            default:
                return op.operation;
        }
    }
    
    getSourceName(sourceId) {
        // Map source IDs to readable names
        const sourceNames = {
            // RSS Sources (30)
            'openai': 'OpenAI Blog',
            'google_ai': 'Google AI',
            'microsoft_ai': 'Microsoft AI',
            'google_deepmind': 'DeepMind',
            'forbes_ai': 'Forbes AI',
            'wired_ai': 'Wired AI',
            'techcrunch_ai': 'TechCrunch AI',
            'the_decoder': 'The Decoder',
            'salesforce_ai': 'Salesforce AI',
            'amazon_ai': 'Amazon Science',
            'apple_ml': 'Apple ML',
            'ars_technica_ai': 'Ars Technica AI',
            'databricks': 'Databricks',
            'datarobot': 'DataRobot',
            'hugging_face': 'Hugging Face',
            'ibm_ai': 'IBM AI',
            'mit_news_ai': 'MIT News AI',
            'mit_technology_review_ai': 'MIT Tech Review',
            'nvidia_edge_ai': 'NVIDIA Edge AI',
            'palantir': 'Palantir',
            'pytorch_blog': 'PyTorch Blog',
            'stanford_ai_lab': 'Stanford AI Lab',
            'tensorflow_blog': 'TensorFlow Blog',
            'the_verge_ai': 'The Verge AI',
            'venturebeat_ai': 'VentureBeat AI',
            'google_alerts_gpt': 'Google Alerts (GPT)',
            'google_alerts_ai': 'Google Alerts (AI)',
            'google_alerts_space': 'Google Alerts (Space)',
            'google_alerts_drone': 'Google Alerts (Drone)',
            'google_alerts_war': 'Google Alerts (War)',
            
            // Tracking Sources (49)
            'anthropic': 'Anthropic',
            'google_ai_blog': 'Google AI Blog',
            'google_research': 'Google Research',
            'deepmind': 'DeepMind',
            'openai_tracking': 'OpenAI News',
            'microsoft_ai_news': 'Microsoft AI News',
            'huggingface': 'Hugging Face',
            'google_cloud_ai': 'Google Cloud AI',
            'aws_ai': 'AWS AI',
            'databricks_tracking': 'Databricks Blog',
            'mistral': 'Mistral AI',
            'cohere': 'Cohere',
            'ai21': 'AI21 Labs',
            'scale': 'Scale AI',
            'together': 'Together AI',
            'stability': 'Stability AI',
            'elevenlabs': 'ElevenLabs',
            'waymo': 'Waymo',
            'openevidence': 'OpenEvidence',
            'writer': 'Writer',
            'crusoe': 'Crusoe AI',
            'lambda': 'Lambda Labs',
            'mit_news': 'MIT News',
            'stanford_ai': 'Stanford AI',
            'alpha_sense': 'AlphaSense',
            'instabase': 'Instabase',
            'appzen': 'AppZen',
            'soundhound': 'SoundHound',
            'b12': 'B12',
            'c3ai': 'C3 AI',
            'standardbots': 'Standard Bots',
            'abb_robotics': 'ABB Robotics',
            'fanuc': 'FANUC',
            'kuka': 'KUKA',
            'kinova': 'Kinova',
            'doosan_robotics': 'Doosan Robotics',
            'tempus': 'Tempus',
            'pathai': 'PathAI',
            'augmedix': 'Augmedix',
            'manus': 'Manus',
            'uizard': 'Uizard',
            'mindfoundry': 'Mind Foundry',
            'nscale': 'nScale',
            'audioscenic': 'AudioScenic',
            'perplexity': 'Perplexity AI',
            'cerebras': 'Cerebras AI',
            'runway': 'Runway ML',
            'suno': 'Suno AI'
        };
        return sourceNames[sourceId] || sourceId;
    }
    
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    getStatusColor(status) {
        switch (status) {
            case 'success': return 'text-green-400';
            case 'error': return 'text-red-400';
            case 'in_progress': return 'text-yellow-400';
            default: return 'text-gray-400';
        }
    }
    
    getPhaseIcon(phase) {
        switch (phase) {
            case 'rss_discovery': return '📡';
            case 'parsing': return '📄';
            case 'media_processing': return '🖼️';
            case 'translation': return '🌐';
            case 'publishing': return '📝';
            case 'change_tracking': return '🔍';
            case 'change_tracking_scan': return '📡';
            case 'change_tracking_extract': return '🔍';
            case 'change_tracking_export': return '📤';
            default: return '⚙️';
        }
    }
    
    formatPhase(phase) {
        switch (phase) {
            case 'rss_discovery': return 'RSS Discovery';
            case 'parsing': return 'Parsing';
            case 'media_processing': return 'Media Processing';
            case 'translation': return 'Translation';
            case 'publishing': return 'Publishing';
            case 'change_tracking': return 'Change Tracking';
            case 'change_tracking_scan': return 'Change Tracking Scan';
            case 'change_tracking_extract': return 'Change Tracking Extract';
            case 'change_tracking_export': return 'Change Tracking Export';
            default: return phase;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    addOperation(operation) {
        // Add new operation from WebSocket
        const formattedOp = {
            timestamp: operation.timestamp || new Date().toISOString(),
            phase: operation.phase,
            operation: operation.operation,
            status: operation.status,
            details: operation.details || {}
        };
        
        // Add to beginning of array
        this.operations.unshift(formattedOp);
        
        // Keep only max operations
        this.operations = this.operations.slice(0, this.maxOperations);
        
        // Re-render
        this.renderOperations();
    }
    
    clear() {
        this.operations = [];
        this.renderOperations();
    }
    
    stop() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    start() {
        this.startRefresh();
    }
}

// Initialize pipeline logs when DOM is ready
let pipelineLogs = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if pipeline logs container exists
    if (document.getElementById('pipeline-logs-container')) {
        pipelineLogs = new PipelineLogs('pipeline-logs-container');
        
        // Export to window for global access
        window.pipelineLogs = pipelineLogs;
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineLogs;
}