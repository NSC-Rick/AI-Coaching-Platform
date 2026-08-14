# Build 003 Deployment Checklist

## Pre-Deployment Verification

### Code Review
- [x] VoiceService abstraction created
- [x] Voice session routes added to app.py
- [x] Voice coaching UI template created
- [x] Client home updated with voice/text options
- [x] Build 002 extraction pipeline integration verified
- [x] Client isolation enforced in voice routes
- [x] Error handling implemented
- [x] Session cancellation handling implemented

### Dependencies
- [x] requirements.txt updated with requests==2.31.0
- [x] All imports verified
- [x] No circular dependencies

### Configuration
- [x] .env.example updated with ELEVENLABS_API_KEY
- [x] .env.example updated with ELEVENLABS_AGENT_ID
- [x] Environment variable validation in VoiceService

### Documentation
- [x] README.md updated for Build 003
- [x] BUILD_003_SUMMARY.md created
- [x] DEPLOYMENT.md updated with ElevenLabs variables
- [x] ELEVENLABS_SETUP.md created

### Testing
- [x] Build 003 test suite created (9 tests)
- [x] Test coverage includes:
  - [x] Voice session initialization
  - [x] Client isolation
  - [x] Session completion with extraction
  - [x] Session cancellation
  - [x] Text coaching preservation
  - [x] Voice service abstraction
  - [x] Context consistency
  - [x] Authorization
  - [x] Build 002 pipeline integration

---

## ElevenLabs Setup

### Account Setup
- [ ] ElevenLabs account created
- [ ] Active subscription confirmed
- [ ] API key generated
- [ ] API key stored securely (NOT in code)

### Agent Configuration
- [ ] Agent created in ElevenLabs dashboard
- [ ] Voice selected and tested
- [ ] Base system prompt configured
- [ ] Conversation settings configured:
  - [ ] Response length: Medium
  - [ ] Interruptions: Enabled
  - [ ] Silence detection: 2-3 seconds
- [ ] Authentication set to Private
- [ ] Agent ID copied

### Agent Testing
- [ ] Test conversation in ElevenLabs dashboard
- [ ] Voice quality verified
- [ ] Response style appropriate
- [ ] Natural conversation flow confirmed

---

## Local Testing

### Environment Setup
- [ ] .env file created from .env.example
- [ ] SECRET_KEY set
- [ ] DATABASE_URL set (or blank for SQLite)
- [ ] OPENAI_API_KEY set
- [ ] OPENAI_MODEL set
- [ ] ELEVENLABS_API_KEY set
- [ ] ELEVENLABS_AGENT_ID set

### Database
- [ ] Database initialized: `flask init-db`
- [ ] Seed data loaded: `flask seed-data`
- [ ] Test users created:
  - [ ] Advisor: ronda@example.com / password
  - [ ] Client: sarah@example.com / password

### Application Testing
- [ ] Application starts: `flask run`
- [ ] Login as advisor works
- [ ] Login as client works
- [ ] Client home page loads
- [ ] Voice coaching button visible
- [ ] Text coaching button visible

### Voice Session Testing
- [ ] Click "🎙️ Voice Coaching"
- [ ] Voice coaching page loads
- [ ] Microphone permission requested
- [ ] Session initialization succeeds
- [ ] ElevenLabs connection established
- [ ] Voice conversation works
- [ ] Agent has client context (name, business, stage)
- [ ] Session end works
- [ ] Extraction runs
- [ ] Coaching record updated
- [ ] Return to client home works

### Text Session Testing (Regression)
- [ ] Click "💬 Text Coaching"
- [ ] Text session starts
- [ ] Messages send/receive
- [ ] Session end works
- [ ] Extraction runs
- [ ] Build 002 functionality preserved

### Advisor Portal Testing
- [ ] Login as advisor
- [ ] View client detail
- [ ] See voice sessions in history
- [ ] See text sessions in history
- [ ] Session summaries visible
- [ ] Commitments from voice sessions visible
- [ ] Risks from voice sessions visible

---

## Render Deployment

### Repository
- [ ] All changes committed to git
- [ ] Changes pushed to GitHub
- [ ] Repository connected to Render

### PostgreSQL Database
- [ ] PostgreSQL service created in Render
- [ ] Database name: coaching_db
- [ ] Internal Database URL copied

### Web Service Configuration
- [ ] Web service created in Render
- [ ] Python version: 3.12+
- [ ] Build command: `pip install -r requirements.txt && python init_render.py`
- [ ] Start command: `gunicorn app:app`
- [ ] PostgreSQL database linked

### Environment Variables (Render)
- [ ] SECRET_KEY set (generate new for production)
- [ ] DATABASE_URL set (auto-configured or manual)
- [ ] OPENAI_API_KEY set
- [ ] OPENAI_MODEL set (gpt-4-turbo-preview or gpt-4o)
- [ ] ELEVENLABS_API_KEY set
- [ ] ELEVENLABS_AGENT_ID set

### Deployment
- [ ] Manual deploy triggered
- [ ] Build logs reviewed
- [ ] Database initialization successful:
  - [ ] Tables created
  - [ ] Seed data loaded
- [ ] Application started successfully
- [ ] No errors in logs

---

## Production Testing

### Smoke Tests
- [ ] Application URL accessible
- [ ] Login page loads
- [ ] Advisor login works
- [ ] Client login works
- [ ] No console errors

### Voice Functionality
- [ ] Client home shows voice option
- [ ] Voice coaching page loads
- [ ] Microphone permission works
- [ ] Voice session initializes
- [ ] ElevenLabs connection works
- [ ] Voice conversation works
- [ ] Session completion works
- [ ] Extraction runs
- [ ] Data persists

### Text Functionality (Regression)
- [ ] Text coaching still works
- [ ] Text sessions complete
- [ ] Text extraction works
- [ ] No regression in Build 002

### Client Isolation
- [ ] Login as sarah@example.com
- [ ] Start voice session
- [ ] Verify context is Sarah's
- [ ] Logout
- [ ] Login as different client (if available)
- [ ] Start voice session
- [ ] Verify context is different client's
- [ ] Confirm no data leakage

### Advisor Visibility
- [ ] Login as advisor
- [ ] View client detail
- [ ] Verify voice sessions visible
- [ ] Verify session summaries accurate
- [ ] Verify commitments captured
- [ ] Verify risks captured

---

## Security Verification

### Secrets Protection
- [ ] ELEVENLABS_API_KEY not in client-side code
- [ ] OPENAI_API_KEY not in client-side code
- [ ] SECRET_KEY not exposed
- [ ] DATABASE_URL not exposed
- [ ] Signed URLs used for ElevenLabs (not API key)

### Authorization
- [ ] Voice session requires authentication
- [ ] Client can only access own sessions
- [ ] Advisor can only see assigned clients
- [ ] No unauthorized access possible

### Data Privacy
- [ ] Client data isolated
- [ ] Session data scoped to engagement
- [ ] No cross-client data leakage
- [ ] Advisor guidance private to engagement

---

## Performance Verification

### Response Times
- [ ] Voice session initialization < 3 seconds
- [ ] ElevenLabs connection < 5 seconds
- [ ] Session completion < 10 seconds
- [ ] Extraction processing < 15 seconds

### Resource Usage
- [ ] No memory leaks
- [ ] Database connections managed
- [ ] No hanging sessions
- [ ] Graceful error recovery

---

## Monitoring Setup

### Application Monitoring
- [ ] Render logs accessible
- [ ] Error tracking configured (optional)
- [ ] Performance monitoring (optional)

### ElevenLabs Monitoring
- [ ] Usage dashboard accessible
- [ ] Cost tracking enabled
- [ ] Budget alerts configured (recommended)

### Database Monitoring
- [ ] PostgreSQL metrics accessible
- [ ] Connection pool healthy
- [ ] Query performance acceptable

---

## User Acceptance Testing

### Client Experience
- [ ] Voice interaction feels natural
- [ ] Coach knows client context
- [ ] Commitments tracked correctly
- [ ] Progress recognized
- [ ] Advisor guidance reflected

### Advisor Experience
- [ ] Voice sessions visible
- [ ] Session summaries useful
- [ ] Extraction quality acceptable
- [ ] Attention items flagged appropriately
- [ ] Guidance reaches voice coach

---

## Documentation Verification

### For Developers
- [ ] README.md accurate
- [ ] BUILD_003_SUMMARY.md complete
- [ ] DEPLOYMENT.md current
- [ ] ELEVENLABS_SETUP.md clear
- [ ] Code comments sufficient

### For Users
- [ ] UI clear and intuitive
- [ ] Error messages helpful
- [ ] Help text available (if needed)

---

## Rollback Plan

### If Issues Found
- [ ] Previous deployment available
- [ ] Database backup exists
- [ ] Rollback procedure documented:
  1. Revert to previous commit
  2. Redeploy in Render
  3. Verify Build 002 functionality
  4. Investigate issue offline

---

## Post-Deployment Tasks

### Immediate (Day 1)
- [ ] Monitor logs for errors
- [ ] Test all critical paths
- [ ] Verify data persistence
- [ ] Check ElevenLabs usage

### Short-term (Week 1)
- [ ] Collect client feedback
- [ ] Collect advisor feedback
- [ ] Monitor extraction quality
- [ ] Track voice session completion rate
- [ ] Review ElevenLabs costs

### Medium-term (Month 1)
- [ ] Analyze session patterns
- [ ] Identify improvement opportunities
- [ ] Refine agent prompts if needed
- [ ] Optimize extraction logic if needed
- [ ] Plan Build 004 features

---

## Success Criteria

### Technical Success
- [x] Build 003 code complete
- [ ] All tests passing in production
- [ ] No critical errors
- [ ] Voice sessions working
- [ ] Text sessions still working
- [ ] Extraction pipeline working
- [ ] Client isolation maintained

### User Success
- [ ] Clients can use voice coaching
- [ ] Voice feels natural
- [ ] Context continuity works
- [ ] Advisors see voice session outcomes
- [ ] No confusion between voice/text modes

### Business Success
- [ ] Hypothesis validated: Voice works as interface
- [ ] Platform still owns state
- [ ] Advisor still in control
- [ ] Ready for real client testing
- [ ] Foundation for Build 004

---

## Sign-Off

### Development Team
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Deployment successful

### Product Owner
- [ ] Requirements met
- [ ] User experience acceptable
- [ ] Ready for user testing

### Technical Lead
- [ ] Architecture preserved
- [ ] Security verified
- [ ] Performance acceptable
- [ ] Monitoring in place

---

## Build 003 Status

**Current Status:** ✅ COMPLETE - Ready for Deployment

**Next Steps:**
1. Complete ElevenLabs agent setup
2. Deploy to Render
3. Complete production testing checklist
4. Gather user feedback
5. Plan Build 004

**Build 003 is ready to ship!**
