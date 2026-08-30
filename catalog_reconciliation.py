"""
Safe, idempotent catalog reconciliation for the AI Coaching Platform.

This module bridges the gap between runtime-ready pathway packages
(on disk under pathways/) and the persistent Pathway/InformationDomain
catalog in PostgreSQL. It is safe to run repeatedly against a populated
production database: it creates missing records, reconciles safe metadata,
and never deletes existing pathways, domains, engagements, or coaching
history.
"""

import os
from models import (
    InformationDomain,
    Pathway,
    AdvisorDomainAccess,
    Advisor,
    User
)


class ReconciliationError(Exception):
    """Raised when the catalog state is too ambiguous to reconcile safely."""
    pass


class AmbiguousDomainError(ReconciliationError):
    """Raised when multiple OCM-like domains exist and cannot be canonicalized."""
    pass


def _find_domain_case_insensitive(db, name):
    """Return the first InformationDomain whose name matches case-insensitively."""
    return InformationDomain.query.filter(
        db.func.lower(InformationDomain.name) == name.lower()
    ).first()


def _canonical_ocm_domain(db, dry_run=False):
    """
    Return the canonical Organizational Change Management domain.

    Strategy:
      1. If a domain named exactly 'Organizational Change Management' exists, use it.
      2. If only a legacy 'Change Management' domain exists, rename it to
         'Organizational Change Management' so existing FK relationships are preserved.
      3. If neither exists, create 'Organizational Change Management'.
      4. If both exist as separate rows, raise AmbiguousDomainError and do not modify.
    """

    ocm = _find_domain_case_insensitive(db, 'Organizational Change Management')
    legacy_cm = _find_domain_case_insensitive(db, 'Change Management')

    if ocm and legacy_cm and ocm.id != legacy_cm.id:
        raise AmbiguousDomainError(
            f"Both 'Organizational Change Management' (id={ocm.id}) and "
            f"'Change Management' (id={legacy_cm.id}) exist. "
            "Manual review is required before reconciliation can proceed safely."
        )

    if ocm:
        if ocm.status != 'active':
            if not dry_run:
                ocm.status = 'active'
            return ocm, "Activated existing Organizational Change Management domain"
        return ocm, "Using existing Organizational Change Management domain"

    if legacy_cm:
        if not dry_run:
            legacy_cm.name = 'Organizational Change Management'
            legacy_cm.description = (
                'Professional development pathways for Change Management practitioners'
            )
            legacy_cm.status = 'active'
        return legacy_cm, "Renamed legacy 'Change Management' domain to canonical OCM"

    if not dry_run:
        ocm = InformationDomain(
            name='Organizational Change Management',
            description='Professional development pathways for Change Management practitioners',
            status='active'
        )
        db.session.add(ocm)
        db.session.flush()
    else:
        ocm = None
    return ocm, "Created Organizational Change Management domain"


def _canonical_small_business_domain(db, dry_run=False):
    """
    Return the canonical Small Business domain, creating it if necessary.
    """

    sb = _find_domain_case_insensitive(db, 'Small Business')
    if sb:
        if sb.status != 'active':
            if not dry_run:
                sb.status = 'active'
            return sb, "Activated existing Small Business domain"
        return sb, "Using existing Small Business domain"

    if not dry_run:
        sb = InformationDomain(
            name='Small Business',
            description='Small business coaching and recovery pathways',
            status='active'
        )
        db.session.add(sb)
        db.session.flush()
    else:
        sb = None
    return sb, "Created Small Business domain"


def _load_manifest(pathway_id, load_pathway):
    """Load the pathway package and return normalized catalog fields."""
    package = load_pathway(pathway_id)
    manifest = package.get('manifest', {})
    return {
        'pathway_id': manifest.get('pathway_id', pathway_id),
        'name': manifest.get('name', pathway_id),
        'description': manifest.get('purpose', '') or '',
        'package_slug': manifest.get('slug', pathway_id.lower().replace('-', '_')),
        'version': manifest.get('version', '0.1'),
        'status': 'active',
    }


def _ensure_pathway(db, pathway_id, domain, load_pathway, dry_run=False):
    """
    Ensure a runtime-ready pathway exists in the catalog.

    If the pathway already exists, reconcile only safe catalog metadata
    (name, description, domain, status, package_slug). Do not alter the
    primary pathway_id or delete the record.
    """
    record = Pathway.query.filter_by(pathway_id=pathway_id).first()
    manifest = _load_manifest(pathway_id, load_pathway)

    if not record:
        if not dry_run:
            record = Pathway(
                pathway_id=manifest['pathway_id'],
                name=manifest['name'],
                description=manifest['description'],
                status='active',
                domain_id=domain.id,
                package_slug=manifest['package_slug']
            )
            db.session.add(record)
            db.session.flush()
        return False, f"Created Pathway {pathway_id} ({manifest['name']})"

    changed = []
    if record.name != manifest['name']:
        if not dry_run:
            record.name = manifest['name']
        changed.append('name')
    if record.domain_id != domain.id:
        if not dry_run:
            record.domain_id = domain.id
        changed.append('domain_id')
    if record.status != 'active':
        if not dry_run:
            record.status = 'active'
        changed.append('status')
    if record.package_slug != manifest['package_slug']:
        if not dry_run:
            record.package_slug = manifest['package_slug']
        changed.append('package_slug')
    if record.description != manifest['description'] and manifest['description']:
        if not dry_run:
            record.description = manifest['description']
        changed.append('description')

    if changed:
        return False, f"Reconciled Pathway {pathway_id}: {', '.join(changed)}"
    return True, f"Pathway {pathway_id} already correct"


def _ensure_advisor_domain_access(db, advisor_email, domain, dry_run=False):
    """
    Ensure the named advisor has access to the given domain.

    The advisor is located by User.email. If the advisor or user is not
    found, the function returns a warning without modifying anything.
    """
    advisor = db.session.query(Advisor).join(User).filter(
        User.email == advisor_email,
        User.role == 'ADVISOR'
    ).first()

    if not advisor:
        return None, f"Advisor with email {advisor_email} not found; no access change made"

    existing = AdvisorDomainAccess.query.filter_by(
        advisor_id=advisor.id,
        domain_id=domain.id
    ).first()

    if existing:
        return True, f"Advisor {advisor_email} already has access to {domain.name}"

    if not dry_run:
        access = AdvisorDomainAccess(
            advisor_id=advisor.id,
            domain_id=domain.id
        )
        db.session.add(access)
        db.session.flush()

    return False, f"Granted advisor {advisor_email} access to {domain.name}"


def reconcile_catalog(db, load_pathway, dry_run=False):
    """
    Reconcile runtime-ready pathway packages with the persistent catalog.

    Returns a list of (status, message) tuples describing every action taken.
    Raises AmbiguousDomainError if the domain state is too ambiguous to
    reconcile safely.

    Safe to run repeatedly.
    """
    results = []

    ocm, ocm_msg = _canonical_ocm_domain(db, dry_run=dry_run)
    results.append(('domain', ocm_msg))

    sb, sb_msg = _canonical_small_business_domain(db, dry_run=dry_run)
    results.append(('domain', sb_msg))

    for pathway_id, domain in [
        ('PATHWAY-001', sb),
        ('PATHWAY-002', ocm)
    ]:
        already_ok, msg = _ensure_pathway(db, pathway_id, domain, load_pathway, dry_run=dry_run)
        results.append(('pathway', msg))

    return results


def reconcile_advisor_access(db, advisor_email=None, domain_name='Organizational Change Management', dry_run=False):
    """
    Reconcile advisor domain access.

    Defaults to granting Rick Daniell access to the canonical OCM domain.
    The advisor email can be overridden via the RICK_ADVISOR_EMAIL
    environment variable or passed explicitly.
    """
    if advisor_email is None:
        advisor_email = os.environ.get('RICK_ADVISOR_EMAIL', 'rick.daniell@example.com')

    ocm = _find_domain_case_insensitive(db, domain_name)
    if not ocm:
        return [('access', f"Domain {domain_name} not found; cannot grant advisor access")]

    already_ok, msg = _ensure_advisor_domain_access(db, advisor_email, ocm, dry_run=dry_run)
    return [('access', msg)]
