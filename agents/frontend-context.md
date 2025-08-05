# Frontend Dashboard Context
Updated: 2025-08-03

## Current State
- Monitoring dashboard at localhost:8001 (vanilla JS + Tailwind)
- Database visualizer in ai-news-db-visualizer/ (React + Ant Design)
- Real-time metrics display working
- Articles tab filters are fully functional

## Active Issues
- Dashboard performance degradation with large datasets
- Mobile responsive layout incomplete
- Dark mode has contrast issues
- Auto-refresh causes memory leaks after ~1 hour
- Media files show as "-" (need to verify if data exists)

## Key Files
- monitoring/static/index.html (main dashboard)
- monitoring/static/monitoring.js (dashboard logic)
- monitoring/app.py (FastAPI backend)
- monitoring/api.py (API endpoints)
- ai-news-db-visualizer/frontend/src/App.tsx (React version)

## Recent Changes
- Fixed Articles tab filtering (all 3 filter types now work)
- Added media file count to API query
- Fixed date_filter parameter passing
- Visual filter indicators working correctly
- Clear filter button functioning properly