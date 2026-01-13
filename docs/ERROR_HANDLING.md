# Error Handling Guide

## Overview

The Property Management Chatbot provides user-friendly error messages for all common issues. Technical errors are hidden by default to avoid confusing users.

---

## Common Errors

### 1. API Quota Exceeded

**Message:**
```
I've reached my API usage limit. Please try again in a minute or contact 
your administrator for a higher quota tier.
```

**Causes:**
- Free tier daily limit reached (15-50 requests/day)
- Too many requests in short time (per-minute limit)
- Account-wide quota exhausted

**Solutions:**
- Wait 1-24 hours for quota reset
- Upgrade to paid tier ($0.35 per million tokens)
- Use a different Google Cloud account
- Reduce `MAX_RETRIES` in `.env` (currently optimized at 1)

---

### 2. API Authentication Error

**Message:**
```
I'm having trouble connecting to my AI service. Please contact your 
administrator to verify the API key configuration.
```

**Causes:**
- Invalid or expired API key
- API not enabled in Google Cloud project
- Wrong model name

**Solutions:**
1. Run `python scripts/setup_env.py` to create new API key
2. Verify API is enabled: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
3. Check `.env` file has valid `GOOGLE_API_KEY`

---

### 3. Network/Connection Error

**Message:**
```
I'm having trouble connecting to my AI service. Please check your internet 
connection and try again in a moment.
```

**Causes:**
- No internet connection
- Firewall blocking requests
- Service temporarily unavailable

**Solutions:**
- Check internet connection
- Verify firewall allows HTTPS to googleapis.com
- Wait a few minutes and retry

---

### 4. Database Error

**Message:**
```
I'm having trouble accessing the database. Please ensure the database file exists.
```

**Causes:**
- Database file missing
- File permissions issue
- Corrupted database

**Solutions:**
1. Generate database: `python scripts/generate_mock_db.py`
2. Check file exists: `property_management.db`
3. Verify file permissions

---

## Debug Mode

Enable detailed technical error messages:

**In `.env` file:**
```
DEBUG_MODE=true
```

When enabled:
- CLI shows full Python error messages
- Web UI displays technical details in expander
- Useful for developers/administrators only

---

## API Call Optimization

**The system is optimized to minimize API calls:**

| Scenario | API Calls |
|----------|-----------|
| Successful query (first try) | 2 |
| Successful query (1 retry) | 3 |
| Failed query (max retries) | 2 |
| Conversational query | 0 |

**Settings:**
- `MAX_RETRIES=1` (reduced from 3 to save quota)
- Conversational queries detected without API calls
- Error handling doesn't make additional API calls

---

## Troubleshooting Checklist

1. **Check `.env` file exists and has valid `GOOGLE_API_KEY`**
2. **Verify database exists:** `property_management.db`
3. **Test API key directly:**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('API Key:', os.getenv('GOOGLE_API_KEY')[:20] + '...')"
   ```
4. **Enable debug mode** to see technical details
5. **Check Google Cloud Console** for API status
6. **Wait if quota exceeded** - limits reset after 24 hours

---

## Contact Support

If errors persist:
1. Enable `DEBUG_MODE=true` in `.env`
2. Reproduce the error
3. Copy the technical details
4. Contact your system administrator with:
   - Error message
   - Technical details (if available)
   - Steps to reproduce
