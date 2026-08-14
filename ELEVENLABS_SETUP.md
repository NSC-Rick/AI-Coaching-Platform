# ElevenLabs Agent Setup Guide

## Build 003 - Voice Coaching Configuration

This guide explains how to create and configure an ElevenLabs Conversational AI agent for the AI Coaching Platform.

---

## Prerequisites

1. ElevenLabs account (https://elevenlabs.io)
2. Active subscription (required for Conversational AI)

---

## Step 1: Create Your Agent

1. Log in to ElevenLabs
2. Navigate to **Conversational AI** → **Agents**
3. Click **"Create Agent"**

---

## Step 2: Basic Configuration

### Agent Name
```
AI Recovery Coach
```

### Agent Description (Internal)
```
Persistent AI coach for small business recovery and stabilization.
Supports clients through structured recovery pathways with human advisor oversight.
```

---

## Step 3: Voice Selection

**Recommended Voice Characteristics:**
- **Tone:** Calm, professional, supportive
- **Style:** Conversational, not robotic
- **Pace:** Moderate (not too fast)

**Suggested Voices:**
- **Charlotte** - Professional, warm
- **Daniel** - Calm, reassuring
- **Rachel** - Clear, supportive

**Test the voice** to ensure it matches the coaching style.

---

## Step 4: System Prompt (Initial)

**Important:** The application will override this prompt dynamically with client-specific context. However, you should set a base prompt for testing.

```
You are an AI Recovery Coach supporting small business owners through financial recovery and stabilization.

COACHING STYLE:
- Be calm, practical, and supportive
- Ask useful questions
- Work from known facts
- Recognize progress
- Follow up on commitments
- Help turn intentions into actions
- Respect advisor guidance
- Apply pathway guardrails

IMPORTANT RULES:
- Sound natural and conversational
- Do NOT sound like a questionnaire
- Do NOT lecture unnecessarily
- Do NOT pretend to be the human advisor
- Do NOT fabricate facts or invent resources
- Do NOT reveal internal implementation details

Your role is to help clients make progress through their recovery pathway using appropriate coaching behavior.
```

**Note:** This base prompt will be dynamically replaced with client-specific context when sessions start from the application.

---

## Step 5: Conversation Settings

### Language
- **Primary Language:** English (US)

### Response Length
- **Setting:** Medium
- **Rationale:** Allows natural conversation without being too verbose

### Interruption Handling
- **Allow Interruptions:** Yes
- **Rationale:** Clients should be able to interject naturally

### Silence Detection
- **Timeout:** 2-3 seconds
- **Rationale:** Gives clients time to think without awkward pauses

---

## Step 6: Knowledge Base (Optional)

**For PoC:** Leave empty

**For Production:** Consider adding:
- Recovery methodology overview
- Common business terms glossary
- General small business resources

**Do NOT add:**
- Client-specific information (comes from application)
- Pathway details (provided dynamically)
- Advisor guidance (provided dynamically)

---

## Step 7: Authentication Settings

### Agent Visibility
- **Setting:** Private
- **Rationale:** Requires signed URL authentication from application

### Authentication Required
- **Setting:** Yes
- **Rationale:** Ensures only authenticated clients can access

---

## Step 8: Advanced Settings

### Temperature
- **Setting:** 0.7
- **Rationale:** Balanced between consistency and natural variation

### Max Tokens
- **Setting:** 150-200 per response
- **Rationale:** Conversational responses without overwhelming client

### First Message
- **Setting:** Enabled
- **Example:** "Hi! How are things going?"

**Note:** The application provides client context, so the agent will know the client's name and situation.

---

## Step 9: Testing Your Agent

### Test in ElevenLabs Dashboard

1. Click **"Test Agent"** in the agent settings
2. Try these test scenarios:

**Test 1: Initial Greeting**
```
You: Hi
Expected: Natural greeting, asks how things are going
```

**Test 2: Commitment Follow-up**
```
You: I said I would update my cash tracker but I haven't done it yet.
Expected: Supportive response, explores barriers, helps with action
```

**Test 3: Concern Expression**
```
You: I'm worried about making payroll next week.
Expected: Calm acknowledgment, asks clarifying questions, doesn't panic
```

**Test 4: Vague Statement**
```
You: Things are okay I guess.
Expected: Gentle exploration, doesn't accept vague answer without follow-up
```

### Adjust Based on Testing

- **Too robotic?** Adjust voice or prompt
- **Too chatty?** Reduce max tokens
- **Interrupts too much?** Adjust silence detection
- **Doesn't follow up?** Refine system prompt

---

## Step 10: Get Your Agent ID

1. In the agent settings, find **Agent ID**
2. Copy the ID (format: `agent_abc123...`)
3. Add to your `.env` file:
   ```
   ELEVENLABS_AGENT_ID=agent_abc123...
   ```

---

## Step 11: Get Your API Key

1. Navigate to **Settings** → **API Keys**
2. Create a new API key or copy existing
3. Add to your `.env` file:
   ```
   ELEVENLABS_API_KEY=your-api-key-here
   ```

**Security Note:** Never commit API keys to version control.

---

## Step 12: Test Integration

### Local Testing

1. Ensure `.env` has both variables set
2. Start the application: `flask run`
3. Log in as a client
4. Click **"🎙️ Voice Coaching"**
5. Test the voice conversation

### Verify Context Injection

The agent should:
- ✓ Know the client's name
- ✓ Reference the business name
- ✓ Understand current pathway stage
- ✓ Follow up on previous commitments (if any)
- ✓ Respect advisor guidance (if any)

If the agent doesn't have this context, check:
- `conversation_config_override` in voice_service.py
- Agent prompt construction
- Signed URL generation

---

## Production Deployment

### Before Going Live

1. **Test thoroughly** with multiple scenarios
2. **Verify guardrails** work (e.g., no new debt recommendation)
3. **Test escalation** behavior (e.g., payroll crisis)
4. **Confirm advisor guidance** reaches voice context
5. **Validate client isolation** (different clients get different context)

### Monitoring

After deployment, monitor:
- Voice session completion rate
- Average session duration
- Extraction success rate
- Client feedback
- Advisor feedback

### Cost Management

ElevenLabs charges per:
- Character processed
- Voice synthesis
- Conversation duration

Monitor usage in ElevenLabs dashboard and set budget alerts.

---

## Troubleshooting

### Agent doesn't know client name

**Cause:** Context not reaching agent  
**Fix:** Check `conversation_config_override` in init_voice_session route

### Agent gives generic responses

**Cause:** Base prompt used instead of dynamic prompt  
**Fix:** Verify prompt override in session config

### Agent doesn't respect guardrails

**Cause:** Guardrails not in prompt  
**Fix:** Check `_build_agent_prompt()` includes pathway guardrails

### Voice quality issues

**Cause:** Voice selection or settings  
**Fix:** Test different voices in ElevenLabs dashboard

### Session doesn't complete

**Cause:** Client-side error or network issue  
**Fix:** Check browser console, verify signed URL generation

---

## Best Practices

1. **Keep base prompt general** - Specific context comes from application
2. **Test voice selection** - Different clients may prefer different voices
3. **Monitor costs** - Voice AI can be expensive at scale
4. **Collect feedback** - Iterate based on client and advisor input
5. **Version agents** - Consider separate agents for testing vs production

---

## Support

- **ElevenLabs Documentation:** https://elevenlabs.io/docs
- **ElevenLabs Support:** support@elevenlabs.io
- **Platform Issues:** Check BUILD_003_SUMMARY.md

---

## Next Steps

After successful setup:

1. ✓ Agent created and configured
2. ✓ API key and Agent ID in environment
3. ✓ Local testing complete
4. ✓ Context injection verified
5. → Deploy to Render
6. → Add environment variables to Render
7. → Test production voice sessions
8. → Gather feedback
9. → Iterate and improve

**Your voice coaching is ready!**
