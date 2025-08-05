# CLAUDE.md - AI News Parser Clean System

## Project: AI News Parser Clean
- **Purpose**: Streamlined AI news collection using Firecrawl Extract API + WordPress publishing
- **Stack**: Python, SQLite, Firecrawl Extract API, DeepSeek API, FastAPI monitoring
- **Location**: Desktop/AI DEV/ainews-clean/
- **Version**: 1.2.0 - Updated media handling (no caption/description)
- **Status**: Production ready with simplified media metadata

## System Overview
Clean implementation of AI News Parser focused on:
- **Extract API only** - No RSS+Scrape complexity
- **26 news sources** - 25 RSS feeds + Google Alerts
- **Five-phase processing** - RSS → Content → Media → WP Prep → WP Publish
- **WordPress ready** - Automated translation and SEO optimization
- **Clean architecture** - Clear separation of concerns
- **Image validation** - ≥300×300px, 3KB-2MB
- **Image metadata** - Only alt_text and title translated (no caption/description)

## Development Commands

### Main System
```bash
cd "Desktop/AI DEV/ainews-clean"
source venv/bin/activate                 # Always use venv!
python core/main.py --rss-full            # Full cycle (Phases 1-3)
python core/main.py --rss-discover      # Phase 1: RSS Discovery
python core/main.py --parse-pending     # Phase 2: Content Parsing  
python core/main.py --media-only        # Phase 3: Media Processing
python core/main.py --wordpress-prepare --limit 5  # Phase 4: Translate articles
python core/main.py --wordpress-publish --limit 5  # Phase 5: Publish to WordPress
python core/main.py --list-sources      # List all sources
python core/main.py --stats             # System statistics
```

### WordPress Integration
```bash
# Setup and check
python scripts/setup_wordpress.py       # Check WordPress connection
python scripts/create_categories.py     # Create categories
python scripts/create_tags.py          # Create all tags

# Publishing workflow
python core/main.py --wordpress-prepare --limit 1  # Test translate
python core/main.py --wordpress-publish --limit 1  # Test publish
```

**WordPress Site**: https://ailynx.ru/ (admin/tE85 PFT4 Ghq9 nl26 nQlt gBnG)
- ✅ 11 categories (under "Новости")
- ✅ 63 tags (models, companies, people)
- ✅ Posts published as drafts for review

### Monitoring
```bash
cd monitoring && ./start_monitoring.sh   # Start dashboard
# Access at http://localhost:8001
```

## Project Structure
```
ainews-clean/
├── core/               # Main application logic
│   ├── main.py        # Entry point
│   ├── config.py      # Configuration
│   ├── database.py    # Database operations
│   └── models.py      # Data models
├── services/          # Service modules
│   ├── rss_discovery.py      # RSS scanning
│   ├── content_parser.py     # Extract API parsing
│   ├── media_processor.py    # Media handling
│   ├── firecrawl_client.py   # Firecrawl client
│   └── wordpress_publisher.py # WordPress publishing
├── monitoring/        # Web dashboard
├── data/             # Databases and config
└── backups/          # System backups directory

```

## Agent System

### Available Agents
1. **frontend-dashboard-specialist** - Dashboard improvements
2. **source-manager** - RSS source management
3. **database-optimization-specialist** - DB operations
4. **news-crawler-specialist** - News collection (delegated to other agents)
5. **monitoring-performance-specialist** - System monitoring

### Working with Agents
- Read context: `agents/[name]-context.md`
- Use Task tool with exact agent names
- Update contexts after each session

## Key Improvements from Original
1. **Removed RSS+Scrape** - Extract API only
2. **Clean architecture** - Better separation
3. **Simplified codebase** - 75% less code
4. **Better monitoring** - Clean dashboard
5. **Smart media handling** - Deduplication
6. **Simplified image metadata** - No caption/description translation

## Database Schema
- **sources** - News sources configuration
- **articles** - Main content with Extract fields
  - Status flow: pending → parsed → published
- **media_files** - Downloaded media
- **related_links** - Related articles
- **wordpress_articles** - WordPress-ready content with translations

## WordPress Quick Access
- **Admin Panel**: https://ailynx.ru/wp-admin/ (admin/tE85 PFT4 Ghq9 nl26 nQlt gBnG)
- **API Base**: https://ailynx.ru/wp-json/wp/v2/
- **Categories**: 11 total (all under "Новости")
- **Tags**: 63 total (AI models, companies, people)
- **Status**: Ready for publishing (drafts mode)

### WordPress Stats Check
```bash
# Quick WordPress status
python -c "
from core.database import Database
db = Database()
with db.get_connection() as conn:
    total = conn.execute('SELECT COUNT(*) FROM articles WHERE content_status=\"completed\"').fetchone()[0]
    wp_ready = conn.execute('SELECT COUNT(*) FROM wordpress_articles WHERE translation_status=\"translated\" AND published_to_wp=0').fetchone()[0]
    published = conn.execute('SELECT COUNT(*) FROM wordpress_articles WHERE published_to_wp=1').fetchone()[0]
    print(f'Articles ready: {total} | Translated: {wp_ready} | Published: {published}')
"
```

## Documentation
- **[Project Overview](README.md)** - Main project documentation
- **[Documentation Hub](docs/README.md)** - All technical docs
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW.md)** - 5-phase workflow

## Important Notes
- Always use Extract API, never RSS+Scrape
- Media validation: ≥300×300px, 3KB-2MB
- Monitoring runs on port 8001
- All paths relative to project root
- **Backups directory**: `/Users/skynet/Desktop/AI DEV/ainews-clean/backups/`

## MCP Servers
- **ainews-sqlite**: Main database - `/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db`
- **ainews-monitoring-db**: Monitoring metrics - `/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db`
- **shadcn-ui**: UI components
- **context7**: Documentation
- **n8n-mcp**: Workflow automation

**Note**: Конфигурация MCP серверов находится в `.claude.json`. После изменения конфигурации нужно перезапустить Claude Desktop для применения изменений.