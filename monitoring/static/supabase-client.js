// Supabase Client Configuration for AI News Dashboard
// Provides direct database access with real-time subscriptions

// Configuration
const SUPABASE_URL = 'https://mtguynupyltlqiwhmilc.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10Z3V5bnVweWx0bHFpd2htaWxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5OTYyMzQsImV4cCI6MjA3MDU3MjIzNH0.IYE2SSXqGCp_QqzqdERyqyQkgH7-fuyF7SA3uEcLSno';

// Global Supabase client instance
let supabaseClient = null;
let realtimeChannels = new Map();

// Connection status
let supabaseConnectionStatus = {
    isConnected: false,
    lastError: null,
    retryCount: 0,
    maxRetries: 3
};

// Initialize Supabase Client
function initializeSupabaseClient() {
    try {
        if (typeof supabase === 'undefined') {
            console.warn('Supabase library not loaded, falling back to API');
            return false;
        }
        
        supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            realtime: {
                params: {
                    eventsPerSecond: 10
                }
            }
        });
        
        // Test connection
        testSupabaseConnection();
        
        console.log('Supabase client initialized successfully');
        return true;
    } catch (error) {
        console.error('Failed to initialize Supabase client:', error);
        supabaseConnectionStatus.lastError = error.message;
        return false;
    }
}

// Test Supabase connection
async function testSupabaseConnection() {
    try {
        const { data, error } = await supabaseClient
            .from('articles')
            .select('count', { count: 'exact', head: true });
            
        if (error) {
            throw error;
        }
        
        supabaseConnectionStatus.isConnected = true;
        supabaseConnectionStatus.lastError = null;
        supabaseConnectionStatus.retryCount = 0;
        
        updateSupabaseConnectionIndicator(true);
        console.log('Supabase connection test successful');
        
    } catch (error) {
        console.error('Supabase connection test failed:', error);
        supabaseConnectionStatus.isConnected = false;
        supabaseConnectionStatus.lastError = error.message;
        supabaseConnectionStatus.retryCount++;
        
        updateSupabaseConnectionIndicator(false, error.message);
        
        // Retry connection if under limit
        if (supabaseConnectionStatus.retryCount < supabaseConnectionStatus.maxRetries) {
            setTimeout(() => testSupabaseConnection(), 2000 * supabaseConnectionStatus.retryCount);
        }
    }
}

// Update connection status indicator in UI
function updateSupabaseConnectionIndicator(isConnected, errorMessage = null) {
    const indicator = document.getElementById('supabase-status');
    if (!indicator) return;
    
    const statusDot = indicator.querySelector('.status-dot');
    const statusText = indicator.querySelector('.status-text');
    
    if (isConnected) {
        statusDot.className = 'status-dot w-2 h-2 rounded-full bg-green-500';
        statusText.textContent = 'Supabase Connected';
        indicator.title = 'Real-time connection active';
    } else {
        statusDot.className = 'status-dot w-2 h-2 rounded-full bg-red-500';
        statusText.textContent = 'Supabase Disconnected';
        indicator.title = errorMessage || 'Connection failed';
    }
}

// =====================================
// HELPER FUNCTIONS FOR DATA QUERIES
// =====================================

// Articles queries
const SupabaseArticles = {
    // Get articles with pagination and filters
    async getArticles(options = {}) {
        if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
            throw new Error('Supabase not connected');
        }
        
        const {
            page = 1,
            pageSize = 20,
            status = null,
            source = null,
            search = null,
            sortBy = 'created_at',
            sortOrder = 'desc'
        } = options;
        
        let query = supabaseClient
            .from('articles')
            .select(`
                article_id,
                title,
                url,
                content_status,
                media_status,
                source_id,
                created_at,
                published_date,
                description,
                media_count,
                discovered_via
            `);
            
        // Apply filters
        if (status) {
            query = query.eq('content_status', status);
        }
        if (source) {
            query = query.eq('source_id', source);
        }
        if (search) {
            query = query.or(`title.ilike.%${search}%,description.ilike.%${search}%`);
        }
        
        // Apply sorting and pagination
        query = query
            .order(sortBy, { ascending: sortOrder === 'asc' })
            .range((page - 1) * pageSize, page * pageSize - 1);
            
        const { data, error, count } = await query;
        
        if (error) throw error;
        
        return {
            data: data || [],
            pagination: {
                page,
                pageSize,
                total: count,
                totalPages: Math.ceil((count || 0) / pageSize)
            }
        };
    },
    
    // Get article statistics
    async getStats() {
        if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
            throw new Error('Supabase not connected');
        }
        
        const { data, error } = await supabaseClient
            .rpc('get_article_stats');
            
        if (error) throw error;
        return data;
    },
    
    // Get recent articles for real-time updates
    async getRecentArticles(limit = 10) {
        if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
            throw new Error('Supabase not connected');
        }
        
        const { data, error } = await supabaseClient
            .from('articles')
            .select('id, title, status, created_at, source_name')
            .order('created_at', { ascending: false })
            .limit(limit);
            
        if (error) throw error;
        return data;
    }
};

// System monitoring queries
const SupabaseMonitoring = {
    // Get system metrics
    async getSystemMetrics(timeRange = '1h') {
        if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
            throw new Error('Supabase not connected');
        }
        
        const { data, error } = await supabaseClient
            .from('system_metrics')
            .select('*')
            .gte('timestamp', new Date(Date.now() - getTimeRangeMs(timeRange)).toISOString())
            .order('timestamp', { ascending: false });
            
        if (error) throw error;
        return data;
    },
    
    // Get pipeline status
    async getPipelineStatus() {
        if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
            throw new Error('Supabase not connected');
        }
        
        const { data, error } = await supabaseClient
            .from('pipeline_operations')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(1)
            .single();
            
        if (error) throw error;
        return data;
    }
};

// =====================================
// REAL-TIME SUBSCRIPTIONS
// =====================================

// Subscribe to real-time changes
function subscribeToRealtime(table, callback, options = {}) {
    if (!supabaseClient || !supabaseConnectionStatus.isConnected) {
        console.warn('Cannot subscribe to realtime: Supabase not connected');
        return null;
    }
    
    const channelName = `${table}-${Date.now()}`;
    
    const channel = supabaseClient
        .channel(channelName)
        .on('postgres_changes', {
            event: '*',
            schema: 'public',
            table: table,
            ...options
        }, (payload) => {
            console.log(`Real-time update for ${table}:`, payload);
            if (callback) callback(payload);
        })
        .subscribe((status) => {
            console.log(`Subscription status for ${table}:`, status);
        });
        
    realtimeChannels.set(channelName, channel);
    return channelName;
}

// Unsubscribe from real-time channel
function unsubscribeFromRealtime(channelName) {
    const channel = realtimeChannels.get(channelName);
    if (channel) {
        channel.unsubscribe();
        realtimeChannels.delete(channelName);
        console.log(`Unsubscribed from channel: ${channelName}`);
    }
}

// Unsubscribe from all channels
function unsubscribeFromAllRealtime() {
    realtimeChannels.forEach((channel, channelName) => {
        channel.unsubscribe();
    });
    realtimeChannels.clear();
    console.log('Unsubscribed from all real-time channels');
}

// =====================================
// UTILITY FUNCTIONS
// =====================================

// Convert time range to milliseconds
function getTimeRangeMs(range) {
    const ranges = {
        '15m': 15 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '6h': 6 * 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        '7d': 7 * 24 * 60 * 60 * 1000
    };
    return ranges[range] || ranges['1h'];
}

// Debounce function for frequent updates
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

// Cache for localStorage
const CacheManager = {
    set(key, data, ttl = 300000) { // 5 minutes default TTL
        const item = {
            data,
            timestamp: Date.now(),
            ttl
        };
        localStorage.setItem(`supabase_cache_${key}`, JSON.stringify(item));
    },
    
    get(key) {
        const item = localStorage.getItem(`supabase_cache_${key}`);
        if (!item) return null;
        
        const parsed = JSON.parse(item);
        const now = Date.now();
        
        if (now - parsed.timestamp > parsed.ttl) {
            localStorage.removeItem(`supabase_cache_${key}`);
            return null;
        }
        
        return parsed.data;
    },
    
    clear() {
        Object.keys(localStorage)
            .filter(key => key.startsWith('supabase_cache_'))
            .forEach(key => localStorage.removeItem(key));
    }
};

// Export global objects
window.SupabaseClient = {
    initialize: initializeSupabaseClient,
    get client() { return supabaseClient; }, // Use getter instead of function
    status: () => supabaseConnectionStatus,
    articles: SupabaseArticles,
    monitoring: SupabaseMonitoring,
    subscribe: subscribeToRealtime,
    unsubscribe: unsubscribeFromRealtime,
    unsubscribeAll: unsubscribeFromAllRealtime,
    cache: CacheManager,
    utils: {
        debounce,
        getTimeRangeMs
    }
};

console.log('Supabase client module loaded');