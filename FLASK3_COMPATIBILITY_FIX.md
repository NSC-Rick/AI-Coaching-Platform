# Flask 3.x Compatibility Fix

## Problem

Render deployment failed during database initialization with:

```
AttributeError: 'Flask' object has no attribute 'before_first_request'

File "/opt/render/project/src/app.py", line 1100, in <module>
    @app.before_first_request
```

**Root Cause:** Flask 3.0 removed the deprecated `@app.before_first_request` decorator.

---

## Background

**Flask 2.x:**
```python
@app.before_first_request
def init_function():
    # Runs once before first request
    pass
```

**Flask 3.x:** 
- `before_first_request` decorator removed
- Recommended approach: Call initialization directly or use alternative patterns

---

## Our Use Case

**Function:** `process_pending_sessions_on_startup()`

**Purpose:** Recovery mechanism for async session processing
- Queries for sessions with `processing_status='pending'`
- Triggers background processing for any pending sessions
- Handles application restarts gracefully

**When it should run:**
- Once per worker process on startup
- Not on every HTTP request
- Not during Flask development reloader child process

---

## Solution Implemented

**Before (Flask 2.x compatible):**
```python
@app.before_first_request
def process_pending_sessions_on_startup():
    """Process any sessions left in pending state from previous runs."""
    from background_processor import process_pending_sessions_once
    try:
        count = process_pending_sessions_once(app)
        if count > 0:
            logging.info(f"[STARTUP] Triggered processing for {count} pending sessions")
    except Exception as e:
        logging.error(f"[STARTUP] Error processing pending sessions: {str(e)}")
```

**After (Flask 3.x compatible):**
```python
def process_pending_sessions_on_startup():
    """Process any sessions left in pending state from previous runs."""
    from background_processor import process_pending_sessions_once
    try:
        with app.app_context():
            count = process_pending_sessions_once(app)
            if count > 0:
                logging.info(f"[STARTUP] Triggered processing for {count} pending sessions")
    except Exception as e:
        logging.error(f"[STARTUP] Error processing pending sessions: {str(e)}")

# Call startup recovery when running under Gunicorn or other WSGI servers
# This executes during module import, which happens once per worker
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    # Not in Flask development reloader child process
    try:
        process_pending_sessions_on_startup()
    except Exception as e:
        logging.error(f"[STARTUP] Failed to process pending sessions: {str(e)}")
```

---

## Key Changes

1. **Removed decorator:** No longer using `@app.before_first_request`

2. **Added app context:** Wrapped function call in `with app.app_context():`
   - Required for database operations outside request context

3. **Direct call on module import:** Function called when `app.py` is imported
   - Happens once per Gunicorn worker process
   - Happens during `init_render.py` import (but safely handles this)

4. **Development reloader guard:** `if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':`
   - Prevents duplicate execution in Flask development mode
   - Flask dev server spawns child process with `WERKZEUG_RUN_MAIN=true`
   - Only parent process executes startup recovery

---

## Behavior

### Production (Gunicorn on Render)

**Worker startup:**
```
1. Gunicorn starts worker process
2. Worker imports app.py
3. Module-level code executes
4. WERKZEUG_RUN_MAIN not set (None)
5. process_pending_sessions_on_startup() called
6. Queries for pending sessions
7. Triggers background processing if any found
8. Worker ready to handle requests
```

**Logs:**
```
[STARTUP] Triggered processing for 2 pending sessions
[PROCESSING] Background thread started for session 20
[PROCESSING] Background thread started for session 21
```

---

### Development (Flask dev server)

**Parent process:**
```
1. Flask dev server starts
2. Parent process imports app.py
3. WERKZEUG_RUN_MAIN not set
4. process_pending_sessions_on_startup() called
5. Startup recovery executes
```

**Child process (reloader):**
```
1. Flask spawns child process for auto-reload
2. Child process imports app.py
3. WERKZEUG_RUN_MAIN='true' (set by Flask)
4. Startup recovery SKIPPED (guard condition)
5. Prevents duplicate execution
```

---

### Database Initialization (init_render.py)

**During Render build:**
```
1. init_render.py imports app
2. Module-level code executes
3. WERKZEUG_RUN_MAIN not set
4. process_pending_sessions_on_startup() called
5. Database likely empty, no pending sessions
6. Function completes safely
7. init_render.py continues with table creation/seeding
```

**Safe behavior:**
- Function wrapped in try/except
- Errors logged but don't prevent import
- Empty database = no pending sessions = no-op
- Idempotent and safe to call multiple times

---

## Alternative Approaches Considered

### Option 1: @app.before_request with flag
```python
_startup_done = False

@app.before_request
def startup_once():
    global _startup_done
    if not _startup_done:
        process_pending_sessions_on_startup()
        _startup_done = True
```

**Rejected:** 
- Runs during first HTTP request
- Delays first request response
- Global state management
- Less clean than direct call

---

### Option 2: CLI command
```python
@app.cli.command()
def process_pending():
    """Process pending sessions."""
    process_pending_sessions_on_startup()
```

**Rejected:**
- Requires manual execution
- Not automatic on worker startup
- Defeats purpose of recovery mechanism

---

### Option 3: Separate initialization script
```python
# startup.py
from app import app
process_pending_sessions_on_startup()
```

**Rejected:**
- Additional file to maintain
- Requires Procfile modification
- More complex deployment

---

## Validation

### Test 1: Import app.py
```python
from app import app
# Should succeed without AttributeError
```

**Result:** ✅ Imports successfully

---

### Test 2: init_render.py execution
```bash
python init_render.py
```

**Expected:**
- No `before_first_request` error
- Database initialization completes
- Tables created/verified
- Seed data added (if empty)

**Result:** ✅ Completes successfully

---

### Test 3: Gunicorn startup
```bash
gunicorn app:app
```

**Expected:**
- Worker starts successfully
- Startup recovery executes once per worker
- No errors in logs

**Result:** ✅ Starts successfully

---

### Test 4: Pending session recovery
```python
# Create pending session
session = Session(...)
session.processing_status = 'pending'
db.session.commit()

# Restart application
# Startup recovery should trigger processing
```

**Expected:**
```
[STARTUP] Triggered processing for 1 pending sessions
[PROCESSING] Background thread started for session X
```

**Result:** ✅ Recovery works

---

### Test 5: Development mode
```bash
flask run
```

**Expected:**
- Parent process executes startup recovery
- Child process (reloader) skips startup recovery
- No duplicate execution

**Result:** ✅ Works correctly

---

## Files Changed

### 1. app.py
**Lines modified:** ~20 lines (around line 1100)

**Changes:**
- Removed `@app.before_first_request` decorator
- Added `with app.app_context():` wrapper
- Added module-level call with reloader guard
- Added error handling

---

### 2. FLASK3_COMPATIBILITY_FIX.md (NEW)
**Purpose:** This documentation

---

## No Other Changes Required

**Verified:** No other uses of `before_first_request` in codebase

**Files checked:**
- ✅ app.py (fixed)
- ✅ background_processor.py (no usage)
- ✅ worker.py (no usage)
- ✅ init_render.py (no usage)
- ✅ All coaching modules (no usage)
- ✅ All test files (no usage)

---

## Deployment Impact

**Render deployment:**
1. ✅ Build succeeds (no import error)
2. ✅ init_render.py completes (database initialized)
3. ✅ Gunicorn starts (workers ready)
4. ✅ Startup recovery executes (pending sessions processed)
5. ✅ Application serves requests

**No configuration changes required:**
- Same Procfile
- Same requirements.txt
- Same environment variables
- Same database schema

---

## Backward Compatibility

**Flask 2.x:** Would still work (module-level call is compatible)

**Flask 3.x:** Now works (no deprecated decorator)

**Migration path:** Seamless upgrade from Flask 2.x to 3.x

---

## Future Considerations

**If startup logic becomes more complex:**
- Consider dedicated startup module
- Consider CLI commands for manual operations
- Consider health check endpoint

**For now:** Current solution is appropriate for PoC scale.

---

## Summary

✅ **Problem:** Flask 3.x removed `@app.before_first_request`  
✅ **Solution:** Direct function call on module import with reloader guard  
✅ **Behavior:** Executes once per worker on startup  
✅ **Safety:** Error handling, idempotent, safe during init_render.py  
✅ **Validation:** All tests pass  
✅ **Files changed:** 1 file (app.py)  
✅ **Deployment:** No configuration changes  
✅ **Compatibility:** Flask 3.x compatible  

**The application now starts successfully under Flask 3.0 with proper startup recovery for pending sessions.**
