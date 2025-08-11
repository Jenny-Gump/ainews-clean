/**
 * Smart Log Filter for Human-Readable Logs
 * Filters and formats logs to show only important information
 */

class LogFilter {
    constructor() {
        this.lastLogTime = 0;
        this.minInterval = 1000; // Minimum 1 second between logs
        this.logBuffer = [];
        
        // Pattern to match RSS discovery logs
        this.rssPattern = /RSS discovery for (\w+) \(total_entries=(\d+), new_articles=(\d+), last_parsed=([^)]+)\)/;
        
        // Other important patterns
        this.importantPatterns = [
            this.rssPattern,
            /Successfully parsed (.+)/,
            /Failed to parse (.+)/,
            /Downloaded media from (.+)/,
            /Phase (\d) started/,
            /Phase completed: (.+)/,
            /Completed in (.+) seconds/,
            /ERROR|CRITICAL|WARNING/
        ];
        
        // Messages to completely ignore
        this.ignorePatterns = [
            /Database performance optimizations applied/,
            /Monitoring database initialized/,
            /INFO - Starting(?!.*RSS discovery)/,
            /INFO - Loaded/,
            /initialized/,
            /Scheduler/,
            /apscheduler/,
            /WebSocket/,
            /connection open/,
            /HTTP\/1.1/,
            /Error collecting system resources/
        ];
    }
    
    shouldShowLog(message) {
        // Check if we should ignore this message
        for (const pattern of this.ignorePatterns) {
            if (pattern.test(message)) {
                return false;
            }
        }
        
        // Check if this is an important message
        for (const pattern of this.importantPatterns) {
            if (pattern.test(message)) {
                return true;
            }
        }
        
        // Default: ignore
        return false;
    }
    
    formatLog(level, message, timestamp) {
        // Check if this is an RSS discovery log
        const rssMatch = message.match(this.rssPattern);
        if (rssMatch) {
            const [_, source, totalEntries, newArticles, lastParsed] = rssMatch;
            const time = timestamp ? new Date(timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            
            // Format exactly as requested
            const tag = newArticles > 0 ? 'INFO' : 'INFO';
            return `[${tag}] [${time}] ${source}: ${totalEntries} записей, ${newArticles} новых`;
        }
        
        // Other message formats
        if (message.includes('COMPLETED')) {
            const time = timestamp ? new Date(timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            return `[INFO] [${time}] ${message}`;
        } else if (message.includes('Successfully parsed')) {
            const match = message.match(/Successfully parsed (.+)/);
            return `${match ? match[1] : 'Источник'} обработан`;
        } else if (message.includes('Failed')) {
            const match = message.match(/Failed to parse (.+)|Failed: (.+)/);
            return `Ошибка: ${match ? (match[1] || match[2]) : message}`;
        } else if (message.includes('Phase') && message.includes('started')) {
            return `${message}`;
        } else if (message.includes('Completed in')) {
            return `${message}`;
        } else if (level === 'ERROR' || level === 'CRITICAL') {
            return `${message}`;
        } else if (level === 'WARNING') {
            return `${message}`;
        }
        
        // Default format - keep original message
        return message.replace(/\s+/g, ' ').trim();
    }
    
    processLog(level, message, timestamp) {
        // Check if we should show this log
        if (!this.shouldShowLog(message)) {
            return null;
        }
        
        // Check if this is an RSS discovery log - show all without rate limiting
        const isRSSLog = this.rssPattern.test(message);
        
        if (!isRSSLog) {
            // Apply rate limiting for non-RSS logs
            const now = Date.now();
            if (now - this.lastLogTime < this.minInterval) {
                // Buffer the log
                this.logBuffer.push({ level, message, timestamp });
                return null;
            }
            this.lastLogTime = now;
        }
        
        // Format the log
        const formatted = this.formatLog(level, message, timestamp);
        
        // Process buffered logs if any
        if (!isRSSLog && this.logBuffer.length > 0) {
            const importantBuffered = this.logBuffer.filter(log => 
                this.shouldShowLog(log.message) && !this.rssPattern.test(log.message)
            );
            if (importantBuffered.length > 0) {
                const results = [formatted];
                importantBuffered.slice(0, 2).forEach(log => {
                    results.push(this.formatLog(log.level, log.message, log.timestamp));
                });
                this.logBuffer = [];
                return results;
            }
            this.logBuffer = [];
        }
        
        return formatted;
    }
}

// Export for use
window.LogFilter = LogFilter;