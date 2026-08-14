from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    advisor = db.relationship('Advisor', backref='user', uselist=False, cascade='all, delete-orphan')
    client = db.relationship('Client', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_active(self):
        return self.active


class Advisor(db.Model):
    __tablename__ = 'advisors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
    engagements = db.relationship('Engagement', backref='advisor', lazy=True)
    advisor_guidance = db.relationship('AdvisorGuidance', backref='advisor', lazy=True)


class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
    business = db.relationship('Business', backref='client', uselist=False, cascade='all, delete-orphan')
    engagements = db.relationship('Engagement', backref='client', lazy=True)


class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    business_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    business_description = db.Column(db.Text)
    current_situation_summary = db.Column(db.Text)


class Engagement(db.Model):
    __tablename__ = 'engagements'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    pathway_id = db.Column(db.String(50), nullable=False)
    pathway_version = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')
    start_date = db.Column(db.Date, nullable=False)
    target_end_date = db.Column(db.Date)
    
    pathway_state = db.relationship('PathwayState', backref='engagement', uselist=False, cascade='all, delete-orphan')
    commitments = db.relationship('Commitment', backref='engagement', lazy=True, cascade='all, delete-orphan')
    risks = db.relationship('Risk', backref='engagement', lazy=True, cascade='all, delete-orphan')
    significant_events = db.relationship('SignificantEvent', backref='engagement', lazy=True, cascade='all, delete-orphan')
    learning_records = db.relationship('LearningRecord', backref='engagement', lazy=True, cascade='all, delete-orphan')
    coaching_observations = db.relationship('CoachingObservation', backref='engagement', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='engagement', lazy=True, cascade='all, delete-orphan')
    advisor_guidance = db.relationship('AdvisorGuidance', backref='engagement', lazy=True, cascade='all, delete-orphan')
    advisor_attention = db.relationship('AdvisorAttention', backref='engagement', lazy=True, cascade='all, delete-orphan')


class PathwayState(db.Model):
    __tablename__ = 'pathway_states'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    current_stage_id = db.Column(db.String(50), nullable=False)
    current_day = db.Column(db.Integer, nullable=False)
    current_focus = db.Column(db.Text)
    current_priority_summary = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Commitment(db.Model):
    __tablename__ = 'commitments'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50), nullable=False, default='open')
    priority = db.Column(db.String(50))
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)


class Risk(db.Model):
    __tablename__ = 'risks'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='open')
    advisor_attention = db.Column(db.Boolean, default=False, nullable=False)
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SignificantEvent(db.Model):
    __tablename__ = 'significant_events'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    estimated_impact = db.Column(db.Text)
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class LearningRecord(db.Model):
    __tablename__ = 'learning_records'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    resource_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='recommended')
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    client_reflection = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False, nullable=False)


class CoachingObservation(db.Model):
    __tablename__ = 'coaching_observations'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    observation = db.Column(db.Text, nullable=False)
    importance = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False, default='active')
    source = db.Column(db.String(50), default='ai_extraction')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime)
    interaction_type = db.Column(db.String(50), nullable=False, default='voice')
    status = db.Column(db.String(50), nullable=False, default='active')
    processing_status = db.Column(db.String(50), default='none')  # none, pending, processing, complete, failed
    summary = db.Column(db.Text)
    
    messages = db.relationship('SessionMessage', backref='session', lazy=True, cascade='all, delete-orphan', order_by='SessionMessage.created_at')


class AdvisorGuidance(db.Model):
    __tablename__ = 'advisor_guidance'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    guidance = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AdvisorAttention(db.Model):
    __tablename__ = 'advisor_attention'
    
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(50), nullable=False, default='normal')
    status = db.Column(db.String(50), nullable=False, default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SessionMessage(db.Model):
    __tablename__ = 'session_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
