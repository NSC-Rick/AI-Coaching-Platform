import os
import logging
import click
from datetime import datetime, timedelta, date
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Advisor, Client, Business, Engagement, PathwayState, Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation, Session, AdvisorGuidance, AdvisorAttention, SessionMessage, InformationDomain, Pathway, DomainComponent
from coaching.ai_service import AIService, AIServiceError
from coaching.context import build_coaching_context, format_context_for_display
from coaching.engine import load_pathway
from coaching.prompts import build_coaching_system_prompt, build_extraction_prompt
from coaching.validator import ExtractionValidator, ValidationError
from coaching.persistence import apply_extraction_updates, PersistenceError
from coaching.advisor_helpers import build_coaching_snapshot, categorize_commitments, categorize_risks, build_recent_developments_timeline, determine_advisor_attention_status
from coaching.storyboard import build_storyboard_context, generate_storyboard
from coaching.voice_service import get_voice_service, get_advisor_voice_service
from background_processor import trigger_session_processing

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Normalize DATABASE_URL for SQLAlchemy with psycopg 3
    # Render provides postgres:// or postgresql://, but we need postgresql+psycopg://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/coaching.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def require_role(role):
    def decorator(f):
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != role:
                flash('Access denied.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'CLIENT':
            return redirect(url_for('client_home'))
        elif current_user.role == 'ADVISOR':
            return redirect(url_for('advisor_home'))
        elif current_user.role == 'ADMIN':
            return redirect(url_for('admin_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active():
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/client/home')
@require_role('CLIENT')
def client_home():
    client = current_user.client
    engagement = Engagement.query.filter_by(client_id=client.id, status='active').first()
    
    if not engagement:
        return render_template('client_home.html', client=client, engagement=None)
    
    pathway_state = engagement.pathway_state
    business = client.business
    
    pathway_data = load_pathway(engagement.pathway_id)
    
    # Get all commitments for categorization
    all_commitments = Commitment.query.filter_by(
        engagement_id=engagement.id
    ).all()
    
    # Categorize commitments using existing helper
    categorized_commitments = categorize_commitments(all_commitments)
    
    # Get next step (highest priority open commitment)
    next_step = None
    if categorized_commitments['next_actions']:
        next_step = categorized_commitments['next_actions'][0]
    elif categorized_commitments['active']:
        next_step = categorized_commitments['active'][0]
    
    recent_learning = LearningRecord.query.filter_by(
        engagement_id=engagement.id,
        status='recommended'
    ).order_by(LearningRecord.recommended_at.desc()).limit(3).all()
    
    learning_resources = []
    if recent_learning:
        resources_data = pathway_data.get('resources', {}).get('resources', [])
        for lr in recent_learning:
            resource = next((r for r in resources_data if r['resource_id'] == lr.resource_id), None)
            if resource:
                learning_resources.append({
                    'record': lr,
                    'resource': resource
                })
    
    return render_template('client_home.html',
                         client=client,
                         business=business,
                         engagement=engagement,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         categorized_commitments=categorized_commitments,
                         next_step=next_step,
                         learning_resources=learning_resources)

@app.route('/voice/coaching/<int:engagement_id>')
@require_role('CLIENT')
def voice_coaching(engagement_id):
    """
    Voice coaching page - Build 003.
    Renders the voice interface for ElevenLabs integration.
    """
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('client_home'))
    
    pathway_data = load_pathway(engagement.pathway_id)
    pathway_state = engagement.pathway_state
    
    return render_template('voice_coaching.html',
                         engagement=engagement,
                         pathway_data=pathway_data,
                         pathway_state=pathway_state)

@app.route('/advisor/home')
@require_role('ADVISOR')
def advisor_home():
    advisor = current_user.advisor
    
    engagements = Engagement.query.filter_by(
        advisor_id=advisor.id,
        status='active'
    ).all()
    
    client_data = []
    for engagement in engagements:
        client = engagement.client
        business = client.business
        pathway_state = engagement.pathway_state
        
        pathway_data = load_pathway(engagement.pathway_id)
        
        open_commitments_count = Commitment.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).count()
        
        highest_risk = Risk.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).order_by(
            db.case(
                (Risk.severity == 'critical', 1),
                (Risk.severity == 'high', 2),
                (Risk.severity == 'moderate', 3),
                (Risk.severity == 'low', 4),
                else_=5
            )
        ).first()
        
        attention_items = AdvisorAttention.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).count()
        
        client_data.append({
            'engagement': engagement,
            'client': client,
            'business': business,
            'pathway_state': pathway_state,
            'pathway_name': pathway_data['manifest']['name'],
            'open_commitments_count': open_commitments_count,
            'highest_risk': highest_risk,
            'attention_items': attention_items
        })
    
    return render_template('advisor_home.html',
                         advisor=advisor,
                         client_data=client_data)


@app.route('/admin/home')
@require_role('ADMIN')
def admin_home():
    total_users = User.query.count()
    active_clients = Client.query.join(User).filter(User.active.is_(True)).count()
    active_advisors = Advisor.query.join(User).filter(User.active.is_(True)).count()
    active_engagements = Engagement.query.filter_by(status='active').count()
    
    return render_template('admin_home.html',
                         total_users=total_users,
                         active_clients=active_clients,
                         active_advisors=active_advisors,
                         active_engagements=active_engagements)


@app.route('/admin/users')
@require_role('ADMIN')
def admin_users():
    users = User.query.all()
    user_data = []
    for u in users:
        name = u.email
        profile_type = 'Administrator'
        if u.client:
            name = f'{u.client.first_name} {u.client.last_name}'
            profile_type = 'Client'
        elif u.advisor:
            name = f'{u.advisor.first_name} {u.advisor.last_name}'
            profile_type = 'Advisor'
        user_data.append({
            'user': u,
            'name': name,
            'profile_type': profile_type
        })
    return render_template('admin_users.html', user_data=user_data)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_user_new():
    if request.method == 'POST':
        role = request.form.get('role', '').upper()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if role not in ('CLIENT', 'ADVISOR'):
            flash('Role must be Client or Advisor.', 'error')
            return render_template('admin_user_new.html')

        if not first_name or not last_name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('admin_user_new.html')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('A user with that email already exists.', 'error')
            return render_template('admin_user_new.html')

        if len(password) < 8:
            flash('Temporary password must be at least 8 characters.', 'error')
            return render_template('admin_user_new.html')

        try:
            user = User(email=email, role=role, active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            if role == 'CLIENT':
                profile = Client(user_id=user.id, first_name=first_name, last_name=last_name)
            else:
                profile = Advisor(user_id=user.id, first_name=first_name, last_name=last_name)

            db.session.add(profile)
            db.session.commit()
            flash(f'{role.title()} user created successfully.', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create user. Please try again.', 'error')
            logging.error(f'Error creating user: {str(e)}')

    return render_template('admin_user_new.html')


@app.route('/admin/users/<int:user_id>')
@require_role('ADMIN')
def admin_user_detail(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    detail = {
        'name': user.email,
        'profile_type': 'Administrator',
        'extra': {}
    }

    if user.client:
        client = user.client
        detail['name'] = f'{client.first_name} {client.last_name}'
        detail['profile_type'] = 'Client'
        business = client.business
        engagement = Engagement.query.filter_by(client_id=client.id, status='active').first()
        detail['extra'] = {
            'business': business,
            'engagement': engagement
        }
    elif user.advisor:
        advisor = user.advisor
        detail['name'] = f'{advisor.first_name} {advisor.last_name}'
        detail['profile_type'] = 'Advisor'
        engagements = Engagement.query.filter_by(advisor_id=advisor.id).all()
        active_engagements = [e for e in engagements if e.status == 'active']
        detail['extra'] = {
            'engagement_count': len(engagements),
            'active_count': len(active_engagements)
        }

    return render_template('admin_user_detail.html', user=user, detail=detail)


@app.route('/admin/users/<int:user_id>/activate', methods=['POST'])
@require_role('ADMIN')
def admin_user_activate(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    if user.role == 'ADMIN' or user.id == current_user.id:
        flash('Action not allowed.', 'error')
        return redirect(url_for('admin_users'))

    user.active = True
    db.session.commit()
    flash('User activated.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@require_role('ADMIN')
def admin_user_deactivate(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    if user.role == 'ADMIN' or user.id == current_user.id:
        flash('Action not allowed.', 'error')
        return redirect(url_for('admin_users'))

    user.active = False
    db.session.commit()
    flash('User deactivated.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/password', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_user_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not password or not confirm:
            flash('Both fields are required.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Temporary password updated.', 'success')
            return redirect(url_for('admin_users'))

    return render_template('admin_user_password.html', user=user)


@app.route('/admin/assignments')
@require_role('ADMIN')
def admin_assignments():
    clients = Client.query.all()
    assignments = []
    unassigned = []
    
    for client in clients:
        engagement = Engagement.query.filter_by(client_id=client.id, status='active').first()
        if engagement:
            advisor = engagement.advisor
            try:
                pathway_data = load_pathway(engagement.pathway_id)
                pathway_name = pathway_data['manifest']['name']
            except Exception:
                pathway_name = engagement.pathway_id
            
            pathway_state = engagement.pathway_state
            stage = pathway_state.current_stage_id if pathway_state else '—'
            day = pathway_state.current_day if pathway_state else '—'
            
            advisor_name = f'{advisor.first_name} {advisor.last_name}' if advisor else '—'
            client_active = client.user.active
            advisor_active = advisor.user.active if advisor and advisor.user else True
            
            assignments.append({
                'client': client,
                'client_name': f'{client.first_name} {client.last_name}',
                'advisor_name': advisor_name,
                'advisor_active': advisor_active,
                'pathway_name': pathway_name,
                'stage': stage,
                'day': day,
                'engagement': engagement,
                'client_active': client_active
            })
        else:
            unassigned.append({
                'client': client,
                'client_name': f'{client.first_name} {client.last_name}',
                'client_active': client.user.active
            })
    
    return render_template('admin_assignments.html', assignments=assignments, unassigned=unassigned)


@app.route('/admin/assignments/<int:engagement_id>')
@require_role('ADMIN')
def admin_assignment_detail(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    if not engagement:
        flash('Engagement not found.', 'error')
        return redirect(url_for('admin_assignments'))
    
    client = engagement.client
    advisor = engagement.advisor
    business = client.business if client else None
    pathway_state = engagement.pathway_state
    
    try:
        pathway_data = load_pathway(engagement.pathway_id)
        pathway_name = pathway_data['manifest']['name']
    except Exception:
        pathway_name = engagement.pathway_id
    
    open_commitments = Commitment.query.filter_by(
        engagement_id=engagement.id,
        status='open'
    ).count()
    
    current_risks = Risk.query.filter_by(
        engagement_id=engagement.id,
        status='open'
    ).count()
    
    last_session = Session.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Session.started_at.desc()).first()
    
    return render_template('admin_assignment_detail.html',
                         engagement=engagement,
                         client=client,
                         advisor=advisor,
                         business=business,
                         pathway_state=pathway_state,
                         pathway_name=pathway_name,
                         open_commitments=open_commitments,
                         current_risks=current_risks,
                         last_session=last_session)


@app.route('/admin/assignments/new/<int:client_id>', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_assignment_new(client_id):
    client = db.session.get(Client, client_id)
    if not client or client.user.role != 'CLIENT':
        flash('Client not found.', 'error')
        return redirect(url_for('admin_assignments'))
    
    existing = Engagement.query.filter_by(client_id=client.id, status='active').first()
    if existing:
        flash('Client already has an active engagement.', 'error')
        return redirect(url_for('admin_assignments'))
    
    advisors = db.session.query(Advisor).join(User).filter(
        User.role == 'ADVISOR',
        User.active.is_(True)
    ).all()
    
    available_pathways = db.session.query(Pathway).join(InformationDomain).filter(
        Pathway.status == 'active',
        InformationDomain.status == 'active'
    ).order_by(Pathway.name).all()
    
    if request.method == 'POST':
        advisor_id = request.form.get('advisor_id', type=int)
        pathway_id = request.form.get('pathway_id', '').strip()
        
        advisor = db.session.get(Advisor, advisor_id)
        if not advisor or not advisor.user or advisor.user.role != 'ADVISOR' or not advisor.user.active:
            flash('You must select an active advisor.', 'error')
            return render_template('admin_assignment_new.html',
                                 client=client,
                                 advisors=advisors,
                                 available_pathways=available_pathways)
        
        pathway_record = db.session.query(Pathway).join(InformationDomain).filter(
            Pathway.pathway_id == pathway_id,
            Pathway.status == 'active',
            InformationDomain.status == 'active'
        ).first()
        
        if not pathway_record:
            flash('Invalid pathway selected.', 'error')
            return render_template('admin_assignment_new.html',
                                 client=client,
                                 advisors=advisors,
                                 available_pathways=available_pathways)
        
        try:
            pathway_data = load_pathway(pathway_record.pathway_id)
            first_stage = pathway_data['manifest']['stages'][0]['stage_id']
            default_duration = pathway_data['manifest'].get('default_duration_days', 90)
            pathway_version = pathway_data['manifest'].get('version', '0.1')
        except Exception as e:
            flash('Selected pathway could not be loaded by the coaching engine.', 'error')
            logging.error(f'Pathway load failed for {pathway_id}: {str(e)}')
            return render_template('admin_assignment_new.html',
                                 client=client,
                                 advisors=advisors,
                                 available_pathways=available_pathways)
        
        try:
            engagement = Engagement(
                client_id=client.id,
                advisor_id=advisor.id,
                pathway_id=pathway_record.pathway_id,
                pathway_version=pathway_version,
                status='active',
                start_date=date.today(),
                target_end_date=date.today() + timedelta(days=default_duration)
            )
            db.session.add(engagement)
            db.session.flush()
            
            pathway_state = PathwayState(
                engagement_id=engagement.id,
                current_stage_id=first_stage,
                current_day=1
            )
            db.session.add(pathway_state)
            db.session.commit()
            
            flash('Engagement created successfully.', 'success')
            return redirect(url_for('admin_assignments'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create engagement.', 'error')
            logging.error(f'Error creating engagement: {str(e)}')
    
    return render_template('admin_assignment_new.html',
                         client=client,
                         advisors=advisors,
                         available_pathways=available_pathways)


@app.route('/admin/assignments/<int:engagement_id>/advisor', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_assignment_advisor(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    if not engagement:
        flash('Engagement not found.', 'error')
        return redirect(url_for('admin_assignments'))
    
    advisors = db.session.query(Advisor).join(User).filter(
        User.role == 'ADVISOR',
        User.active.is_(True)
    ).all()
    
    if request.method == 'POST':
        advisor_id = request.form.get('advisor_id', type=int)
        advisor = db.session.get(Advisor, advisor_id)
        
        if not advisor or not advisor.user or advisor.user.role != 'ADVISOR' or not advisor.user.active:
            flash('You must select an active advisor.', 'error')
            return render_template('admin_assignment_advisor.html',
                                 engagement=engagement,
                                 advisors=advisors)
        
        try:
            engagement.advisor_id = advisor.id
            db.session.commit()
            flash('Advisor updated successfully.', 'success')
            return redirect(url_for('admin_assignments'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update advisor.', 'error')
            logging.error(f'Error updating advisor: {str(e)}')
    
    return render_template('admin_assignment_advisor.html',
                         engagement=engagement,
                         advisors=advisors)


@app.route('/admin/domains')
@require_role('ADMIN')
def admin_domains():
    domains = InformationDomain.query.order_by(InformationDomain.name).all()
    return render_template('admin_domains.html', domains=domains)


@app.route('/admin/domains/new', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_domain_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'draft')
        
        if not name:
            flash('Domain name is required.', 'error')
            return render_template('admin_domain_form.html', domain=None)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_domain_form.html', domain=None)
        
        existing = InformationDomain.query.filter_by(name=name).first()
        if existing:
            flash('A domain with that name already exists.', 'error')
            return render_template('admin_domain_form.html', domain=None)
        
        try:
            domain = InformationDomain(
                name=name,
                description=description,
                status=status
            )
            db.session.add(domain)
            db.session.commit()
            flash('Information Domain created.', 'success')
            return redirect(url_for('admin_domains'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create domain.', 'error')
            logging.error(f'Error creating domain: {str(e)}')
    
    return render_template('admin_domain_form.html', domain=None)


@app.route('/admin/domains/<int:domain_id>/edit', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_domain_edit(domain_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('admin_domains'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'draft')
        
        if not name:
            flash('Domain name is required.', 'error')
            return render_template('admin_domain_form.html', domain=domain)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_domain_form.html', domain=domain)
        
        existing = InformationDomain.query.filter(
            InformationDomain.name == name,
            InformationDomain.id != domain.id
        ).first()
        if existing:
            flash('A domain with that name already exists.', 'error')
            return render_template('admin_domain_form.html', domain=domain)
        
        try:
            domain.name = name
            domain.description = description
            domain.status = status
            db.session.commit()
            flash('Information Domain updated.', 'success')
            return redirect(url_for('admin_domains'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update domain.', 'error')
            logging.error(f'Error updating domain: {str(e)}')
    
    return render_template('admin_domain_form.html', domain=domain)


@app.route('/admin/domains/<int:domain_id>')
@require_role('ADMIN')
def admin_domain_detail(domain_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('admin_domains'))
    
    component_counts = {}
    for component_type in DomainComponent.COMPONENT_TYPES:
        count = DomainComponent.query.filter_by(
            domain_id=domain.id,
            component_type=component_type
        ).count()
        component_counts[component_type] = count
    
    pathways_runtime = []
    for p in domain.pathways:
        runtime_ready = True
        try:
            load_pathway(p.pathway_id)
        except Exception:
            runtime_ready = False
        pathways_runtime.append({'pathway': p, 'runtime_ready': runtime_ready})
    
    return render_template('admin_domain_detail.html',
                         domain=domain,
                         pathways=pathways_runtime,
                         component_counts=component_counts,
                         component_labels=DomainComponent.TYPE_LABELS)


@app.route('/admin/domains/<int:domain_id>/components')
@require_role('ADMIN')
def admin_domain_components(domain_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('admin_domains'))
    
    type_filter = request.args.get('type', '').strip()
    query = DomainComponent.query.filter_by(domain_id=domain.id)
    if type_filter in DomainComponent.COMPONENT_TYPES:
        query = query.filter_by(component_type=type_filter)
    components = query.order_by(DomainComponent.name).all()
    
    return render_template('admin_domain_components.html',
                         domain=domain,
                         components=components,
                         type_filter=type_filter,
                         component_labels=DomainComponent.TYPE_LABELS)


@app.route('/admin/domains/<int:domain_id>/components/new', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_domain_component_new(domain_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('admin_domains'))
    
    if request.method == 'POST':
        component_type = request.form.get('component_type', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'draft')
        
        if component_type not in DomainComponent.COMPONENT_TYPES:
            flash('Invalid component type.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=None,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        if not name:
            flash('Component name is required.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=None,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=None,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        try:
            component = DomainComponent(
                domain_id=domain.id,
                component_type=component_type,
                name=name,
                description=description,
                status=status
            )
            db.session.add(component)
            db.session.commit()
            flash('Component created.', 'success')
            return redirect(url_for('admin_domain_detail', domain_id=domain.id))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create component.', 'error')
            logging.error(f'Error creating domain component: {str(e)}')
    
    return render_template('admin_domain_component_form.html',
                         domain=domain, component=None,
                         component_labels=DomainComponent.TYPE_LABELS)


@app.route('/admin/domains/<int:domain_id>/components/<int:component_id>/edit', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_domain_component_edit(domain_id, component_id):
    domain = db.session.get(InformationDomain, domain_id)
    if not domain:
        flash('Domain not found.', 'error')
        return redirect(url_for('admin_domains'))
    
    component = db.session.get(DomainComponent, component_id)
    if not component or component.domain_id != domain.id:
        flash('Component not found.', 'error')
        return redirect(url_for('admin_domain_detail', domain_id=domain.id))
    
    if request.method == 'POST':
        component_type = request.form.get('component_type', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'draft')
        
        if component_type not in DomainComponent.COMPONENT_TYPES:
            flash('Invalid component type.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=component,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        if not name:
            flash('Component name is required.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=component,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_domain_component_form.html',
                                 domain=domain, component=component,
                                 component_labels=DomainComponent.TYPE_LABELS)
        
        try:
            component.component_type = component_type
            component.name = name
            component.description = description
            component.status = status
            db.session.commit()
            flash('Component updated.', 'success')
            return redirect(url_for('admin_domain_detail', domain_id=domain.id))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update component.', 'error')
            logging.error(f'Error updating domain component: {str(e)}')
    
    return render_template('admin_domain_component_form.html',
                         domain=domain, component=component,
                         component_labels=DomainComponent.TYPE_LABELS)


@app.route('/admin/pathways')
@require_role('ADMIN')
def admin_pathways():
    pathways = Pathway.query.order_by(Pathway.pathway_id).all()
    return render_template('admin_pathways.html', pathways=pathways)


@app.route('/admin/pathways/new', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_pathway_new():
    active_domains = InformationDomain.query.filter_by(status='active').order_by(InformationDomain.name).all()
    
    if request.method == 'POST':
        pathway_id = request.form.get('pathway_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        domain_id = request.form.get('domain_id', type=int)
        package_slug = request.form.get('package_slug', '').strip()
        status = request.form.get('status', 'draft')
        
        if not pathway_id or not name or not domain_id:
            flash('Pathway ID, Name, and Information Domain are required.', 'error')
            return render_template('admin_pathway_form.html', pathway=None, domains=active_domains)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_pathway_form.html', pathway=None, domains=active_domains)
        
        domain = db.session.get(InformationDomain, domain_id)
        if not domain or domain.status != 'active':
            flash('You must select an active Information Domain.', 'error')
            return render_template('admin_pathway_form.html', pathway=None, domains=active_domains)
        
        existing = Pathway.query.filter_by(pathway_id=pathway_id).first()
        if existing:
            flash('A Pathway with that ID already exists.', 'error')
            return render_template('admin_pathway_form.html', pathway=None, domains=active_domains)
        
        try:
            pathway = Pathway(
                pathway_id=pathway_id,
                name=name,
                description=description,
                domain_id=domain_id,
                package_slug=package_slug,
                status=status
            )
            db.session.add(pathway)
            db.session.commit()
            flash('Pathway created.', 'success')
            return redirect(url_for('admin_pathways'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to create Pathway.', 'error')
            logging.error(f'Error creating pathway: {str(e)}')
    
    return render_template('admin_pathway_form.html', pathway=None, domains=active_domains)


@app.route('/admin/pathways/<int:pathway_db_id>/edit', methods=['GET', 'POST'])
@require_role('ADMIN')
def admin_pathway_edit(pathway_db_id):
    pathway = db.session.get(Pathway, pathway_db_id)
    if not pathway:
        flash('Pathway not found.', 'error')
        return redirect(url_for('admin_pathways'))
    
    active_domains = InformationDomain.query.filter_by(status='active').order_by(InformationDomain.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        domain_id = request.form.get('domain_id', type=int)
        package_slug = request.form.get('package_slug', '').strip()
        status = request.form.get('status', 'draft')
        
        if not name or not domain_id:
            flash('Name and Information Domain are required.', 'error')
            return render_template('admin_pathway_form.html', pathway=pathway, domains=active_domains)
        
        if status not in ('draft', 'active', 'inactive'):
            flash('Invalid status.', 'error')
            return render_template('admin_pathway_form.html', pathway=pathway, domains=active_domains)
        
        domain = db.session.get(InformationDomain, domain_id)
        if not domain or domain.status != 'active':
            flash('You must select an active Information Domain.', 'error')
            return render_template('admin_pathway_form.html', pathway=pathway, domains=active_domains)
        
        try:
            pathway.name = name
            pathway.description = description
            pathway.domain_id = domain_id
            pathway.package_slug = package_slug
            pathway.status = status
            db.session.commit()
            flash('Pathway updated.', 'success')
            return redirect(url_for('admin_pathways'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update Pathway.', 'error')
            logging.error(f'Error updating pathway: {str(e)}')
    
    return render_template('admin_pathway_form.html', pathway=pathway, domains=active_domains)


@app.route('/advisor/client/<int:engagement_id>')
@require_role('ADVISOR')
def client_detail(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.advisor_id != current_user.advisor.id:
        flash('Client not found or access denied.', 'error')
        return redirect(url_for('advisor_home'))
    
    client = engagement.client
    business = client.business
    pathway_state = engagement.pathway_state
    
    pathway_data = load_pathway(engagement.pathway_id)
    
    commitments = Commitment.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Commitment.created_at.desc()).all()
    
    risks = Risk.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Risk.created_at.desc()).all()
    
    significant_events = SignificantEvent.query.filter_by(
        engagement_id=engagement.id
    ).order_by(SignificantEvent.event_date.desc()).all()
    
    learning_records = LearningRecord.query.filter_by(
        engagement_id=engagement.id
    ).order_by(LearningRecord.recommended_at.desc()).all()
    
    # Get active observations first, then historical
    active_observations = CoachingObservation.query.filter_by(
        engagement_id=engagement.id,
        status='active'
    ).order_by(CoachingObservation.created_at.desc()).all()
    
    historical_observations = CoachingObservation.query.filter(
        CoachingObservation.engagement_id == engagement.id,
        CoachingObservation.status.in_(['resolved', 'superseded'])
    ).order_by(CoachingObservation.created_at.desc()).limit(5).all()
    
    coaching_observations = active_observations + historical_observations
    
    advisor_guidance = AdvisorGuidance.query.filter_by(
        engagement_id=engagement.id
    ).order_by(AdvisorGuidance.created_at.desc()).all()
    
    # Get open attention items first, then resolved
    open_attention_items = AdvisorAttention.query.filter_by(
        engagement_id=engagement.id,
        status='open'
    ).order_by(AdvisorAttention.created_at.desc()).all()
    
    resolved_attention_items = AdvisorAttention.query.filter_by(
        engagement_id=engagement.id,
        status='resolved'
    ).order_by(AdvisorAttention.created_at.desc()).limit(5).all()
    
    attention_items = open_attention_items + resolved_attention_items
    
    sessions = Session.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Session.started_at.desc()).limit(5).all()
    
    context = build_coaching_context(engagement_id)
    context_display = format_context_for_display(context)
    
    # Build structured data for advisor presentation
    coaching_snapshot = build_coaching_snapshot(context, pathway_state, sessions)
    categorized_commitments = categorize_commitments(commitments)
    categorized_risks = categorize_risks(risks)
    recent_developments = build_recent_developments_timeline(sessions, coaching_observations, significant_events)
    advisor_attention_status = determine_advisor_attention_status(attention_items, risks, commitments)
    
    # Get most recent session for last client activity
    last_session = sessions[0] if sessions else None
    
    # Get most recent advisor guidance for last advisor activity
    last_advisor_guidance = advisor_guidance[0] if advisor_guidance else None
    
    return render_template('client_detail.html',
                         engagement=engagement,
                         client=client,
                         business=business,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         commitments=commitments,
                         risks=risks,
                         significant_events=significant_events,
                         learning_records=learning_records,
                         coaching_observations=coaching_observations,
                         advisor_guidance=advisor_guidance,
                         attention_items=attention_items,
                         sessions=sessions,
                         context_display=context_display,
                         coaching_snapshot=coaching_snapshot,
                         categorized_commitments=categorized_commitments,
                         categorized_risks=categorized_risks,
                         recent_developments=recent_developments,
                         advisor_attention_status=advisor_attention_status,
                         last_session=last_session,
                         last_advisor_guidance=last_advisor_guidance)

@app.route('/advisor/client/<int:engagement_id>/storyboard')
@require_role('ADVISOR')
def client_storyboard(engagement_id):
    """
    Generate and display a Client Storyboard for the advisor.
    
    This is a read-only, on-demand summary of the client's coaching journey.
    It does not modify coaching state, Pathway state, or any client data.
    """
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.advisor_id != current_user.advisor.id:
        flash('Client not found or access denied.', 'error')
        return redirect(url_for('advisor_home'))
    
    client = engagement.client
    business = client.business
    pathway_data = load_pathway(engagement.pathway_id)
    
    try:
        context = build_storyboard_context(engagement_id)
        storyboard = generate_storyboard(context)
    except AIServiceError as e:
        logging.error(f"Storyboard AI generation failed for engagement {engagement_id}: {str(e)}")
        flash('Unable to generate Storyboard at this time. Please try again later.', 'error')
        return redirect(url_for('client_detail', engagement_id=engagement_id))
    except Exception as e:
        logging.error(f"Storyboard generation failed for engagement {engagement_id}: {str(e)}")
        flash('Unable to generate Storyboard at this time. Please try again later.', 'error')
        return redirect(url_for('client_detail', engagement_id=engagement_id))
    
    return render_template('client_storyboard.html',
                         engagement=engagement,
                         client=client,
                         business=business,
                         pathway_data=pathway_data,
                         storyboard=storyboard)

@app.route('/advisor/client/<int:engagement_id>/add_guidance', methods=['POST'])
@require_role('ADVISOR')
def add_guidance(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.advisor_id != current_user.advisor.id:
        flash('Client not found or access denied.', 'error')
        return redirect(url_for('advisor_home'))
    
    guidance_text = request.form.get('guidance')
    priority = request.form.get('priority', 'normal')
    
    if guidance_text:
        guidance = AdvisorGuidance(
            engagement_id=engagement_id,
            advisor_id=current_user.advisor.id,
            guidance=guidance_text,
            priority=priority,
            status='active'
        )
        db.session.add(guidance)
        db.session.commit()
        flash('Guidance added successfully.', 'success')
    
    return redirect(url_for('client_detail', engagement_id=engagement_id))

@app.route('/session/start/<int:engagement_id>', methods=['POST'])
@require_role('CLIENT')
def start_session(engagement_id):
    import time
    start_time = time.time()
    
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('client_home'))
    
    try:
        ai_service = AIService()
    except AIServiceError as e:
        flash(f'AI service not available: {str(e)}', 'error')
        return redirect(url_for('client_home'))
    
    session = Session(
        engagement_id=engagement_id,
        started_at=datetime.utcnow(),
        interaction_type='text',
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    
    context = build_coaching_context(engagement_id)
    pathway_data = load_pathway(engagement.pathway_id)
    system_prompt = build_coaching_system_prompt(context, pathway_data)
    
    try:
        ai_start = time.time()
        initial_message = ai_service.generate_coaching_response(
            messages=[],
            system_prompt=system_prompt
        )
        ai_elapsed = time.time() - ai_start
        logging.info(f"[PERFORMANCE] Coaching initial response: {ai_elapsed:.1f}s")
        
        # DIAGNOSTIC CHECKPOINT 3A: Before Persistence
        print(f"[DIAGNOSTIC] Initial Message Type: {type(initial_message)}")
        print(f"[DIAGNOSTIC] Initial Message Length: {len(initial_message) if initial_message else 0}")
        print(f"[DIAGNOSTIC] Initial Message Preview: {repr(initial_message[:100] if initial_message else initial_message)}")
        
        assistant_msg = SessionMessage(
            session_id=session.id,
            role='assistant',
            content=initial_message
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        # DIAGNOSTIC CHECKPOINT 3B: After Persistence
        persisted_msg = db.session.get(SessionMessage, assistant_msg.id)
        print(f"[DIAGNOSTIC] Persisted Message ID: {persisted_msg.id}")
        print(f"[DIAGNOSTIC] Persisted Role: {persisted_msg.role}")
        print(f"[DIAGNOSTIC] Persisted Content Type: {type(persisted_msg.content)}")
        print(f"[DIAGNOSTIC] Persisted Content Length: {len(persisted_msg.content) if persisted_msg.content else 0}")
        print(f"[DIAGNOSTIC] Persisted Content Preview: {repr(persisted_msg.content[:100] if persisted_msg.content else persisted_msg.content)}")
        
    except AIServiceError as e:
        logging.error(f"Failed to generate initial message: {str(e)}")
        flash('Failed to start coaching session. Please try again.', 'error')
        db.session.delete(session)
        db.session.commit()
        return redirect(url_for('client_home'))
    
    return redirect(url_for('coaching_session', session_id=session.id))

@app.route('/session/<int:session_id>')
@require_role('CLIENT')
def coaching_session(session_id):
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        flash('This session has ended.', 'info')
        return redirect(url_for('client_home'))
    
    engagement = session.engagement
    pathway_state = engagement.pathway_state
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = SessionMessage.query.filter_by(session_id=session_id).order_by(SessionMessage.created_at).all()
    
    return render_template('coaching_session.html',
                         session=session,
                         engagement=engagement,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         messages=messages)

@app.route('/session/<int:session_id>/message', methods=['POST'])
@require_role('CLIENT')
def send_message(session_id):
    import time
    start_time = time.time()
    
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        flash('This session has ended.', 'info')
        return redirect(url_for('client_home'))
    
    message_content = request.form.get('message', '').strip()
    
    if not message_content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('coaching_session', session_id=session_id))
    
    user_msg = SessionMessage(
        session_id=session_id,
        role='user',
        content=message_content
    )
    db.session.add(user_msg)
    db.session.commit()
    
    try:
        ai_service = AIService()
        
        engagement = session.engagement
        context = build_coaching_context(engagement.id)
        pathway_data = load_pathway(engagement.pathway_id)
        system_prompt = build_coaching_system_prompt(context, pathway_data)
        
        conversation_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]
        
        ai_start = time.time()
        response = ai_service.generate_coaching_response(
            messages=conversation_messages,
            system_prompt=system_prompt
        )
        ai_elapsed = time.time() - ai_start
        logging.info(f"[PERFORMANCE] Coaching response session={session_id}: {ai_elapsed:.1f}s")
        
        # DIAGNOSTIC CHECKPOINT 3A: Before Persistence
        print(f"[DIAGNOSTIC] Response Type: {type(response)}")
        print(f"[DIAGNOSTIC] Response Length: {len(response) if response else 0}")
        print(f"[DIAGNOSTIC] Response Preview: {repr(response[:100] if response else response)}")
        
        assistant_msg = SessionMessage(
            session_id=session_id,
            role='assistant',
            content=response
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        # DIAGNOSTIC CHECKPOINT 3B: After Persistence
        persisted_msg = db.session.get(SessionMessage, assistant_msg.id)
        print(f"[DIAGNOSTIC] Persisted Message ID: {persisted_msg.id}")
        print(f"[DIAGNOSTIC] Persisted Role: {persisted_msg.role}")
        print(f"[DIAGNOSTIC] Persisted Content Type: {type(persisted_msg.content)}")
        print(f"[DIAGNOSTIC] Persisted Content Length: {len(persisted_msg.content) if persisted_msg.content else 0}")
        print(f"[DIAGNOSTIC] Persisted Content Preview: {repr(persisted_msg.content[:100] if persisted_msg.content else persisted_msg.content)}")
        
    except AIServiceError as e:
        logging.error(f"Failed to generate response: {str(e)}")
        flash('Failed to get coach response. Please try again.', 'error')
    
    return redirect(url_for('coaching_session', session_id=session_id))

@app.route('/session/<int:session_id>/end', methods=['POST'])
@require_role('CLIENT')
def end_session(session_id):
    import time
    start_time = time.time()
    
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        return redirect(url_for('client_home'))
    
    # Mark session as completed and queue for background processing
    session.ended_at = datetime.utcnow()
    session.status = 'completed'
    session.processing_status = 'pending'
    db.session.commit()
    
    elapsed = time.time() - start_time
    logging.info(f"[PERFORMANCE] Session close session={session_id}: {elapsed:.2f}s")
    logging.info(f"[PROCESSING] Session {session_id} queued for background processing")
    
    # Trigger background processing in separate thread
    trigger_session_processing(app, session_id)
    
    flash('Session completed. Your progress is being processed.', 'success')
    return redirect(url_for('client_home'))

def process_session_extraction(session_id):
    """
    Process session extraction and persist updates.
    This is the core post-session processing pipeline.
    """
    session = db.session.get(Session, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    engagement = session.engagement
    
    logging.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
    
    context = build_coaching_context(engagement.id)
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]
    
    logging.info(f"[EXTRACTION] Session has {len(messages)} messages")
    logging.info(f"[EXTRACTION] Open commitments: {len(context.get('open_commitments', []))}")
    logging.info(f"[EXTRACTION] Current risks: {len(context.get('current_risks', []))}")
    
    if len(messages) < 2:
        logging.info("[EXTRACTION] Session too short for extraction")
        session.summary = "Brief session - no significant updates"
        db.session.commit()
        return
    
    try:
        ai_service = AIService()
        extraction_prompt = build_extraction_prompt()
        
        logging.info("[EXTRACTION] Calling AI service for extraction")
        
        extraction = ai_service.extract_session_outcomes(
            messages=messages,
            context=context,
            extraction_prompt=extraction_prompt
        )
        
        logging.info(f"[EXTRACTION] Extraction result keys: {list(extraction.keys())}")
        logging.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')[:100]}")
        logging.info(f"[EXTRACTION] New commitments: {len(extraction.get('new_commitments', []))}")
        logging.info(f"[EXTRACTION] Commitment updates: {len(extraction.get('commitment_updates', []))}")
        logging.info(f"[EXTRACTION] New risks: {len(extraction.get('new_risks', []))}")
        logging.info(f"[EXTRACTION] Risk updates: {len(extraction.get('risk_updates', []))}")
        logging.info(f"[EXTRACTION] New observations: {len(extraction.get('new_observations', []))}")
        logging.info(f"[EXTRACTION] Advisor attention items: {len(extraction.get('advisor_attention_items', []))}")
        
        validator = ExtractionValidator(engagement.id, pathway_data, context)
        is_valid, errors = validator.validate_extraction(extraction)
        
        if not is_valid:
            logging.error(f"[EXTRACTION] Validation failed: {errors}")
            session.summary = "Session completed - validation errors prevented some updates"
            db.session.commit()
            return
        
        logging.info("[EXTRACTION] Validation passed, applying updates")
        
        changes = apply_extraction_updates(engagement.id, extraction)
        
        session_summary = extraction.get('session_summary', 'Session completed')
        session.summary = session_summary
        db.session.commit()
        
        logging.info(f"[EXTRACTION] Session extraction complete. Changes: {changes}")
        logging.info(f"[EXTRACTION] Session summary persisted: {session_summary[:100]}")
        
    except AIServiceError as e:
        logging.error(f"AI service error during extraction: {str(e)}")
        session.summary = "Session completed - AI extraction unavailable"
        db.session.commit()
        raise
    except Exception as e:
        logging.error(f"Unexpected error during extraction: {str(e)}")
        session.summary = "Session completed - processing error"
        db.session.commit()
        raise

@app.route('/debug/session/<int:session_id>')
@login_required
def debug_session(session_id):
    """
    Debug view for session extraction details.
    Shows before/after context and extraction results.
    """
    session = db.session.get(Session, session_id)
    
    if not session:
        flash('Session not found.', 'error')
        return redirect(url_for('index'))
    
    engagement = session.engagement
    
    if current_user.role == 'CLIENT' and engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    if current_user.role == 'ADVISOR' and engagement.advisor_id != current_user.advisor.id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    context = build_coaching_context(engagement.id)
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]
    
    debug_info = {
        'session_id': session.id,
        'status': session.status,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        'summary': session.summary,
        'message_count': len(messages),
        'context': context,
        'messages': messages
    }
    
    return jsonify(debug_info)

# ============================================================================
# BUILD 003 - VOICE SESSION ROUTES
# ============================================================================

@app.route('/voice/session/init/<int:engagement_id>', methods=['POST'])
@require_role('CLIENT')
def init_voice_session(engagement_id):
    """
    Initialize a voice session and return configuration for ElevenLabs.
    
    This route:
    1. Validates client access
    2. Creates a Session record with interaction_type='voice'
    3. Builds coaching context
    4. Generates ElevenLabs signed URL
    5. Returns configuration for client-side voice initialization
    """
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        voice_service = get_voice_service()
    except Exception as e:
        logging.error(f"Voice service initialization failed: {str(e)}")
        return jsonify({'error': 'Voice service not available'}), 503
    
    session = Session(
        engagement_id=engagement_id,
        started_at=datetime.utcnow(),
        interaction_type='voice',
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    
    try:
        context = build_coaching_context(engagement_id)
        pathway_data = load_pathway(engagement.pathway_id)
        pathway_state = engagement.pathway_state
        
        # Voice Spike 001D-1: Pass application identifiers for round-trip
        signed_url_data = voice_service.generate_signed_url(
            session_id=str(session.id),
            engagement_id=engagement_id
        )
        
        session_config = voice_service.build_session_config(
            client_name=engagement.client.first_name,
            business_name=engagement.client.business.business_name,
            pathway_data=pathway_data,
            current_stage=pathway_state.current_stage_id if pathway_state else 'RS-01',
            current_day=pathway_state.current_day if pathway_state else 1,
            coaching_context=format_context_for_display(context),
            session_id=str(session.id),
            user_id=str(current_user.id),
            engagement_id=engagement_id
        )
        
        response_data = {
            'session_id': session.id,
            'signed_url': signed_url_data['signed_url'],
            'config': session_config,
            'client_name': engagement.client.first_name  # For ElevenLabs dynamicVariables
        }
        
        logging.info(f"Voice session {session.id} initialized for engagement {engagement_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Failed to initialize voice session: {str(e)}")
        db.session.delete(session)
        db.session.commit()
        return jsonify({'error': 'Failed to initialize voice session'}), 500

@app.route('/voice/session/<int:session_id>/complete', methods=['POST'])
@require_role('CLIENT')
def complete_voice_session(session_id):
    """
    Complete a voice session and process the conversation.
    
    This route:
    1. Receives conversation data from the client
    2. Normalizes it into SessionMessage format
    3. Marks the session as completed
    4. Triggers the existing Build 002 extraction pipeline
    """
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Session not found or access denied'}), 403
    
    if session.status != 'active':
        return jsonify({'error': 'Session is not active'}), 400
    
    if session.interaction_type != 'voice':
        return jsonify({'error': 'Not a voice session'}), 400
    
    try:
        conversation_data = request.get_json()
        
        if not conversation_data:
            return jsonify({'error': 'No conversation data provided'}), 400
        
        voice_service = get_voice_service()
        
        if not voice_service.validate_conversation_data(conversation_data):
            return jsonify({'error': 'Invalid conversation data'}), 400
        
        messages = voice_service.normalize_conversation_to_messages(conversation_data)
        
        for msg_data in messages:
            session_msg = SessionMessage(
                session_id=session_id,
                role=msg_data.get('role', 'user'),
                content=msg_data.get('content', ''),
                created_at=msg_data.get('timestamp') or datetime.utcnow()
            )
            db.session.add(session_msg)
        
        metadata = voice_service.get_conversation_metadata(conversation_data)
        
        session.ended_at = datetime.utcnow()
        session.status = 'completed'
        db.session.commit()
        
        logging.info(f"Voice session {session_id} completed. Messages: {len(messages)}")
        
        try:
            process_session_extraction(session.id)
            
            return jsonify({
                'status': 'success',
                'message': 'Voice session completed and processed',
                'session_id': session.id,
                'metadata': metadata
            }), 200
            
        except Exception as e:
            logging.error(f"Extraction failed for voice session {session_id}: {str(e)}")
            return jsonify({
                'status': 'partial_success',
                'message': 'Session saved but extraction failed',
                'session_id': session.id,
                'error': str(e)
            }), 200
        
    except Exception as e:
        logging.error(f"Failed to complete voice session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to process voice session'}), 500

@app.route('/voice/session/<int:session_id>/cancel', methods=['POST'])
@require_role('CLIENT')
def cancel_voice_session(session_id):
    """
    Cancel an interrupted voice session safely.
    
    This handles cases where the client closes the browser or the
    connection is lost before normal completion.
    """
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Session not found or access denied'}), 403
    
    if session.status != 'active':
        return jsonify({'error': 'Session is not active'}), 400
    
    try:
        session.ended_at = datetime.utcnow()
        session.status = 'cancelled'
        session.summary = 'Session interrupted'
        db.session.commit()
        
        logging.info(f"Voice session {session_id} cancelled")
        
        return jsonify({
            'status': 'success',
            'message': 'Session cancelled'
        }), 200
        
    except Exception as e:
        logging.error(f"Failed to cancel voice session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to cancel session'}), 500

# ============================================================================
# ADVISOR AI GUIDE - Voice application support
# ============================================================================

@app.route('/voice/advisor/init', methods=['POST'])
@require_role('ADVISOR')
def init_advisor_voice():
    """
    Initialize an Advisor AI Guide voice conversation.
    
    Returns a signed URL and minimal config for the ElevenLabs
    Advisor AI Guide agent. No session record is created and no
    client coaching context is passed.
    """
    try:
        voice_service = get_advisor_voice_service()
    except Exception as e:
        logging.error(f"Advisor voice service initialization failed: {str(e)}")
        return jsonify({'error': 'Advisor voice service not available'}), 503
    
    try:
        signed_url_data = voice_service.generate_signed_url()
    except Exception as e:
        logging.error(f"Failed to generate advisor signed URL: {str(e)}")
        return jsonify({'error': 'Failed to initialize advisor voice session'}), 500
    
    config = {
        'agent_id': voice_service.agent_id,
        'user_id': str(current_user.id)
    }
    
    return jsonify({
        'signed_url': signed_url_data['signed_url'],
        'config': config,
        'advisor_name': current_user.advisor.first_name
    }), 200


@app.cli.command('init-db')
def init_db():
    os.makedirs('data', exist_ok=True)
    db.create_all()
    print('Database initialized.')

@app.cli.command('seed-data')
def seed_data():
    from werkzeug.security import generate_password_hash
    from datetime import date
    
    print('Seeding database...')
    
    advisor_user = User(
        email='ronda@example.com',
        role='ADVISOR',
        active=True
    )
    advisor_user.set_password('advisor123')
    db.session.add(advisor_user)
    db.session.flush()
    
    advisor = Advisor(
        user_id=advisor_user.id,
        first_name='Ronda',
        last_name='Advisor'
    )
    db.session.add(advisor)
    db.session.flush()
    
    client_a_user = User(
        email='sarah@example.com',
        role='CLIENT',
        active=True
    )
    client_a_user.set_password('client123')
    db.session.add(client_a_user)
    db.session.flush()
    
    client_a = Client(
        user_id=client_a_user.id,
        first_name='Sarah',
        last_name='Johnson'
    )
    db.session.add(client_a)
    db.session.flush()
    
    business_a = Business(
        client_id=client_a.id,
        business_name="Sarah's Hardware",
        industry='Retail',
        business_description='Local hardware store serving the community for 15 years',
        current_situation_summary='Experiencing cash flow challenges following recent market changes. Working on stabilization plan.'
    )
    db.session.add(business_a)
    
    engagement_a = Engagement(
        client_id=client_a.id,
        advisor_id=advisor.id,
        pathway_id='PATHWAY-001',
        pathway_version='0.1',
        status='active',
        start_date=date.today() - timedelta(days=18),
        target_end_date=date.today() + timedelta(days=72)
    )
    db.session.add(engagement_a)
    db.session.flush()
    
    pathway_state_a = PathwayState(
        engagement_id=engagement_a.id,
        current_stage_id='RS-01',
        current_day=18,
        current_focus='Short-term liquidity and cash visibility',
        current_priority_summary='Maintain 14-day cash visibility, complete lender preparation, continue customer outreach'
    )
    db.session.add(pathway_state_a)
    
    commitment_a1 = Commitment(
        engagement_id=engagement_a.id,
        description='Contact lender to discuss payment modification',
        due_date=date.today() - timedelta(days=2),
        status='open',
        priority='high'
    )
    db.session.add(commitment_a1)
    
    commitment_a2 = Commitment(
        engagement_id=engagement_a.id,
        description='Update 14-day cash tracker',
        due_date=date.today() + timedelta(days=2),
        status='open',
        priority='high'
    )
    db.session.add(commitment_a2)
    
    commitment_a3 = Commitment(
        engagement_id=engagement_a.id,
        description='Contact five inactive customers',
        status='open',
        priority='normal'
    )
    db.session.add(commitment_a3)
    
    risk_a1 = Risk(
        engagement_id=engagement_a.id,
        title='Johnson account lost',
        description='Major customer Johnson account was lost. Estimated revenue impact: $4,000/month',
        severity='high',
        status='open',
        advisor_attention=True
    )
    db.session.add(risk_a1)
    
    risk_a2 = Risk(
        engagement_id=engagement_a.id,
        title='Lender contact delayed',
        description='Client has postponed lender discussion twice',
        severity='moderate',
        status='open',
        advisor_attention=False
    )
    db.session.add(risk_a2)
    
    event_a1 = SignificantEvent(
        engagement_id=engagement_a.id,
        title='Lost Johnson account',
        description='Johnson account decided to switch to online supplier',
        event_date=date.today() - timedelta(days=5),
        estimated_impact='$4,000/month revenue reduction'
    )
    db.session.add(event_a1)
    
    learning_a1 = LearningRecord(
        engagement_id=engagement_a.id,
        resource_id='RS-R001',
        status='completed',
        recommended_at=datetime.utcnow() - timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(days=6),
        client_reflection='Now I understand why we can be profitable but still have cash problems',
        follow_up_required=False
    )
    db.session.add(learning_a1)
    
    observation_a1 = CoachingObservation(
        engagement_id=engagement_a.id,
        observation='Client is consistently completing operational tasks but avoiding lender outreach',
        importance='high',
        status='active'
    )
    db.session.add(observation_a1)
    
    session_a1 = Session(
        engagement_id=engagement_a.id,
        started_at=datetime.utcnow() - timedelta(days=3),
        ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
        interaction_type='voice',
        summary='Client reported Johnson account loss and agreed to update cash forecast'
    )
    db.session.add(session_a1)
    
    guidance_a1 = AdvisorGuidance(
        engagement_id=engagement_a.id,
        advisor_id=advisor.id,
        guidance='For the next two weeks, prioritize cash visibility and lender preparation. Do not introduce additional revenue initiatives until those actions are complete.',
        priority='high',
        status='active'
    )
    db.session.add(guidance_a1)
    
    attention_a1 = AdvisorAttention(
        engagement_id=engagement_a.id,
        title='Lender contact repeatedly deferred',
        description='Client has postponed lender discussion for second consecutive week',
        priority='high',
        status='open'
    )
    db.session.add(attention_a1)
    
    client_b_user = User(
        email='michael@example.com',
        role='CLIENT',
        active=True
    )
    client_b_user.set_password('client123')
    db.session.add(client_b_user)
    db.session.flush()
    
    client_b = Client(
        user_id=client_b_user.id,
        first_name='Michael',
        last_name='Chen'
    )
    db.session.add(client_b)
    db.session.flush()
    
    business_b = Business(
        client_id=client_b.id,
        business_name="Chen's Bakery",
        industry='Food Service',
        business_description='Family bakery specializing in artisan breads and pastries',
        current_situation_summary='Recovering from equipment failure. Implementing cost controls and revenue recovery plan.'
    )
    db.session.add(business_b)
    
    engagement_b = Engagement(
        client_id=client_b.id,
        advisor_id=advisor.id,
        pathway_id='PATHWAY-001',
        pathway_version='0.1',
        status='active',
        start_date=date.today() - timedelta(days=42),
        target_end_date=date.today() + timedelta(days=48)
    )
    db.session.add(engagement_b)
    db.session.flush()
    
    pathway_state_b = PathwayState(
        engagement_id=engagement_b.id,
        current_stage_id='RS-02',
        current_day=42,
        current_focus='Revenue activation from proven customers',
        current_priority_summary='Complete customer outreach cycle, review vendor opportunities'
    )
    db.session.add(pathway_state_b)
    
    commitment_b1 = Commitment(
        engagement_id=engagement_b.id,
        description='Complete outreach to top 10 wholesale customers',
        due_date=date.today() + timedelta(days=5),
        status='open',
        priority='high'
    )
    db.session.add(commitment_b1)
    
    risk_b1 = Risk(
        engagement_id=engagement_b.id,
        title='Equipment replacement costs',
        description='Oven repair costs higher than expected',
        severity='moderate',
        status='open',
        advisor_attention=False
    )
    db.session.add(risk_b1)
    
    db.session.commit()
    
    print('Database seeded successfully!')
    print('\nTest User Credentials:')
    print('=' * 50)
    print('Advisor:')
    print('  Email: ronda@example.com')
    print('  Password: advisor123')
    print('\nClient A (Sarah):')
    print('  Email: sarah@example.com')
    print('  Password: client123')
    print('\nClient B (Michael):')
    print('  Email: michael@example.com')
    print('  Password: client123')
    print('=' * 50)

@app.cli.command('create-admin')
def create_admin():
    """Create the first admin user from ADMIN_EMAIL and ADMIN_PASSWORD env vars."""
    email = os.environ.get('ADMIN_EMAIL')
    password = os.environ.get('ADMIN_PASSWORD')
    
    if not email or not password:
        raise click.ClickException('ERROR: ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required.')
    
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise click.ClickException(f'ERROR: User {email} already exists (role={existing.role}).')
    
    admin_user = User(email=email, role='ADMIN', active=True)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    print(f'Admin user created: {email}')
    print('Change the default password immediately.')


def bootstrap_admin():
    """Create the initial admin user from ADMIN_EMAIL and ADMIN_PASSWORD at startup."""
    email = os.environ.get('ADMIN_EMAIL')
    password = os.environ.get('ADMIN_PASSWORD')
    
    if not email or not password:
        logging.info('ADMIN BOOTSTRAP: credentials not configured; skipping')
        return
    
    with app.app_context():
        try:
            existing = User.query.filter_by(email=email).first()
            if existing:
                logging.info(f'ADMIN BOOTSTRAP: User already exists; skipping: {email}')
                return
            
            admin_user = User(email=email, role='ADMIN', active=True)
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            logging.info(f'ADMIN BOOTSTRAP: Admin user created: {email}')
        except Exception as e:
            db.session.rollback()
            logging.error(f'ADMIN BOOTSTRAP: failed to create admin: {str(e)}')


def ensure_database_schema():
    """Create any missing database tables. Idempotent; does not drop or modify existing tables."""
    try:
        with app.app_context():
            db.create_all()
            logging.info('[STARTUP] Database schema verified.')
    except Exception as e:
        logging.error(f'[STARTUP] Database schema verification failed: {str(e)}')


# Process any pending sessions on startup (recovery mechanism)
# Flask 3.x compatible: Call directly after app initialization
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

# ============================================================
# ELEVENLABS WEBHOOK ENDPOINT (Connectivity Spike)
# ============================================================

@app.route('/webhooks/elevenlabs/post-call', methods=['POST'])
def elevenlabs_post_call_webhook():
    """
    ElevenLabs Post-Call Webhook receiver.
    
    Voice Spike 001D-1: Identity Round-Trip
    
    Purpose: Verify that application-controlled identity can be recovered
    from ElevenLabs post-call webhooks.
    
    This endpoint:
    - Verifies HMAC signature (if ELEVENLABS_WEBHOOK_SECRET is configured)
    - Accepts POST requests from ElevenLabs
    - Extracts application identity metadata
    - Logs the received payload and identity for inspection
    - Returns HTTP 200
    
    This endpoint does NOT (yet):
    - Create or modify database records
    - Associate webhooks with clients
    - Create coaching sessions
    - Invoke AI coaching service
    - Invoke extraction/validation/persistence
    - Update pathway state
    - Create commitments or risks
    
    Identity round-trip is proven, but transcript persistence is deferred
    to Voice Spike 001D-2.
    """
    try:
        # Voice Spike 001D-1: HMAC Signature Verification
        webhook_secret = os.environ.get('ELEVENLABS_WEBHOOK_SECRET')
        if webhook_secret:
            signature_header = request.headers.get('ElevenLabs-Signature')
            if not signature_header:
                logging.warning("ELEVENLABS WEBHOOK: Missing signature header")
                return jsonify({'error': 'Missing signature'}), 401
            
            # Verify HMAC signature
            import hmac
            import hashlib
            
            request_body = request.get_data()
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature_header, expected_signature):
                logging.warning("ELEVENLABS WEBHOOK: Invalid signature")
                return jsonify({'error': 'Invalid signature'}), 401
            
            logging.info("ELEVENLABS WEBHOOK: Signature verified")
        else:
            logging.warning("ELEVENLABS WEBHOOK: No webhook secret configured - signature verification skipped")
        
        # Get raw request data
        content_type = request.content_type or 'unknown'
        
        logging.info("=" * 60)
        logging.info("ELEVENLABS POST-CALL WEBHOOK RECEIVED")
        logging.info("=" * 60)
        logging.info(f"Content-Type: {content_type}")
        logging.info(f"Request Method: {request.method}")
        logging.info(f"Remote Address: {request.remote_addr}")
        
        # Attempt to parse JSON payload
        if request.is_json:
            try:
                payload = request.get_json()
                
                # Voice Spike 001D-1: Extract application identity
                logging.info("=" * 60)
                logging.info("ELEVENLABS VOICE IDENTITY TEST")
                logging.info("=" * 60)
                
                # Extract ElevenLabs conversation ID
                conversation_id = payload.get('conversation_id') or payload.get('id')
                logging.info(f"ElevenLabs conversation: {conversation_id}")
                
                # Extract application identity from custom metadata
                # The exact location depends on ElevenLabs webhook payload structure
                app_metadata = None
                identity_recovered = False
                
                # Check common locations for custom metadata
                if 'metadata' in payload:
                    app_metadata = payload['metadata']
                elif 'custom_llm_extra_body' in payload:
                    app_metadata = payload['custom_llm_extra_body']
                elif 'analysis' in payload and isinstance(payload['analysis'], dict):
                    app_metadata = payload['analysis'].get('custom_llm_extra_body')
                
                if app_metadata:
                    app_session_id = app_metadata.get('app_session_id')
                    app_engagement_id = app_metadata.get('app_engagement_id')
                    app_platform = app_metadata.get('app_platform')
                    
                    logging.info(f"Application session: {app_session_id}")
                    logging.info(f"Application engagement: {app_engagement_id}")
                    logging.info(f"Application platform: {app_platform}")
                    
                    if app_session_id and app_engagement_id:
                        identity_recovered = True
                        logging.info("Identity recovered: YES")
                    else:
                        logging.info("Identity recovered: PARTIAL (missing fields)")
                else:
                    logging.info("Application metadata: NOT FOUND")
                    logging.info("Identity recovered: NO")
                
                logging.info("=" * 60)
                
                # Pretty-print the full JSON payload for inspection
                import json
                payload_str = json.dumps(payload, indent=2, default=str)
                
                logging.info("Full Payload (JSON):")
                logging.info(payload_str)
                
            except Exception as json_error:
                logging.error(f"Failed to parse JSON payload: {str(json_error)}")
                logging.info("Raw data:")
                logging.info(request.get_data(as_text=True))
        else:
            # Not JSON, log raw data
            logging.info("Payload (not JSON):")
            logging.info(request.get_data(as_text=True))
        
        logging.info("=" * 60)
        logging.info("END ELEVENLABS WEBHOOK")
        logging.info("=" * 60)
        
        # Return success
        return jsonify({
            'status': 'received',
            'message': 'ElevenLabs post-call webhook received successfully'
        }), 200
        
    except Exception as e:
        # Log error but don't crash the application
        logging.error("=" * 60)
        logging.error("ELEVENLABS WEBHOOK ERROR")
        logging.error("=" * 60)
        logging.error(f"Error processing webhook: {str(e)}")
        logging.error("=" * 60)
        
        # Return error response
        return jsonify({
            'status': 'error',
            'message': 'Failed to process webhook'
        }), 500


# ============================================================
# STARTUP RECOVERY
# ============================================================

# Call startup recovery when running under Gunicorn or other WSGI servers
# This executes during module import, which happens once per worker
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    # Not in Flask development reloader child process
    try:
        ensure_database_schema()
    except Exception as e:
        logging.error(f"[STARTUP] Failed to ensure database schema: {str(e)}")
    
    try:
        process_pending_sessions_on_startup()
    except Exception as e:
        logging.error(f"[STARTUP] Failed to process pending sessions: {str(e)}")
    
    try:
        bootstrap_admin()
    except Exception as e:
        logging.error(f"[STARTUP] Failed to bootstrap admin: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
