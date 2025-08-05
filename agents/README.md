# Agent System Documentation

## Overview
This folder contains context files and workflows for the AI News Parser agent system.

## Files Structure
- `*-context.md` - Context files for each agent (updated after each session)
- `AGENT_WORKFLOW.md` - Guide for agents on how to work
- `COORDINATOR_CHECKLIST.md` - Checklist for coordinator
- `REPORT_TEMPLATE.md` - Template for agent session reports
- `QUICK_REFERENCE.md` - Quick reference for common tasks

## Available Agents
1. **frontend-dashboard-specialist** - UI/UX improvements
2. **news-crawler-specialist** - News collection
3. **database-optimization-specialist** - Database operations
4. **monitoring-performance-specialist** - System monitoring
5. **source-manager** - Source management

## Workflow
1. Coordinator reads agent context
2. Coordinator assigns task to agent
3. Agent completes task and reports
4. Coordinator updates agent context

## Important Rules
- Context files MUST be updated after each agent session
- Agents work only within their domain
- All changes must be tested before reporting complete