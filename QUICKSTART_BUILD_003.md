# Build 003 Quick Start Guide

## Get Voice Coaching Running in 10 Minutes

This guide gets you from zero to working voice coaching as quickly as possible.

---

## Prerequisites

- Python 3.8+
- OpenAI API key
- ElevenLabs account with API key and agent

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd AI-Coaching-Platform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Environment (3 minutes)

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` and set:

```bash
SECRET_KEY=any-random-string-for-testing
DATABASE_URL=
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_AGENT_ID=agent_your-agent-id-here
```

**Get your keys:**
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys

**Create ElevenLabs agent:**
- Go to: https://elevenlabs.io/app/agents
- Click "Create Agent"
- Choose a voice (e.g., Charlotte)
- Set to Private authentication
- Copy the Agent ID

---

## Step 3: Initialize Database (1 minute)

```bash
# Create database and tables
flask init-db

# Load test data
flask seed-data
```

**Test users created:**
- Advisor: `ronda@example.com` / `password`
- Client: `sarah@example.com` / `password`

---

## Step 4: Start Application (1 minute)

```bash
flask run
```

Application runs at: http://127.0.0.1:5000

---

## Step 5: Test Voice Coaching (3 minutes)

### Login as Client

1. Open http://127.0.0.1:5000
2. Login with:
   - Email: `sarah@example.com`
   - Password: `password`

### Start Voice Session

1. Click **"🎙️ Voice Coaching"**
2. Click **"Start Conversation"**
3. Allow microphone access
4. Wait for connection (should say "Connected - Listening...")
5. Speak naturally: *"Hi, how are you?"*
6. Listen to response
7. Continue conversation
8. Click **"End Conversation"** when done

### Verify Results

1. Return to client home
2. See updated coaching record (if commitments made)
3. Logout

### Check Advisor View

1. Login as advisor:
   - Email: `ronda@example.com`
   - Password: `password`
2. Click on Sarah's engagement
3. See voice session in history
4. See session summary
5. See any commitments/risks captured

---

## Troubleshooting

### "Voice service not available"

**Cause:** Missing ElevenLabs environment variables  
**Fix:** Check `.env` has both `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID`

### "Failed to initialize voice session"

**Cause:** Invalid ElevenLabs credentials  
**Fix:** Verify API key and Agent ID are correct

### "Microphone access denied"

**Cause:** Browser blocked microphone  
**Fix:** Allow microphone in browser settings, reload page

### "Connection error"

**Cause:** Network issue or ElevenLabs service down  
**Fix:** Check internet connection, verify ElevenLabs status

### Agent doesn't know client name

**Cause:** Context not reaching agent  
**Fix:** Check browser console for errors, verify agent is Private

### Text coaching doesn't work

**Cause:** Missing OpenAI API key  
**Fix:** Set `OPENAI_API_KEY` in `.env`

---

## What to Test

### Voice Coaching Features

1. **Natural Conversation**
   - Say: "I'm worried about cash flow"
   - Expect: Supportive, exploratory response

2. **Commitment Making**
   - Say: "I'll update my cash tracker today"
   - Expect: Acknowledgment, follow-up
   - Check: Commitment appears in client home

3. **Context Awareness**
   - Start new session
   - Say: "I updated the tracker"
   - Expect: Coach remembers previous commitment

4. **Advisor Guidance**
   - Login as advisor
   - Add guidance: "Focus on lender preparation"
   - Logout, login as client
   - Start voice session
   - Expect: Coach mentions lender preparation

### Text Coaching (Regression Test)

1. Click **"💬 Text Coaching"**
2. Send message: "Hello"
3. Receive response
4. Verify Build 002 still works

---

## Next Steps

### For Development

1. Read `BUILD_003_SUMMARY.md` for architecture details
2. Review `tests/test_build_003.py` for test examples
3. Check `coaching/voice_service.py` for implementation

### For Deployment

1. Follow `DEPLOYMENT.md` for Render deployment
2. Use `BUILD_003_DEPLOYMENT_CHECKLIST.md` for verification
3. See `ELEVENLABS_SETUP.md` for agent configuration

### For Customization

1. Modify agent prompt in `coaching/voice_service.py`
2. Adjust voice settings in ElevenLabs dashboard
3. Customize UI in `templates/voice_coaching.html`

---

## Common Questions

### Can I use a different AI model?

Yes, change `OPENAI_MODEL` in `.env` to:
- `gpt-4o` (faster, cheaper)
- `gpt-4-turbo-preview` (default)
- `gpt-3.5-turbo` (cheapest, lower quality)

### Can I use a different voice?

Yes, in ElevenLabs dashboard:
1. Go to your agent
2. Click "Voice"
3. Choose different voice
4. Save

### How much does this cost?

**OpenAI:**
- GPT-4 Turbo: ~$0.01 per text session
- GPT-4o: ~$0.005 per text session

**ElevenLabs:**
- Varies by plan and usage
- Voice sessions cost more than text
- Check ElevenLabs dashboard for current pricing

### Can I run this in production?

Yes, but:
1. Use strong `SECRET_KEY`
2. Use PostgreSQL (not SQLite)
3. Monitor costs
4. Set up proper monitoring
5. Follow security best practices

### Where's the data stored?

- **Local:** SQLite database in `data/` folder
- **Production:** PostgreSQL database (via `DATABASE_URL`)
- **Voice audio:** Not stored (only transcripts)

---

## Support

- **Build 003 Details:** See `BUILD_003_SUMMARY.md`
- **Architecture:** See `docs/02_ARCHITECTURE.md`
- **Deployment:** See `DEPLOYMENT.md`
- **ElevenLabs Setup:** See `ELEVENLABS_SETUP.md`

---

## Success!

If you can:
- ✅ Start a voice session
- ✅ Have a conversation
- ✅ See the session in advisor view
- ✅ See commitments captured

**Build 003 is working!**

Enjoy your voice-enabled AI coaching platform! 🎙️
