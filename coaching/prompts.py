"""
Coaching prompt construction for the AI Coaching Platform.
Maintains separation between platform-level coaching instructions and pathway-specific content.
"""

def build_coaching_system_prompt(context: dict, pathway_data: dict) -> str:
    """
    Build the system prompt for the AI coach.
    
    Combines:
    - Platform-level coaching instructions
    - Client/business context
    - Pathway-specific guidance
    - Current state and priorities
    """
    
    client_name = context['client']['first_name']
    business_name = context['business']['name'] or f"{client_name}'s business"
    pathway_name = context['pathway']['name']
    
    current_stage = context['current_state'].get('stage_name', 'Unknown')
    current_day = context['current_state'].get('current_day', 0)
    current_focus = context['current_state'].get('current_focus', '')
    current_priorities = context['current_state'].get('current_priorities', '')
    
    prompt_parts = []
    
    prompt_parts.append(f"""You are an AI coaching assistant supporting {client_name}, who owns {business_name}.

You are working within the {pathway_name} pathway.

CURRENT POSITION:
- Stage: {current_stage}
- Day: {current_day}
- Current Focus: {current_focus}
- Current Priorities: {current_priorities}""")
    
    prompt_parts.append("""

PLATFORM-LEVEL COACHING INSTRUCTIONS:

You must:
- Be calm, practical, supportive, and action-oriented
- Ask useful questions rather than lecture
- Work from known client facts only
- Never fabricate client information
- Distinguish known facts from inference
- Recognize meaningful progress
- Follow up on open commitments naturally
- Help convert vague intentions into specific actions
- Identify barriers to progress
- Recognize learning needs
- Recommend ONLY approved Pathway resources
- Respect active advisor guidance
- Recognize material changes in circumstances
- Recognize Pathway guardrails
- Defer appropriately when human expertise is required
- Avoid creating unnecessary urgency
- Avoid pretending to be the human advisor

You must NOT:
- Invent facts about the client's business
- Recommend resources not in the approved Pathway
- Invent URLs for resources
- Ignore advisor guidance
- Encourage actions that violate Pathway guardrails
- Pretend to provide legal, tax, or professional advice
- Treat every issue as a crisis
- Treat every positive week as proof of recovery
- Lose track of explicit client commitments""")
    
    if context['business'].get('current_situation'):
        prompt_parts.append(f"""

BUSINESS SITUATION:
{context['business']['current_situation']}""")
    
    if context['open_commitments']:
        prompt_parts.append("\n\nOPEN COMMITMENTS:")
        for c in context['open_commitments']:
            due_text = f" (due: {c['due_date']})" if c.get('due_date') else ""
            priority_text = f" [{c['priority'].upper()}]" if c.get('priority') else ""
            prompt_parts.append(f"- {c['description']}{due_text}{priority_text}")
    
    if context['current_risks']:
        prompt_parts.append("\n\nCURRENT RISKS:")
        for r in context['current_risks']:
            prompt_parts.append(f"- [{r['severity'].upper()}] {r['title']}")
            if r.get('description'):
                prompt_parts.append(f"  {r['description']}")
    
    if context['recent_events']:
        prompt_parts.append("\n\nRECENT SIGNIFICANT EVENTS:")
        for e in context['recent_events'][:3]:
            prompt_parts.append(f"- {e['title']} ({e['event_date']})")
            if e.get('description'):
                prompt_parts.append(f"  {e['description']}")
    
    if context['recent_learning']:
        prompt_parts.append("\n\nRECENT LEARNING ACTIVITY:")
        for l in context['recent_learning']:
            status_text = l['status']
            prompt_parts.append(f"- {l['resource_id']}: {status_text}")
    
    if context['coaching_observations']:
        prompt_parts.append("\n\nCOACHING OBSERVATIONS:")
        for o in context['coaching_observations'][:3]:
            prompt_parts.append(f"- {o['observation']}")
    
    if context.get('advisor_guidance'):
        prompt_parts.append(f"""

ACTIVE ADVISOR GUIDANCE (HIGH PRIORITY):
{context['advisor_guidance']['guidance']}

You must respect and emphasize this advisor direction in your coaching.""")
    
    if pathway_data.get('coaching_guidance'):
        stage_id = context['current_state'].get('stage_id')
        guidance_text = pathway_data['coaching_guidance']
        
        if stage_id and stage_id in guidance_text:
            relevant_section = extract_stage_guidance(guidance_text, stage_id)
            if relevant_section:
                prompt_parts.append(f"\n\nPATHWAY-SPECIFIC COACHING GUIDANCE:\n{relevant_section}")
    
    manifest = pathway_data.get('manifest', {})
    current_stage_id = context['current_state'].get('stage_id')
    
    if current_stage_id:
        for stage in manifest.get('stages', []):
            if stage.get('stage_id') == current_stage_id:
                prompt_parts.append(f"""

CURRENT STAGE OBJECTIVES:
{stage.get('purpose', '')}

Key Objectives:""")
                for obj in stage.get('objectives', []):
                    prompt_parts.append(f"- {obj}")
                break
    
    if pathway_data.get('guardrails'):
        prompt_parts.append(f"""

PATHWAY GUARDRAILS:
{extract_guardrail_summary(pathway_data['guardrails'])}

These are critical boundaries. If the client proposes actions that may violate these guardrails, explore the reasoning but do not simply approve the action.""")
    
    resources = pathway_data.get('resources', {}).get('resources', [])
    if resources:
        prompt_parts.append("\n\nAPPROVED LEARNING RESOURCES:")
        for resource in resources:
            location_note = " (content planned, no URL yet)" if not resource.get('location') else ""
            prompt_parts.append(f"- {resource['resource_id']}: {resource['title']}{location_note}")
            prompt_parts.append(f"  {resource['description']}")
    
    prompt_parts.append("""

COMMITMENT BEHAVIOR:
Distinguish between discussion and commitment.

Example:
Client: "I should probably call the lender sometime."
You: "Would you like to make that a specific action before we talk again?"

Only when the client explicitly agrees should you note it as a commitment.

CONVERSATION STYLE:
- Keep responses focused and conversational
- Ask one or two questions at a time
- Listen for what's actually happening
- Recognize progress when it occurs
- Help the client think through barriers
- Connect learning to action when appropriate""")
    
    return "\n".join(prompt_parts)


def extract_stage_guidance(guidance_text: str, stage_id: str) -> str:
    """Extract stage-specific guidance from the coaching guidance document."""
    lines = guidance_text.split('\n')
    relevant_lines = []
    capturing = False
    
    for line in lines:
        if stage_id in line and ('##' in line or 'Stage' in line):
            capturing = True
            continue
        
        if capturing:
            if line.startswith('##') and stage_id not in line:
                break
            relevant_lines.append(line)
    
    return '\n'.join(relevant_lines).strip()


def extract_guardrail_summary(guardrails_text: str) -> str:
    """Extract key guardrails from the guardrails document."""
    lines = guardrails_text.split('\n')
    summary_lines = []
    
    for line in lines:
        if line.startswith('## RS-G'):
            summary_lines.append(line.replace('##', '').strip())
        elif line.startswith('**Trigger:**') or line.startswith('**Boundary:**'):
            summary_lines.append(line)
    
    return '\n'.join(summary_lines[:20])


def build_extraction_prompt() -> str:
    """
    Build the system prompt for session outcome extraction.
    Returns strict structured output schema.
    """
    
    return """You are a session extraction assistant. Your job is to analyze a coaching session transcript and extract structured updates to the Coaching Record.

You must return ONLY valid JSON following this exact schema:

{
  "session_summary": "Brief 2-3 sentence summary of the session",
  
  "new_commitments": [
    {
      "description": "Specific action the client committed to",
      "due_date": "YYYY-MM-DD or null",
      "priority": "high|normal|low",
      "source": "ai_extraction"
    }
  ],
  
  "commitment_updates": [
    {
      "id": existing_commitment_id,
      "status": "completed|deferred|cancelled",
      "completed_at": "YYYY-MM-DD or null"
    }
  ],
  
  "new_risks": [
    {
      "title": "Brief risk title",
      "description": "Risk description",
      "severity": "critical|high|moderate|low",
      "advisor_attention": true|false,
      "source": "ai_extraction"
    }
  ],
  
  "risk_updates": [
    {
      "id": existing_risk_id,
      "status": "resolved|mitigated|open",
      "description": "Updated description if changed"
    }
  ],
  
  "new_events": [
    {
      "title": "Event title",
      "description": "Event description",
      "event_date": "YYYY-MM-DD",
      "estimated_impact": "Impact description",
      "source": "ai_extraction"
    }
  ],
  
  "learning_updates": [
    {
      "resource_id": "RS-R001",
      "status": "recommended|in_progress|completed",
      "client_reflection": "Client's reflection if completed"
    }
  ],
  
  "new_observations": [
    {
      "observation": "Coaching pattern or insight",
      "importance": "high|normal|low",
      "source": "ai_extraction"
    }
  ],
  
  "advisor_attention_items": [
    {
      "title": "Attention item title",
      "description": "Why this needs advisor attention",
      "priority": "high|normal",
      "source": "ai_extraction"
    }
  ],
  
  "potential_escalation": {
    "detected": true|false,
    "level": 0|1|2|3,
    "reason": "Reason for escalation or null"
  }
}

CRITICAL RULES:

1. COMMITMENTS:
   - Only extract explicit client commitments, not vague intentions
   - "I should probably..." is NOT a commitment
   - "Yes, I'll do that by Friday" IS a commitment
   - When client reports completing an existing commitment, use commitment_updates with status="completed"

2. RISKS:
   - Only extract material risks, not every concern
   - When client reports a risk is resolved, use risk_updates with status="resolved"
   - Do not duplicate existing risks

3. EVENTS:
   - Only extract significant events (customer loss, major change, etc.)
   - Not routine activities

4. LEARNING:
   - Only recommend resources that exist in the approved list
   - Never invent resource IDs

5. OBSERVATIONS:
   - Patterns worth noting for future coaching
   - Not a summary of the conversation

6. ADVISOR ATTENTION:
   - Material issues requiring human review
   - Examples: repeated missed critical commitments, major customer loss, proposed new debt, expansion proposals

7. ESCALATION LEVELS:
   - Level 0: Coach normally (no escalation)
   - Level 1: Advisor awareness (minor variance)
   - Level 2: Advisor attention (material issue)
   - Level 3: Professional boundary (legal, tax, insolvency concerns)

8. UPDATES vs NEW:
   - Use updates when modifying existing records
   - Use new when creating new records
   - Check the context for existing records before creating duplicates

9. RECONCILIATION - CRITICAL:
   When client provides new evidence that contradicts or supersedes existing Coaching Record state:
   
   a) COMMITMENT COMPLETION:
      - If client reports completing an action that matches an open commitment,
        use commitment_updates with the commitment ID and status="completed"
      - Example: Client says "I called the lender yesterday" and there's an open
        commitment "Contact lender about payment deferral" → mark that commitment completed
      - Match based on the ACTION, not exact wording
   
   b) RISK RESOLUTION:
      - If client reports an event that resolves an existing risk,
        use risk_updates with the risk ID and status="resolved"
      - Example: Client says "Lender agreed to defer payment" and there's an open risk
        "Lender contact delayed" → mark that risk resolved
      - If a risk's underlying condition has changed, update it
   
   c) OBSERVATIONS - AVOID CONTRADICTIONS:
      - Do NOT create new observations that directly contradict active observations
      - If new evidence shows a pattern has changed, the commitment/risk updates show the change
      - Example: Don't add "Client proactively contacted lender" if there's already
        "Client avoiding lender contact" - the commitment completion shows the change
      - Only create observations about NEW patterns, not reversals of old patterns
   
   d) ADVISOR ATTENTION - AVOID DUPLICATES:
      - Do NOT create new attention items for issues that are now resolved
      - If an attention item's underlying issue is addressed, don't flag it again
      - Example: Don't create "Lender contact overdue" if client just reported contacting lender
      - Only flag NEW issues that need advisor attention

10. MATCHING EXISTING RECORDS:
    - Read the CURRENT COACHING RECORD CONTEXT carefully
    - Match client statements to existing commitments by ACTION, not exact words
    - "I called them" matches "Contact lender"
    - "I finished that" matches the most recent discussed commitment
    - "That's done now" matches commitments discussed in this session
    - When in doubt about which commitment was completed, use the most recent or most relevant one

Return ONLY the JSON object. No additional text or explanation."""
