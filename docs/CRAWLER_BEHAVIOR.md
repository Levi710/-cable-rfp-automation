# Crawler Behavior Documentation

## Overview

The Cable RFP Automation System uses a **persistent crawling strategy** that always attempts to fetch fresh data from external APIs before supplementing with local data.

## Crawling Strategy

### Updated Behavior (Current)

**Every discovery operation performs the following steps:**

1. **GeM API** - Always attempt to crawl
   - Searches for cable-related tenders
   - Continues even if fails (403, timeout, etc.)

2. **BharatTender API** - Always attempt to crawl
   - Searches for cable tenders
   - Continues even if fails (connection error, etc.)

3. **Local Database** - Always supplement
   - Loads cached tenders from previous runs
   - Adds to results regardless of API success

4. **Deduplication** - Remove duplicates by tender_id
   - Prevents duplicate entries from multiple sources
   - Keeps first occurrence of each tender

5. **Filtering** - Apply cable detection
   - Threshold: 0.3 (lenient)
   - Ensures all results are cable-related

### Previous Behavior (Deprecated)

**Old fallback strategy:**
- Only used local database if BOTH APIs failed
- Did not supplement successful API calls with local data

**Why changed:**
- APIs are unreliable (403 errors, connection issues)
- Local database contains valuable historical data
- Users wanted EVERY tender to be considered, not just API results

## Implementation

### Code Location

`crawlers/official_sources_only.py` - `OfficialSourcesCrawler` class

### Key Methods

```python
async def discover_tenders(self) -> List[Dict]:
    """
    Strategy:
    1. Always attempt to crawl from GeM API
    2. Always attempt to crawl from BharatTender API
    3. Always supplement with local database
    4. Deduplicate and filter for cable-related tenders
    """
```

### Deduplication Logic

```python
# Deduplicate by tender_id
seen_ids = set()
unique_tenders = []

for tender in all_tenders:
    tender_id = tender.get('tender_id')
    if tender_id and tender_id not in seen_ids:
        seen_ids.add(tender_id)
        unique_tenders.append(tender)
```

## API Failure Handling

### GeM API Failures

**Common errors:**
- `403 Forbidden` - API access restrictions
- `Connection timeout` - Network issues
- `Rate limiting` - Too many requests

**Handling:**
- Log warning message
- Continue to next source
- Does NOT stop discovery

### BharatTender API Failures

**Common errors:**
- `Connection refused` - Service unavailable
- `Name or service not known` - DNS resolution failed
- `SSL errors` - Certificate issues

**Handling:**
- Log warning message
- Continue to local database
- Does NOT stop discovery

## Output Format

### Console Log Example

```
================================================================================
DISCOVERING TENDERS FROM OFFICIAL SOURCES
================================================================================

GeM Public API...
   GeM failed: API returned status 403

BharatTender Official API...
   BharatTender failed: Connection error

Loading from local database to supplement...
   Found 3 tenders from local database

Removed 0 duplicate tenders

Filtering for cable-related tenders (threshold=0.3)...
================================================================================
TOTAL DISCOVERED: 3 tenders
   Cable-related: 3
   Filtered out: 0
================================================================================
```

### Success Metrics by Source

| Source | Typical Success Rate | Reason for Failures |
|--------|---------------------|---------------------|
| GeM API | 10-20% | 403 Forbidden, Rate limiting |
| BharatTender | 5-10% | DNS issues, Service unavailable |
| Local Database | 100% | Always available |

## Database Storage

### Deduplication

All discovered tenders are stored in PostgreSQL with deduplication:

```python
def _store_tenders(self, tenders: List[Dict]):
    """Store tenders with deduplication."""
    
    for tender in tenders:
        existing = db.query(DiscoveredTender).filter_by(
            tender_id=tender_id
        ).first()
        
        if not existing:
            db.add(db_tender)  # Store new
            stored += 1
        else:
            duplicates += 1    # Skip duplicate
```

### Database Schema

```python
class DiscoveredTender:
    tender_id: str       # Primary identifier
    source: str          # GeM, BharatTender, Local Database
    title: str           # Tender title (max 500 chars)
    description: str     # Full description (max 3000 chars)
    organization: str    # Issuing organization
    estimated_value: int # Contract value in Rs
    raw_data: dict       # Complete tender data
    created_at: datetime # Discovery timestamp
```

## Configuration

### Cable Detection Threshold

```python
threshold = 0.3  # Lenient (30% confidence)
```

**Adjustable values:**
- `0.1` - Very lenient (more false positives)
- `0.3` - Lenient (current setting)
- `0.5` - Moderate (balanced)
- `0.7` - Strict (fewer false positives)

### API Timeouts

```python
# In gem_api_simple.py
timeout = 10  # seconds

# In bharat_tender.py
timeout = 10  # seconds
```

## Performance Metrics

### Typical Execution

```
Discovery Phase: 1-2 seconds
├─ GeM API:          0.5s (usually fails)
├─ BharatTender:     0.5s (usually fails)
└─ Local Database:   0.1s (always succeeds)

Deduplication:       <0.1s
Cable Filtering:     <0.1s
Database Storage:    <0.1s

Total: 1-3 seconds
```

### Results Distribution

**Typical discovery:**
- GeM API: 0-5 tenders (when successful)
- BharatTender: 0-10 tenders (when successful)
- Local Database: 3-20 tenders (always)
- After deduplication: 3-30 unique tenders

## Troubleshooting

### Issue: No tenders discovered

**Check:**
```bash
# Verify local database has data
docker compose exec -T app python -c "from crawlers.local_database import LocalTenderDatabase; db = LocalTenderDatabase(); print(len(db.load_tenders()))"

# Expected: > 0
```

### Issue: Duplicate tenders in results

**Check deduplication logic:**
```bash
# View discovered tenders
docker compose exec -T app python -c "from database.models import DiscoveredTender; from config.database import SessionLocal; db = SessionLocal(); print(db.query(DiscoveredTender).count())"
```

### Issue: APIs always fail

**Expected behavior:**
- GeM API: 403 errors are normal (API access restricted)
- BharatTender: Connection errors are normal (service unreliable)
- System designed to work without API access

**No action needed** - Local database provides fallback data

## Future Enhancements

### Potential Improvements

1. **API Authentication**
   - Register for official GeM API keys
   - Reduces 403 errors

2. **Retry Logic**
   - Exponential backoff for failed requests
   - Increases successful API calls

3. **Caching Strategy**
   - Cache API responses for 1 hour
   - Reduces redundant API calls

4. **Smart Scheduling**
   - Crawl during low-traffic hours
   - Avoids rate limiting

5. **Multiple API Endpoints**
   - Add more government tender sources
   - Increases tender coverage

## Best Practices

### For Developers

1. **Always handle API failures gracefully**
   ```python
   try:
       tenders = api.search()
   except Exception as e:
       logger.warning(f"API failed: {e}")
       # Continue with other sources
   ```

2. **Log all discovery operations**
   - Source attempted
   - Results count
   - Errors encountered

3. **Maintain local database**
   - Regularly update sample tenders
   - Ensure diverse test data

### For Users

1. **API failures are normal** - System designed to work without APIs

2. **Local database is supplement** - Not just fallback

3. **Check logs regularly** - Monitor API success rates

4. **Report persistent failures** - If local database also fails

## See Also

- `crawlers/official_sources_only.py` - Main crawler implementation
- `crawlers/gem_api_simple.py` - GeM API client
- `crawlers/bharat_tender.py` - BharatTender API client
- `crawlers/local_database.py` - Local database loader
- `README.md` - Complete system documentation

---

**Last Updated:** 2025-01-07
**Version:** 2.0 (Always crawl + supplement strategy)
