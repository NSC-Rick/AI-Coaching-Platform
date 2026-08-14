# Deployment Guide

## Build 001 Deployment to Render

### Prerequisites

- GitHub repository with the code
- Render account

### Step 1: Prepare Repository

Ensure the following files are in your repository:
- `requirements.txt` - Python dependencies
- `app.py` - Main application file
- `.gitignore` - Excludes data/, .env, etc.
- All application code

### Step 2: Create Render Web Service

1. Log in to Render (https://render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** ai-coaching-platform (or your choice)
   - **Environment:** Python 3
   - **Python Version:** 3.12 or higher (3.14 supported)
   - **Build Command:** `pip install -r requirements.txt && python init_render.py`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free (for testing) or paid tier

**Note:** The application uses psycopg 3 for PostgreSQL connectivity, which is compatible with Python 3.14+

**Important:** The build command includes `python init_render.py` which automatically:
- Creates database tables
- Seeds PoC test data (only if database is empty)
- Is safe to run on every deployment

### Step 3: Add PostgreSQL Database

1. In Render dashboard, click "New +" and select "PostgreSQL"
2. Configure the database:
   - **Name:** ai-coaching-db (or your choice)
   - **Database:** coaching_db
   - **User:** Will be auto-generated
   - **Region:** Same as your web service
   - **Instance Type:** Free (for testing) or paid tier

3. After creation, note the **Internal Database URL**

### Step 4: Configure Environment Variables

In your Render Web Service, go to "Environment" and add:

1. **SECRET_KEY**
   - Generate a secure random key
   - Example: Use Python to generate: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Value: Your generated key

2. **DATABASE_URL**
   - This should be automatically set if you linked the PostgreSQL database
   - If not, copy the Internal Database URL from your PostgreSQL service
   - Format: `postgresql://user:password@host/database`

### Step 5: Deploy

1. Click "Manual Deploy" → "Deploy latest commit"
2. Wait for the build to complete
3. Check the build logs - you should see:
   ```
   RENDER DATABASE INITIALIZATION
   ============================================================
   Step 1: Creating database tables...
   ✓ Database tables created/verified
   
   Step 2: Checking for existing data...
   Database is empty - proceeding with seed data
   
   Step 3: Seeding PoC test data...
   ✓ Created advisor: ronda@example.com
   ✓ Created client A: sarah@example.com (Sarah's Hardware)
   ✓ Created client B: michael@example.com (Chen's Bakery)
   ✓ Seed data created successfully
   
   TEST USER CREDENTIALS
   [credentials displayed]
   
   INITIALIZATION COMPLETE
   ```

**Note:** Database initialization happens automatically during build. No manual shell commands required!

**On Subsequent Deployments:**
The initialization script detects existing data and skips seeding:
```
Step 2: Checking for existing data...
Found 3 users in database
✓ Database already contains data
Skipping seed data to avoid duplicates
INITIALIZATION COMPLETE (existing data preserved)
```

### Step 6: Verify Deployment

1. Visit your Render URL (e.g., https://ai-coaching-platform.onrender.com)
2. You should see the login page
3. Test login with seed credentials:
   - Advisor: ronda@example.com / advisor123
   - Client: sarah@example.com / client123

### Expected Behavior

**Client Portal:**
- Mobile-responsive interface
- Current pathway status
- Open commitments
- Recommended resources
- "Talk to My Coach" button (shows placeholder message)

**Advisor Portal:**
- List of assigned clients
- Client status overview
- Access to client detail pages
- Ability to add guidance

**Client Detail (Advisor View):**
- Complete client information
- Commitments, risks, events
- Learning activity
- Coaching observations
- Advisor guidance form
- Coaching context display

### Troubleshooting

**Build Fails:**
- Check that `requirements.txt` is present and valid
- Verify Python version compatibility
- Check build logs for specific errors

**Application Won't Start:**
- Verify `gunicorn app:app` command is correct
- Check that `app.py` exists and has an `app` object
- Review application logs

**Database Connection Errors:**
- Verify DATABASE_URL is set correctly
- Ensure PostgreSQL database is running
- Check that database initialization completed

**500 Errors:**
- Check application logs in Render dashboard
- Verify all environment variables are set
- Ensure database is initialized

### Post-Deployment

**Security:**
- Change default test user passwords
- Use strong SECRET_KEY
- Review and restrict database access

**Monitoring:**
- Monitor Render logs for errors
- Check application performance
- Review database usage

**Next Steps:**
- Test all functionality
- Create production users
- Plan for Build 002 features

### Render-Specific Notes

**Automatic Database Initialization:**

Render Free tier does not provide shell access, so the application uses `init_render.py` for automatic initialization:

- **First Deployment:** Creates tables and seeds PoC test data
- **Subsequent Deployments:** Detects existing data and skips seeding
- **Safe to Run Repeatedly:** No risk of duplicating data or dropping tables
- **Runs During Build:** Happens before application starts

**Local Development:**

For local development, continue using Flask CLI commands:
```bash
flask init-db      # Create tables
flask seed-data    # Seed test data
```

These commands are preserved and work identically to `init_render.py`.

**Free Tier Limitations:**
- Services spin down after 15 minutes of inactivity
- First request after spin-down will be slow (30-60 seconds)
- 750 hours/month free compute time
- Database limited to 1GB
- No shell access (use init_render.py for initialization)

**Scaling:**
- Upgrade to paid tier for always-on service
- Increase database size as needed
- Add custom domain if desired
- Paid tiers include shell access

### Database Backup

**Manual Backup:**
```bash
# In Render Shell
pg_dump $DATABASE_URL > backup.sql
```

**Automated Backups:**
- Available on paid PostgreSQL plans
- Configure in Render dashboard

### Environment Variable Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| SECRET_KEY | Yes | Flask secret key | `a1b2c3d4e5f6...` |
| DATABASE_URL | Auto | PostgreSQL connection | `postgresql://user:pass@host/db` |

### Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render web service created
- [ ] PostgreSQL database created
- [ ] Environment variables configured (SECRET_KEY, DATABASE_URL)
- [ ] Build command set to: `pip install -r requirements.txt && python init_render.py`
- [ ] Application deployed successfully
- [ ] Build logs show successful database initialization
- [ ] Test credentials displayed in build logs
- [ ] Login page accessible
- [ ] Client portal tested
- [ ] Advisor portal tested
- [ ] Client isolation verified
- [ ] Pathway loading verified
- [ ] Context builder verified

### Support

For Render-specific issues:
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com

For application issues:
- Review application logs
- Check design documents in `/docs`
- Verify against Build 001 scope in README.md
