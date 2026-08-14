# AI Coaching Platform

## Build 002 — AI Coaching Engine & Persistent Coaching Loop

**Current Build:** 002  
**Status:** Complete

This is the AI Coaching Platform Proof of Concept with working AI coaching loop.

### Project Purpose

The AI Coaching Platform provides persistent AI coaching support to small business clients through structured Pathways. The platform supplements human advisors by providing continuous support between advisor interactions.

### Build 001 Scope

Build 001 establishes the application foundation and demonstrates:

- Flask application structure
- Persistent SQL data model
- Client and Advisor roles with authentication
- Client isolation and authorization
- PATHWAY-001 (Recovery & Stabilization) configuration loading
- Basic Coaching Record persistence
- Mobile-first Client Portal
- Responsive Advisor Portal
- Coaching Context Builder
- Successful deployment capability to Render

### Build 002 Scope

Build 002 adds the AI coaching engine and demonstrates:

- **OpenAI API integration** - Clean AI service abstraction
- **Text-based coaching sessions** - Interactive coaching conversations
- **Coaching context assembly** - Focused, relevant context for AI
- **Session extraction** - Structured updates from conversations
- **Validation layer** - AI outputs validated before persistence
- **Provenance tracking** - Source tracking for coaching record entries
- **Persistent coaching loop** - Sessions update coaching record
- **Guardrail recognition** - PATHWAY-001 boundaries enforced
- **Advisor guidance integration** - Human direction influences AI
- **Duplicate handling** - Updates existing records vs creating duplicates

**Build 002 intentionally does NOT include:**
- ElevenLabs voice interaction (planned for Build 003)
- Automated check-ins or scheduled sessions
- Email notifications to advisors
- Resource URL links (placeholders only)
- Automated Pathway progression
- Session analytics or metrics

These features are planned for future builds.

## Technology Stack

- **Backend:** Python 3, Flask, SQLAlchemy, Flask-Login
- **AI:** OpenAI API (GPT-4 Turbo)
- **Database:** SQLite (local), PostgreSQL (production via DATABASE_URL)
- **Web Server:** Gunicorn (production)
- **Frontend:** HTML/CSS/JavaScript (responsive, mobile-first)

## Local Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/NSC-Rick/AI-Coaching-Platform.git
cd AI-Coaching-Platform
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file:
```bash
cp .env.example .env
```

6. Edit `.env` and set your configuration:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

**Note:** You need an OpenAI API key for Build 002 coaching sessions. Get one at https://platform.openai.com/api-keys

### Database Initialization

**Local Development:**

Initialize the database:
```bash
flask init-db
```

Seed test data:
```bash
flask seed-data
```

**Production Deployment (Render):**

Database initialization happens automatically via `init_render.py` during the build process. See `DEPLOYMENT.md` for details.

This creates test users with the following credentials:

**Advisor:**
- Email: ronda@example.com
- Password: advisor123

**Client A (Sarah):**
- Email: sarah@example.com
- Password: client123

**Client B (Michael):**
- Email: michael@example.com
- Password: client123

### Running Locally

Start the development server:
```bash
python app.py
```

Or using Flask CLI:
```bash
flask run
```

The application will be available at http://localhost:5000

## Testing

Run the test suite:
```bash
python -m pytest tests/test_foundation.py -v
```

Or using unittest:
```bash
python tests/test_foundation.py
```

## Environment Variables

### Required

- `SECRET_KEY` - Flask secret key for session management (required)

### Optional

- `DATABASE_URL` - Database connection string
  - If not set, defaults to SQLite at `data/coaching.db`
  - For PostgreSQL on Render, this is automatically set
  - Format: `postgresql://user:password@host:port/database`

## Project Structure

```
AI-Coaching-Platform/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
│
├── docs/                           # Design documentation
│   ├── 01 — AI Coaching Platform PoC Scope.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_COACHING_RECORD.md
│   ├── 04_PATHWAY_SPECIFICATION.md
│   └── 05_PATHWAY_001_RECOVERY_STABILIZATION.md
│
├── coaching/                       # Coaching engine modules
│   ├── __init__.py
│   ├── engine.py                   # Pathway loader and validation
│   └── context.py                  # Coaching context builder
│
├── pathways/                       # Pathway configurations
│   └── recovery_stabilization/
│       ├── pathway.yaml            # Pathway manifest
│       ├── methodology.md          # Methodology documentation
│       ├── coaching_guidance.md    # Coaching guidance
│       ├── guardrails.md           # Domain-specific guardrails
│       ├── milestones.json         # Pathway milestones
│       └── resources.json          # Learning resources
│
├── templates/                      # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── client_home.html
│   ├── advisor_home.html
│   └── client_detail.html
│
├── static/                         # Static assets
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── app.js
│
├── models/                         # Database models
│   ├── __init__.py
│   └── models.py
│
├── tests/                          # Test suite
│   └── test_foundation.py
│
└── data/                           # Local database (gitignored)
    └── coaching.db
```

## Deployment to Render

The application is configured for deployment to Render.

### Render Configuration

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn app:app
```

### Environment Variables on Render

Set the following environment variables in Render:

1. `SECRET_KEY` - Generate a secure random key
2. `DATABASE_URL` - Automatically set by Render when you add a PostgreSQL database

### Database Setup on Render

1. Add a PostgreSQL database to your Render service
2. Render will automatically set the `DATABASE_URL` environment variable
3. After deployment, run database initialization:
   - Use Render Shell to run: `flask init-db`
   - Then run: `flask seed-data`

## Architecture

### Separation of Concerns

The platform maintains strict separation between:

- **PLATFORM** = HOW we coach (common capabilities)
- **PATHWAY** = WHAT we coach (domain-specific content)
- **COACHING RECORD** = WHAT we know about this client

### Client Isolation

Client isolation is a non-negotiable requirement:
- Clients can only access their own engagement data
- Advisors can only access clients assigned to them
- All data access is validated server-side
- Authorization is never based solely on client-supplied IDs

### Pathway Loading

The Coaching Engine loads Pathways dynamically:
1. Identifies engagement and assigned Pathway
2. Loads Pathway manifest and configuration
3. Validates Pathway structure
4. Makes Pathway content available to the application

### Coaching Context Builder

The Context Builder assembles relevant client state for coaching:
- Client and business information
- Current Pathway state
- Open commitments
- Current risks
- Recent significant events
- Recent learning activity
- Coaching observations
- Active advisor guidance
- Recent session summary

This context would be provided to the AI coach in future builds.

## PATHWAY-001: Recovery & Stabilization

The initial Pathway is based on the 90-Day Stabilization & Revenue Activation Plan.

### Stages

1. **RS-01: Immediate Stabilization** (Days 1-30)
   - Focus: Restore operating control and improve short-term liquidity

2. **RS-02: Revenue Activation & Structural Tightening** (Days 31-60)
   - Focus: Generate revenue from proven channels while tightening structure

3. **RS-03: Governance & Accountability** (Days 61-90)
   - Focus: Establish disciplined recurring financial review

### Core Principle

**This is a stabilization pathway, not an expansion pathway.**

## Known Limitations (Build 001)

- No AI coaching integration (placeholder only)
- No voice interaction (ElevenLabs integration planned for Build 002)
- No automated Coaching Record updates from sessions
- No email notifications
- No resource URL links (placeholders only)
- Limited Pathway management (single Pathway only)
- Basic seed data only

## Next Steps (Build 002 and Beyond)

Future builds will add:
- OpenAI API integration for coaching intelligence
- ElevenLabs voice interface
- Automated session extraction and Coaching Record updates
- Resource recommendation logic
- Guardrail evaluation
- Advisor briefing generation
- Email notifications
- Additional Pathways

## Design Documentation

Complete design specifications are available in the `/docs` folder:

1. `01 — AI Coaching Platform PoC Scope.md` - Overall PoC vision and scope
2. `02_ARCHITECTURE.md` - System architecture and design principles
3. `03_COACHING_RECORD.md` - Persistent coaching record specification
4. `04_PATHWAY_SPECIFICATION.md` - Pathway structure and requirements
5. `05_PATHWAY_001_RECOVERY_STABILIZATION.md` - Recovery & Stabilization Pathway details

## License

Proprietary - Vermont Small Business Development Center (VtSBDC)

## Contact

For questions or issues, contact the development team.
