# Frontend Dashboard Context
Updated: 2025-08-09

## Current State
- Monitoring dashboard at localhost:8001 (vanilla JS + Tailwind)
- Database visualizer in ai-news-db-visualizer/ (React + Ant Design)
- Real-time metrics display working
- Articles tab filters are fully functional

## Fixed Issues (2025-08-09)
- ✅ Single Pipeline button state persistence fixed with 15-second grace period
- ✅ Process detection improved with retry logic (3 attempts over 1.5 seconds)
- ✅ Added "Starting..." and "Stopping..." intermediate button states
- ✅ Prevented race condition between UI state and process detection

## Fixed Issues (2025-08-08)
- ✅ WebSocket log streaming errors fixed (null pointer exceptions)
- ✅ RSS Discovery button functionality restored with better logging
- ✅ Disabled defunct /ws/logs WebSocket endpoint

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
- monitoring/api_rss_endpoints.py (Extract system endpoints)
- ai-news-db-visualizer/frontend/src/App.tsx (React version)

## Recent Changes (2025-08-09)
- Added grace period tracking variables (pipelineStartupGrace, rssStartupGrace)
- Modified updateExtractButtonStates() to respect 15-second grace period
- Added check_process_with_retry() function for better process detection
- Set grace period timestamps when starting processes
- Clear grace periods on errors or when processes stop

## Recent Changes (2025-08-08)
- Fixed Articles tab filtering (all 3 filter types now work)
- Added media file count to API query
- Fixed date_filter parameter passing
- Visual filter indicators working correctly
- Clear filter button functioning properly

## Technical Details of Button Fix
1. **Problem**: Button state was being overridden by automatic status checks every 5 seconds
2. **Root Cause**: Process startup delay (6-10 seconds) vs status check interval (5 seconds)
3. **Solution**: 15-second grace period prevents status updates from overriding button state during startup
4. **Implementation**:
   - Grace period variables: `pipelineStartupGrace`, `rssStartupGrace`
   - Grace period duration: `STARTUP_GRACE_PERIOD = 15000` (15 seconds)
   - Process detection retry: 3 attempts over 1.5 seconds
   - Button shows "Starting..." during initialization