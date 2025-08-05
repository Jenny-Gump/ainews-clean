# AI News Parser - Quick Reference

## Project Structure
```
ainews/
├── ai-news-parser/         # Main parser code
│   ├── main.py            # Entry point
│   ├── monitoring/        # Dashboard & monitoring
│   ├── data/             # Databases
│   └── sources.json      # Source configurations
├── agents/               # Agent context files
└── docs/                # Documentation

## Key Commands
```bash
# Navigate to project
cd "Desktop/AI DEV/ainews/ai-news-parser"

# Activate environment
source venv/bin/activate

# Run crawlers
python main.py --crawl --days-back 7
python main.py --rss-scrape --days-back 7

# Start monitoring
cd monitoring && python app.py

# Check sources
python source_validator.py
```

## Database Locations
- Main: `data/ainews.db`
- Monitoring: `data/monitoring.db`

## API Endpoints
- Dashboard: http://localhost:8001
- API: http://localhost:8001/api/

## MCP Servers
- `mcp__ainews-sqlite` - Articles database
- `mcp__ainews-monitoring-db` - Metrics database
- `mcp__playwright` - UI testing
- `mcp__shadcn-ui` - UI components

## Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Memory leak | Restart monitoring service |
| 429 errors | Reduce rate limit in config |
| RSS broken | Run RSS health check |
| Slow queries | Check database indexes |