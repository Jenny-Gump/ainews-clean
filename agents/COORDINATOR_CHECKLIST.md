# Coordinator Checklist

## Before Calling an Agent
- [ ] Read agent's context file
- [ ] Prepare clear task description
- [ ] Identify expected outcomes
- [ ] Check if task matches agent's expertise

## Task Assignment Template
```
Context: [Current state from context file]
Task: [Specific task description]
Expected Result: [What should be delivered]
Constraints: [Any limitations or requirements]
```

## After Agent Completes Task
- [ ] Review agent's report
- [ ] Update agent's context file with:
  - [ ] New "Recent Changes"
  - [ ] Updated "Active Issues"
  - [ ] Modified "Current State" (if needed)
- [ ] Verify delivered results
- [ ] Update project documentation if needed

## Context Update Example
```markdown
## Recent Changes
- 2025-08-02: Fixed dashboard memory leak, optimized refresh cycle

## Active Issues
- [RESOLVED] Memory leak in auto-refresh
- [NEW] Chart rendering slow with >1000 data points
```

## Agent Selection Guide
| If task involves... | Use this agent |
|-------------------|----------------|
| UI, visualization, dashboard | frontend-dashboard-specialist |
| Crawling, scraping, Firecrawl | news-crawler-specialist |
| SQL, migrations, DB performance | database-optimization-specialist |
| Metrics, alerts, performance | monitoring-performance-specialist |
| RSS feeds, source quality | source-manager |

## API Documentation References
| Agent | Key APIs |
|-------|----------|
| news-crawler-specialist | Firecrawl API: https://docs.firecrawl.dev/introduction |
| frontend-dashboard-specialist | Shadcn/UI: via mcp__shadcn-ui |
| database-optimization-specialist | SQLite docs: https://sqlite.org/docs.html |