# AI News Monitoring System

A comprehensive monitoring and control dashboard for the AI News Parser Clean system.

## 🚀 Current Status: **FULLY OPERATIONAL**

✅ All core systems working  
✅ Memory monitoring restored  
✅ Refresh functionality fixed  
✅ Database management active  
✅ Process control operational  

## Features

### 📊 Dashboard Tabs
- **Control Panel**: Process management, database operations, parsing progress
- **Articles**: Article statistics and content status monitoring  
- **Memory**: Real-time system resources and process monitoring
- **RSS Feeds**: Source health monitoring and feed status
- **Errors**: Error tracking and analysis

### 🎯 Core Functionality
- **Real-time System Monitoring**: CPU, memory, disk usage with live updates
- **Process Control**: Start/stop RSS discovery, parsing, and media phases
- **Database Management**: Clean articles by status (pending/completed/failed)
- **Article Management**: View and delete individual articles with cascade deletion
- **Memory Monitoring**: Track AI News processes and resource consumption
- **WebSocket Updates**: Real-time dashboard updates every 30 seconds
- **RSS Feed Health**: Monitor 27 RSS feeds with health scoring
- **Error Analysis**: Comprehensive error tracking and context collection

## 🛠 Installation & Setup

### Prerequisites
- Python 3.13+ 
- SQLite (included with Python)
- Required packages (see requirements.txt)

### Quick Start
```bash
# From project root
cd "Desktop/AI DEV/ainews-clean/monitoring"

# Start monitoring system
./start_monitoring.sh
```

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start directly
python3 app.py
```

## 📱 Usage

**Dashboard URL**: http://localhost:8001

### Process Management
- **Start RSS**: Begin RSS feed discovery
- **Start Parse**: Parse pending articles with Firecrawl Extract API
- **Start Media**: Download and process media files
- **Database Cleanup**: Remove articles by status

### Article Management
- **View Articles**: Browse all articles in the Articles tab
- **Delete Articles**: Click the X button next to any article to delete it
- **Cascade Deletion**: Automatically removes related media files and links

### System Monitoring
- **Memory Tab**: View process memory usage, CPU consumption
- **Real-time Metrics**: Live system resource monitoring
- **Process Control**: Kill individual processes or all AI News processes

## 🔌 API Endpoints

### Extract System Control
- `POST /api/extract/rss/start` - Start RSS Discovery phase
- `POST /api/extract/parse/start` - Start Extract API parsing phase  
- `POST /api/extract/media/start` - Start media download phase
- `GET /api/extract/status` - Get status of all Extract processes
- `GET /api/extract/last-parsed` - Get global last_parsed timestamp
- `PUT /api/extract/last-parsed` - Update global last_parsed timestamp

### Database Management
- `GET /api/extract/articles/stats` - Get article statistics by status
- `DELETE /api/extract/articles/by-status/{status}` - Delete articles by status

### Articles Management
- `GET /api/articles` - Get paginated list of articles
- `GET /api/articles/{article_id}` - Get specific article details
- `DELETE /api/articles/{article_id}` - Delete specific article and related data

### Memory & System Monitoring
- `GET /api/memory/current` - Get current memory metrics
- `GET /api/memory/processes` - Get AI News process list
- `POST /api/memory/kill/{pid}` - Kill specific process
- `POST /api/memory/kill-all` - Kill all AI News processes

### RSS Monitoring  
- `GET /api/rss/health` - Get RSS feed health summary
- `GET /api/rss/sources` - Get detailed source information

### Real-time Updates
- **WebSocket**: `/ws` - Real-time dashboard updates
- **Log Stream**: `/ws/logs` - Live log streaming

## 🗄️ Database Architecture

### Main Databases
- **Main Database**: `../data/ainews.db` - Articles, sources, media
- **Monitoring Database**: `../data/monitoring.db` - System metrics, monitoring data

### Monitoring Database Schema
- **system_metrics** - CPU, memory, disk usage over time
- **error_logs** - Error tracking with context
- **source_metrics** - RSS feed health scores
- **api_calls** - Extract API usage tracking
- **parsing_progress** - Phase execution history

## 📁 Project Structure

```
monitoring/
├── app.py              # Main FastAPI application with lifespan management
├── extract_api.py      # Extract system API endpoints  
├── api.py              # Monitoring API routes
├── database.py         # Database operations and models
├── collectors.py       # System metrics collectors
├── memory_monitor.py   # Memory monitoring and cleanup
├── process_manager.py  # Process control and management
├── rss_monitor.py      # RSS feed health monitoring
├── automation.py       # Automated recovery and optimization
├── parsing_tracker.py  # Phase progress tracking
├── log_processor.py    # Log analysis and processing
├── static/
│   ├── index.html      # Main dashboard interface
│   ├── monitoring.js   # Dashboard JavaScript
│   └── js/
│       ├── log-filter.js      # Smart log filtering
│       └── overall-progress.js # Progress visualization
└── start_monitoring.sh # Startup script
```

## 🔄 Three-Phase Process Control

The monitoring system manages the AI News Parser's three phases:

### Phase 1: RSS Discovery 
- Scans 27 RSS feeds for new articles
- Updates source last_parsed timestamps  
- Creates pending articles in database

### Phase 2: Content Parsing
- Processes pending articles via Firecrawl Extract API
- Extracts clean content, summaries, tags
- Updates article status to completed/failed

### Phase 3: Media Processing  
- Downloads article images and media
- Deduplicates and optimizes media files
- Links media to articles in database

### Process Management Features
- **Independent Control**: Start/stop each phase separately
- **Status Monitoring**: Real-time process status and PID tracking
- **Resource Monitoring**: Memory and CPU usage per process
- **Automatic Restart**: Configurable restart on failure
- **Log Streaming**: Real-time log output via WebSocket

## 🚨 System Health & Alerts

### Memory Management
- **10GB Memory Limit** with automatic cleanup
- **Process Monitoring** with resource usage tracking
- **Emergency Callbacks** for critical memory situations
- **Cache Management** for optimal performance

### RSS Feed Health
- **Health Scoring** for all 27 RSS feeds
- **Stale Detection** for inactive feeds  
- **Error Tracking** for feed failures
- **Automatic Recovery** attempts

### Error Analysis
- **Context Collection** for meaningful error reporting
- **Error Grouping** for pattern identification

## 🔧 Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check for existing instances
ps aux | grep monitoring
kill -9 [PID]  # Kill existing processes

# Start fresh
cd monitoring && ./start_monitoring.sh
```

**Memory Issues**
- Monitor Memory tab for high usage
- Use "Kill All AI News Processes" if needed
- Check logs for memory-related errors

**Database Locks**
- Restart monitoring service
- Check for long-running queries
- Use database cleanup functions

## 📝 Логирование

### Структура логов
- **Системные логи**: `../logs/monitoring/system.log` - основные логи мониторинга
- **Логи контент-парсинга**: `../logs/content_parsing/` - логи обработки статей
- **Логи медиа-обработки**: `../logs/media_processing/` - логи скачивания медиа
- **Логи RSS-поиска**: `../logs/rss_discovery/` - логи сканирования RSS
- **Экспорты ошибок**: `../logs/error_exports/` - детальные отчеты об ошибках

### Управление логами
```bash
# Запуск с ротацией логов
./start_monitoring.sh

# Остановка мониторинга
./stop_monitoring.sh

# Ручная ротация логов
logrotate -s /tmp/logrotate.state ../logs/logrotate.conf
```

### Ротация логов
- **Автоматическая ротация** при превышении 50MB
- **Сохранение последних 5-7 файлов** в зависимости от типа
- **Сжатие старых логов** для экономии места
- **Максимальный возраст**: 14-30 дней в зависимости от типа

## 🎯 Recent Updates (August 2025)

✅ **Article Deletion Feature** - Added delete buttons (X) next to each article in dashboard  
✅ **Individual Article Management** - Delete specific articles with cascade deletion of related data  
✅ **Centralized Logging Integration** - All monitoring operations use app_logging module  
✅ **Fixed Refresh Dashboard Button** - Now properly updates all data and timestamps  
✅ **Restored Memory Monitoring** - Complete system resource tracking in Memory tab  
✅ **Enhanced Process Control** - Better process management and status tracking  
✅ **Improved Error Handling** - More robust error collection and display  
✅ **Database Management** - Article cleanup by status with UI controls  
✅ **Performance Optimization** - Reduced memory usage and improved WebSocket efficiency