# CLAUDE.md - AI News Parser Clean

## Project: AI News Parser
- **Purpose**: AI news collection, translation and publication 
- **Stack**: Python, Supabase, Firecrawl API, DeepSeek API, OpenAI API, FastAPI
- **Location**: Desktop/AI DEV/ainews-clean/
- **Status**: Production ready

## System Architecture
- **Database**: Supabase (Claude uses MCP, system uses API)
  - Project: `mtguynupyltlqiwhmilc`
  - Claude access: `mcp__supabase__*` tools
  - System access: `services/supabase_client.py`
- **Sources**: 30 (25 RSS + 5 Google Alerts)
- **APIs**: Firecrawl (parsing), DeepSeek (translation), OpenAI GPT-3.5 (media)
- **Monitoring**: FastAPI dashboard at http://localhost:8001
- **WordPress**: https://ailynx.ru with custom SEO plugin

## Main Commands
```bash
cd "Desktop/AI DEV/ainews-clean"

# Find new articles (Phase 1)
python core/main.py --rss-discover

# Process ONE article (Phases 2-5)
python core/main.py --single-pipeline

# Stats and sources
python core/main.py --stats
python core/main.py --list-sources

# Monitoring dashboard
cd monitoring && ./start_monitoring.sh
```

## Agent System

### Available Agents (use exact names)
1. **frontend-dashboard-specialist** - UI/UX, dashboard, Playwright tests
2. **source-manager** - RSS sources, feed health, validation
3. **database-optimization-specialist** - DB queries, migrations, schema
4. **news-crawler-specialist** - News collection, Firecrawl API
5. **monitoring-performance-specialist** - System monitoring, performance

### Agent Workflow
1. Read context: `agents/[name]-context.md`
2. Use Task tool with exact agent name
3. Update context after completion

## WordPress Access
- **URL**: https://ailynx.ru
- **Username**: admin
- **App Password**: tE85 PFT4 Ghq9 nl26 nQlt gBnG

## MCP Servers
- **supabase**: Main database access
- **ainews-sqlite**: Legacy SQLite (read-only)
- **ainews-monitoring-db**: Monitoring metrics
- **playwright**: Browser automation
- **shadcn-ui**: UI components
- **context7**: Documentation lookup

## Project Structure
```
ainews-clean/
├── core/               # Main pipeline logic
├── services/           # API services
├── monitoring/         # Web dashboard
├── agents/            # Agent contexts
├── prompts/           # LLM prompts
├── data/              # Config and media
└── docs/              # Documentation
```

## Documentation
- Main README: `/README.md`
- Architecture: `/docs/architecture.md`
- API Reference: `/docs/API/API_REFERENCE.md`
- Monitoring: `/monitoring/README.md`

## Critical Rules
1. Pipeline runs ONLY from dashboard (never from terminal)
2. ONE article per run (no batch processing)
3. Test with example.com URLs only
4. Never create files unless necessary
5. Always prefer editing over creating new files