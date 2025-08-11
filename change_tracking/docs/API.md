# Firecrawl changeTracking API Documentation

## Overview

Firecrawl's changeTracking feature automatically detects changes in web content between scraping sessions. This is ideal for monitoring news sites and detecting new articles or content updates.

## How it works

1. **First scrape** - Firecrawl stores a snapshot of the content
2. **Subsequent scrapes** - Compares current content with stored snapshot
3. **Returns status** - `new`, `changed`, or `same`

## API Usage

### Basic Request

```javascript
const response = await fetch('https://api.firecrawl.dev/v1/scrape', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com/news',
    formats: ['markdown', 'changeTracking']
  })
});
```

### Response Format

```javascript
{
  "success": true,
  "data": {
    "markdown": "# Page Title\n\nContent here...",
    "changeTracking": {
      "changeStatus": "new",      // or "changed" or "same"
      "changeDetected": true,     // boolean
      "previousSnapshot": null,   // for new pages
      "currentSnapshot": "hash123" // content hash
    }
  }
}
```

## Change Status Values

| Status | Description | Action Required |
|--------|-------------|----------------|
| `new` | First time scraping this URL | Create new tracking record |
| `changed` | Content has changed since last scrape | Update existing record |
| `same` | No changes detected | Update last_checked timestamp only |

## Python Implementation

```python
from services.firecrawl_client import FirecrawlClient

async def monitor_page(url: str):
    async with FirecrawlClient() as client:
        result = await client.scrape_url(
            url, 
            formats=['markdown', 'changeTracking']
        )
        
        change_tracking = result.get('changeTracking', {})
        status = change_tracking.get('changeStatus', 'unknown')
        
        if status == 'new':
            print(f"New page discovered: {url}")
        elif status == 'changed':
            print(f"Changes detected on: {url}")
        elif status == 'same':
            print(f"No changes on: {url}")
```

## Best Practices

### Rate Limiting
- Max 5 concurrent requests
- 2-second pause between batches
- Handle 429 errors gracefully

### Error Handling
```python
try:
    result = await client.scrape_url(url, formats=['markdown', 'changeTracking'])
except Exception as e:
    if 'timeout' in str(e).lower():
        # Retry with longer timeout
        pass
    elif 'rate limit' in str(e).lower():
        # Wait and retry
        await asyncio.sleep(60)
    else:
        # Log error and continue
        logger.error(f"Failed to scrape {url}: {e}")
```

### Content Validation
- Check for minimum content length
- Verify markdown format
- Validate page structure didn't break

## Limitations

- changeTracking only works for same URL
- Content must be publicly accessible
- Some dynamic content may cause false positives
- API rate limits apply (check your plan)

## Troubleshooting

### Common Issues

**False Positives**:
- Dynamic timestamps in content
- Rotating ads or widgets
- Session-specific content

**Solutions**:
- Use content hashing as secondary validation
- Filter out known dynamic elements
- Implement content similarity checking

**Missing Changes**:
- CDN caching delays
- Gradual content rollouts
- A/B testing variations

**Solutions**:
- Add cache-busting parameters
- Increase check frequency
- Multiple checks over time

## Cost Optimization

- Use batch processing (5 URLs per batch)
- Implement smart scheduling (check popular sources more frequently)
- Cache results locally to avoid redundant checks
- Monitor API usage and optimize based on change patterns

## Integration Examples

### With Database
```python
def process_change_result(url: str, result: dict):
    change_tracking = result.get('changeTracking', {})
    status = change_tracking.get('changeStatus')
    
    if status == 'new':
        db.create_tracked_article(url, result['markdown'])
    elif status == 'changed':
        db.update_tracked_article(url, result['markdown'])
    else:  # same
        db.touch_last_checked(url)
```

### With Notifications
```python
async def notify_on_changes(results: list):
    new_pages = [r for r in results if r['status'] == 'new']
    changed_pages = [r for r in results if r['status'] == 'changed']
    
    if new_pages or changed_pages:
        await send_notification(f"Found {len(new_pages)} new and {len(changed_pages)} changed pages")
```

## References

- [Firecrawl API Documentation](https://docs.firecrawl.dev)
- [changeTracking Feature Guide](https://docs.firecrawl.dev/features/change-tracking)
- [Rate Limits and Pricing](https://firecrawl.dev/pricing)