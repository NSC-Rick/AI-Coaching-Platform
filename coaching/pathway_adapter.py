"""
Pathway Adapter — normalize a loaded Pathway Package into a
PathwayRuntimeContext without exposing file layout or package-version
internals.

This module is the architectural seam between the low-level package
loader (coaching.engine.load_pathway) and the coaching engine.  It
resolves package data, the current stage, and the requested day into a
standard v1-shaped runtime context.

Phase C1 scope:
- Normalize PATHWAY-001 (legacy Recovery package).
- Keep all user-state, persistence, AI, prompt, and voice concerns out.
- Do not implement progression, evidence capture, or activity selection.
"""

from .engine import load_pathway, PathwayLoadError


class PathwayAdapterError(Exception):
    """Raised when the adapter cannot build a runtime context."""
    pass


class PathwayAdapter:
    """
    Adapter that transforms a loaded package into a normalized
    PathwayRuntimeContext.
    """

    @classmethod
    def for_pathway(cls, pathway_id, current_stage_id=None, current_day=None):
        """
        Build a normalized runtime context for a pathway by loading the
        package first.

        Args:
            pathway_id: The package identifier (e.g. 'PATHWAY-001').
            current_stage_id: Optional stage to resolve.
            current_day: Optional day within the stage.

        Returns:
            dict: PathwayRuntimeContext.

        Raises:
            PathwayAdapterError: if the pathway cannot be loaded or the
                requested stage cannot be resolved.
        """
        try:
            package = load_pathway(pathway_id)
        except PathwayLoadError as e:
            raise PathwayAdapterError(str(e)) from e

        return cls.from_package(package, current_stage_id, current_day)

    @classmethod
    def from_package(cls, package, current_stage_id=None, current_day=None):
        """
        Build a normalized runtime context from an already loaded package.

        This avoids re-loading the package when the caller already holds
        the load_pathway() result.
        """
        manifest = package.get('manifest', {})

        runtime = {
            'pathway': cls._normalize_pathway(manifest),
            'current_stage': cls._resolve_stage(manifest, current_stage_id),
            'development': {
                'primary_capabilities': [],
                'reinforcing_capabilities': [],
                'target_behaviors': []
            },
            'coaching': cls._normalize_coaching(package, current_stage_id),
            'practice': {'relevant_activities': []},
            'evidence': {'relevant_evidence': []},
            'progression': cls._normalize_progression(manifest, current_stage_id),
            'completion': {'criteria': []},
            'resources': cls._normalize_resources(package)
        }

        if current_day is not None and runtime['current_stage']:
            runtime['current_stage']['current_day'] = current_day

        return runtime

    @classmethod
    def _normalize_pathway(cls, manifest):
        """Normalize the identity section."""
        return {
            'id': manifest.get('pathway_id'),
            'slug': manifest.get('slug'),
            'name': manifest.get('name'),
            'version': manifest.get('version'),
            'status': manifest.get('status'),
            'domain': manifest.get('domain'),  # None for legacy Recovery
            'purpose': manifest.get('purpose'),
            'core_rule': manifest.get('core_rule'),
            'target_user': manifest.get('target_user'),  # None for legacy
            'entry_context': manifest.get('entry_context'),  # None for legacy
            'expected_outcome': manifest.get('expected_outcome'),  # None for legacy
            'default_duration_days': manifest.get('default_duration_days'),
            'development_dimensions': cls._normalize_development_dimensions(manifest)
        }

    @classmethod
    def _normalize_development_dimensions(cls, manifest):
        """Normalize development dimensions when supplied by the pathway."""
        dimensions = manifest.get('development_dimensions', [])
        if not dimensions:
            return []
        normalized = []
        for dim in dimensions:
            normalized.append({
                'dimension_id': dim.get('dimension_id'),
                'name': dim.get('name'),
                'description': dim.get('description')
            })
        return normalized

    @classmethod
    def _resolve_stage(cls, manifest, current_stage_id):
        """Resolve and normalize the current stage."""
        if current_stage_id is None:
            return None

        stages = manifest.get('stages', [])

        for stage in stages:
            if stage.get('stage_id') == current_stage_id:
                return {
                    'id': stage.get('stage_id'),
                    'name': stage.get('name'),
                    'description': stage.get('purpose'),  # Legacy uses 'purpose'
                    'purpose': stage.get('purpose'),
                    'objectives': stage.get('objectives', []),
                    'typical_days': stage.get('typical_days'),
                    'exit_conditions': []
                }

        raise PathwayAdapterError(f"Stage not found: {current_stage_id}")

    @classmethod
    def _normalize_coaching(cls, package, current_stage_id):
        """Normalize coaching content for the resolved stage."""
        guidance_text = package.get('coaching_guidance', '')
        return {
            'methodology': package.get('methodology', ''),
            'guidance': guidance_text,
            'pathway_wide_guidance': cls._extract_pathway_wide_guidance(guidance_text),
            'stage_guidance': cls._extract_stage_guidance(guidance_text, current_stage_id),
            'guardrails': package.get('guardrails', '')
        }

    @classmethod
    def _extract_pathway_wide_guidance(cls, guidance_text):
        """
        Return coaching guidance with the stage-specific block removed.

        This keeps pathway-wide posture, behavior rules, privacy guidance,
        and other universal coaching instructions separate from the
        current-stage guidance.
        """
        if not guidance_text:
            return ''

        start, end = cls._locate_stage_specific_block(guidance_text)
        if start is None:
            return guidance_text.strip()

        before = guidance_text[:start].rstrip()
        after = guidance_text[end:].lstrip() if end is not None else ''

        if before and after:
            return f"{before}\n\n{after}".strip()
        return (before or after).strip()

    @classmethod
    def _locate_stage_specific_block(cls, guidance_text):
        """
        Locate the stage-specific section within coaching_guidance.md.

        Returns (start, end) character offsets, where start is the
        beginning of the '## Stage-Specific Guidance' heading and end is
        the start of the next '## ' heading (or None if it runs to EOF).
        """
        if not guidance_text:
            return None, None

        import re
        pattern = re.compile(r'^##\s+Stage[-\s]Specific Guidance\s*$', re.IGNORECASE | re.MULTILINE)
        match = pattern.search(guidance_text)
        if not match:
            return None, None

        start = match.start()
        next_heading = re.search(r'^##\s', guidance_text[match.end():], re.MULTILINE)
        if next_heading:
            end = match.end() + next_heading.start()
        else:
            end = None

        return start, end

    @classmethod
    def _extract_stage_guidance(cls, guidance_text, stage_id):
        """Extract the section of coaching guidance relevant to a stage."""
        if not stage_id or not guidance_text:
            return ''

        start, end = cls._locate_stage_specific_block(guidance_text)
        if start is not None:
            block = guidance_text[start:end] if end is not None else guidance_text[start:]
        else:
            block = guidance_text

        lines = block.split('\n')
        relevant_lines = []
        capturing = False

        for line in lines:
            if not capturing:
                if stage_id in line and line.lstrip().startswith('#'):
                    capturing = True
                    continue
            else:
                if line.lstrip().startswith('#') and stage_id not in line:
                    break
                relevant_lines.append(line)

        return '\n'.join(relevant_lines).strip()

    @classmethod
    def _normalize_progression(cls, manifest, current_stage_id):
        """
        Normalize progression semantics.  For PATHWAY-001, the package is
        time-oriented, so the type is reported as 'time_based'.  No
        automatic progression logic is implemented.
        """
        stages = manifest.get('stages', [])
        next_stage_id = None

        if current_stage_id:
            stage_ids = [s.get('stage_id') for s in stages]
            try:
                idx = stage_ids.index(current_stage_id)
                if idx + 1 < len(stage_ids):
                    next_stage_id = stage_ids[idx + 1]
            except ValueError:
                # current_stage_id not in stages — _resolve_stage already errors
                pass

        return {
            'progression_type': 'time_based',
            'from_stage': current_stage_id,
            'to_stage': next_stage_id,
            'description': 'Time-oriented stage sequence.',
            'evidence_considered': []
        }

    @classmethod
    def _normalize_resources(cls, package):
        """Normalize all resources from the package."""
        resources_data = package.get('resources', {})
        all_resources = resources_data.get('resources', [])

        normalized = []
        for r in all_resources:
            normalized.append({
                'resource_id': r.get('resource_id'),
                'title': r.get('title'),
                'resource_type': r.get('resource_type'),
                'description': r.get('description'),
                'location': r.get('location'),
                'learning_objective': r.get('learning_objective'),
                'when_to_recommend': r.get('when_to_recommend', []),
                'related_stage': r.get('related_stage'),
                'follow_up_questions': r.get('follow_up_questions', [])
            })

        return {'available_resources': normalized}
