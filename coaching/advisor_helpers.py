"""
Helper functions for advisor views.
Formats existing coaching data for advisor presentation.
"""

from datetime import datetime, timedelta

def build_coaching_snapshot(context, pathway_state, recent_sessions):
    """
    Build a plain-language coaching snapshot from existing context.
    
    Returns a dict with:
    - situation: Current situation summary
    - current_focus: What client is working on
    - next_action: Next meaningful action
    - recent_developments: Chronological list of recent developments
    """
    snapshot = {
        'situation': '',
        'current_focus': '',
        'next_action': '',
        'recent_developments': []
    }
    
    # Build situation from pathway state and recent session
    client_name = context['client']['first_name']
    
    if pathway_state and pathway_state.current_focus:
        snapshot['current_focus'] = pathway_state.current_focus
    
    if pathway_state and pathway_state.current_priority_summary:
        snapshot['situation'] = pathway_state.current_priority_summary
    
    # Extract recent developments from sessions
    if recent_sessions:
        for session in recent_sessions[:3]:  # Last 3 sessions
            if session.summary:
                dev_date = session.started_at.strftime('%b %d')
                snapshot['recent_developments'].append({
                    'date': dev_date,
                    'summary': session.summary,
                    'session_id': session.id
                })
    
    # Get next action from open commitments
    if context.get('open_commitments'):
        # Find the most urgent/recent commitment
        for commitment in context['open_commitments']:
            if commitment.get('status') == 'open':
                snapshot['next_action'] = commitment['description']
                break
    
    return snapshot


def categorize_commitments(commitments):
    """
    Categorize commitments into active, completed, and historical.
    
    Returns dict with:
    - active: Currently active commitments
    - next_actions: Immediate next actions
    - completed_recent: Recently completed
    - historical: Older commitments
    """
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)
    
    categorized = {
        'active': [],
        'next_actions': [],
        'completed_recent': [],
        'historical': []
    }
    
    for commitment in commitments:
        if commitment.status == 'open':
            # Check if it's a next action (due soon or high priority)
            is_next_action = False
            if commitment.due_date and commitment.due_date <= today + timedelta(days=2):
                is_next_action = True
            elif commitment.priority == 'high':
                is_next_action = True
            
            if is_next_action:
                categorized['next_actions'].append(commitment)
            else:
                categorized['active'].append(commitment)
        
        elif commitment.status == 'completed':
            if commitment.updated_at and commitment.updated_at >= week_ago:
                categorized['completed_recent'].append(commitment)
            else:
                categorized['historical'].append(commitment)
        
        else:
            categorized['historical'].append(commitment)
    
    return categorized


def categorize_risks(risks):
    """
    Categorize risks into active watch items and historical.
    
    Returns dict with:
    - active: Currently active risks
    - watch: Items requiring monitoring
    - resolved: Recently resolved
    - historical: Older risks
    """
    categorized = {
        'active': [],
        'watch': [],
        'resolved': [],
        'historical': []
    }
    
    for risk in risks:
        if risk.status == 'open':
            if risk.severity in ['critical', 'high']:
                categorized['active'].append(risk)
            else:
                categorized['watch'].append(risk)
        elif risk.status == 'mitigated':
            categorized['resolved'].append(risk)
        else:
            categorized['historical'].append(risk)
    
    return categorized


def build_recent_developments_timeline(sessions, observations, events):
    """
    Build a chronological timeline of recent developments.
    
    Combines sessions, observations, and events into a unified timeline.
    Returns list of development items sorted by date (newest first).
    """
    timeline = []
    
    # Add session summaries
    for session in sessions[:5]:  # Last 5 sessions
        if session.summary:
            timeline.append({
                'date': session.started_at,
                'type': 'session',
                'content': session.summary,
                'display_date': session.started_at.strftime('%b %d')
            })
    
    # Add significant observations
    for obs in observations[:5]:
        if obs.status == 'active' and obs.importance in ['high', 'critical']:
            timeline.append({
                'date': obs.created_at,
                'type': 'observation',
                'content': obs.observation,
                'display_date': obs.created_at.strftime('%b %d')
            })
    
    # Add significant events
    for event in events[:3]:
        timeline.append({
            'date': event.event_date,
            'type': 'event',
            'content': f"{event.title}: {event.description}" if event.description else event.title,
            'display_date': event.event_date.strftime('%b %d')
        })
    
    # Sort by date, newest first
    timeline.sort(key=lambda x: x['date'], reverse=True)
    
    # Group by date for display
    grouped_timeline = []
    current_date = None
    current_group = None
    
    for item in timeline[:10]:  # Limit to 10 most recent
        if item['display_date'] != current_date:
            if current_group:
                grouped_timeline.append(current_group)
            current_date = item['display_date']
            current_group = {
                'date': current_date,
                'items': []
            }
        current_group['items'].append(item)
    
    if current_group:
        grouped_timeline.append(current_group)
    
    return grouped_timeline


def determine_advisor_attention_status(attention_items, risks, commitments):
    """
    Determine if advisor intervention is currently needed.
    
    Returns dict with:
    - needs_attention: Boolean
    - reason: Why attention is needed (if applicable)
    - watch_items: List of items to monitor
    """
    status = {
        'needs_attention': False,
        'reason': None,
        'watch_items': []
    }
    
    # Check for open attention items
    open_attention = [item for item in attention_items if item.status == 'open']
    if open_attention:
        high_priority = [item for item in open_attention if item.priority == 'high']
        if high_priority:
            status['needs_attention'] = True
            status['reason'] = f"{len(high_priority)} high-priority attention item(s)"
        else:
            status['watch_items'].extend([item.title for item in open_attention[:3]])
    
    # Check for critical/high risks
    critical_risks = [risk for risk in risks if risk.status == 'open' and risk.severity in ['critical', 'high']]
    if critical_risks:
        if not status['needs_attention']:
            status['needs_attention'] = True
            status['reason'] = f"{len(critical_risks)} high-severity risk(s)"
        status['watch_items'].extend([risk.title for risk in critical_risks[:3]])
    
    # Check for overdue commitments
    today = datetime.utcnow().date()
    overdue = [c for c in commitments if c.status == 'open' and c.due_date and c.due_date < today]
    if len(overdue) > 2:  # More than 2 overdue commitments
        if not status['needs_attention']:
            status['needs_attention'] = True
            status['reason'] = f"{len(overdue)} overdue commitments"
    
    return status
