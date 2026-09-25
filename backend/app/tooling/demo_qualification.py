"""Populate deterministic synthetic records for disposable local UI qualification."""
from __future__ import annotations

import importlib
from datetime import date
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.registry import DEFINITIONS, ENTITY_BINDINGS
from app.platform.entity_registry import EntityRegistry, load_relationship_definitions
from app.platform.models import EntityRelationship
from app.platform.notifications import create as create_notification, set_preference
from app.platform.schemas import NotificationCreate, RelationshipCreate
from app.platform.security import Actor
from app.platform.workspace_registry import WorkspaceRegistry
from app.platform.relationships import create as create_relationship

FIXTURE_KIND = 'local_synthetic_demo'


def _registries():
    workspaces = WorkspaceRegistry(DEFINITIONS)
    relationships_file = Path(__file__).resolve().parents[1] / 'config' / 'relationships.json'
    entities = EntityRegistry(ENTITY_BINDINGS, load_relationship_definitions(relationships_file), workspaces.definitions())
    return entities


def _record(session: Session, actor: Actor, workspace: str, values: dict):
    service = importlib.import_module(f'app.features.{workspace}.service')
    payload = service.CRUD.create_schema.model_validate(values)
    return service.CRUD.create(session, actor, payload)


def _link(session: Session, actor: Actor, entities: EntityRegistry, key: str, source, target, metadata: dict | None = None):
    return create_relationship(session, actor, entities, RelationshipCreate(
        definition_key=key, source_id=source.id, target_id=target.id, metadata=metadata or {},
    ))


def seed_demo_qualification(database, tenant_id: str, user_id: str = 'demo.admin') -> dict:
    """Create one bounded, realistic fixture using feature CRUD and relationship APIs.

    The caller is the explicit demo-seed command, which refuses company and
    production profiles and only operates on a new disposable data root.
    """
    actor = Actor(user_id, tenant_id, 'admin', 'demo-qualification-fixture', frozenset({
        'read', 'write', 'restore', 'export', 'import', 'admin', 'manage_members',
    }))
    entities = _registries()
    with database.session(tenant_id) as session:
        records: dict[str, list] = {}

        def add(workspace: str, *rows: dict):
            records.setdefault(workspace, []).extend(_record(session, actor, workspace, row) for row in rows)
            return records[workspace][-len(rows):]

        work_items = add('work_items',
            {'title': 'Qualify synthetic process excursion evidence', 'description': 'Compare the measurement trail with the equipment and recipe history.', 'status': 'open', 'priority': 'high'},
            {'title': 'Recover retrying telemetry delivery', 'description': 'Verify retry, recovery and service objective effects in the local fixture.', 'status': 'in_progress', 'priority': 'normal'},
            {'title': 'Document chamber maintenance handoff', 'description': 'A long-form fixture record for the dossier and table projections.', 'status': 'done', 'priority': 'low'},
        )
        projects = add('projects',
            {'title': 'Process capability recovery · Chamber 5 North', 'summary': 'Coordinated synthetic work across chamber qualification, SPC review and operator runbooks.', 'status': 'active', 'owner': 'demo.process'},
            {'title': 'Reticle handling control refresh', 'summary': 'Planned follow-up with a deliberately short title.', 'status': 'planned', 'owner': 'demo.quality'},
            {'title': 'Decommission legacy recipe station', 'summary': 'Blocked pending a reviewed equipment and data-retention plan.', 'status': 'blocked', 'owner': 'demo.operations'},
        )
        racks = add('racks',
            {'name': 'FAB-A · Bay 04 · Rack R12', 'site': 'North process floor', 'row_name': 'Bay 04', 'rack_units': 42, 'power_capacity_kw': 18.0, 'pdu_a_capacity_kw': 12.0, 'pdu_b_capacity_kw': 12.0, 'weight_capacity_kg': 820.0, 'thermal_capacity_kw': 14.0, 'status': 'active'},
            {'name': 'Metrology lab rack M-2', 'site': 'Metrology laboratory', 'row_name': 'M-2', 'rack_units': 24, 'power_capacity_kw': 8.0, 'status': 'maintenance'},
        )
        equipment = add('equipment',
            {'name': 'CAP-7 chamber controller', 'kind': 'appliance', 'status': 'active', 'serial': 'SYN-CAP7-0042', 'power_kw': 2.8, 'notes': 'Controller for the synthetic Chamber 5 North process line.'},
            {'name': 'NW-24 dual-fabric leaf switch', 'kind': 'switch', 'status': 'active', 'serial': 'SYN-NW24-0081', 'power_kw': 1.1, 'notes': 'Front and rear ports have representative fiber links.'},
            {'name': 'Wafer history storage node', 'kind': 'storage', 'status': 'maintenance', 'serial': 'SYN-STOR-0017', 'power_kw': 4.2, 'notes': 'Local fixture storage node; no company data is present.'},
            {'name': 'TMP-04 chamber sensor bridge', 'kind': 'server', 'status': 'offline', 'serial': None, 'power_kw': 0.9, 'notes': None},
        )
        knowledge = add('knowledge_entries',
            {'title': 'Runbook · chamber drift triage and safe restart', 'entry_type': 'runbook', 'status': 'published', 'criticality': 'critical', 'owner': 'demo.process', 'review_state': 'verified', 'next_review_at': date(2026, 12, 15), 'content': 'Compare target and measured uniformity. Confirm interlocks before a restart.', 'procedures': {'checks': ['review control chart', 'verify interlock state', 'record recovery sample']}, 'tags': ['operations', 'recovery', 'safety', 'quality']},
            {'title': 'Network port map · legacy sensor bridge', 'entry_type': 'architecture_note', 'status': 'draft', 'criticality': 'standard', 'owner': 'demo.infrastructure', 'review_state': 'stale', 'next_review_at': None, 'content': None, 'procedures': {}, 'tags': ['network', 'hardware']},
        )
        investigations = add('investigations',
            {'title': 'Uniformity drift after PM-204 · chamber 5N', 'status': 'investigating', 'priority': 'critical', 'problem': 'Eight consecutive metrology samples drifted toward the upper process limit after preventive maintenance.', 'evidence': {'source': 'synthetic local SPC fixture', 'samples': 10, 'exception_count': 2}, 'hypotheses': {'gas_flow': 'Primary; flow setpoint changed during PM', 'sensor_offset': 'Unlikely; cross-check against bridge sensor'}, 'causes': {'candidate': 'MFC calibration drift'}, 'actions': {'owner': 'demo.process', 'next_review': '2026-09-24'}, 'findings': None, 'conclusion': None},
            {'title': 'Intermittent sensor bridge communication loss', 'status': 'validated', 'priority': 'high', 'problem': 'Short telemetry gaps aligned with a degraded uplink.', 'evidence': {'events': 3, 'port': 'Gi1/0/24'}, 'hypotheses': {'fiber': 'Connector contamination'}, 'causes': {'confirmed': 'Low receive power'}, 'actions': {'action': 'Clean and retest'}, 'findings': 'Optical level returned to expected range after cleaning.', 'conclusion': 'Monitor through the next scheduled run.'},
        )
        research = add('research',
            {'title': 'Can pressure compensation recover uniformity without recipe drift?', 'status': 'experimenting', 'phase': 'experiment', 'question': 'Can chamber pressure compensation restore capability while keeping downstream film thickness in control?', 'hypothesis': 'A bounded 0.4% pressure correction will recover within-subgroup variation.', 'methodology': 'Compare three synthetic subgroups with the existing released recipe and fixed metrology points.', 'experiments': {'groups': [{'name': 'baseline', 'n': 5}, {'name': 'offset +0.2%', 'n': 5}, {'name': 'offset +0.4%', 'n': 5}]}, 'evidence': {'fixture': FIXTURE_KIND, 'metric': 'uniformity_percent'}, 'analysis': 'The largest correction recovers the mean but increases range; review the complete chart before adoption.', 'findings': None, 'conclusion': None, 'recommendation': 'Continue with a narrower correction sweep.'},
            {'title': 'Recipe audit sampling plan', 'status': 'review', 'phase': 'analysis', 'question': 'Which review sample size provides useful warning before lot completion?', 'hypothesis': None, 'methodology': 'Compare a short and full-run sample window.', 'experiments': {'windows': [5, 10, 20]}, 'evidence': {'source': 'synthetic'}, 'analysis': None, 'findings': 'Short names and nullable values are included in this record.', 'conclusion': None, 'recommendation': None},
        )
        risks = add('risks',
            {'title': 'Unreviewed pressure correction may mask a failing sensor', 'status': 'mitigating', 'category': 'process', 'severity': 8, 'occurrence': 4, 'detection': 5, 'residual_severity': 6, 'residual_occurrence': 2, 'residual_detection': 3, 'effect': 'A compensation change could conceal the original sensor fault and shift downstream quality.', 'causes': {'primary': 'Sensor drift following maintenance'}, 'mitigations': {'guard': 'Independent metrology checkpoint'}, 'prevention': {'owner': 'demo.quality'}},
            {'title': 'Storage-node maintenance overlap', 'status': 'assessing', 'category': 'hardware', 'severity': 5, 'occurrence': 3, 'detection': 4, 'residual_severity': None, 'residual_occurrence': None, 'residual_detection': None, 'effect': None, 'causes': {}, 'mitigations': {}, 'prevention': {}},
        )
        plan_tasks = add('plan_tasks',
            {'title': 'Chamber capability recovery', 'status': 'in_progress', 'start_date': '2026-09-16', 'end_date': '2026-10-02', 'baseline_start': '2026-09-15', 'baseline_end': '2026-09-25', 'progress': 62, 'milestone': False, 'owner': 'demo.process', 'resource_group': 'Process engineering', 'effort_hours': 54, 'capacity_hours': 48, 'notes': 'Parent scope for the slipping measurement and qualification work.'},
            {'title': 'Repeat upper-limit metrology subgroup', 'status': 'blocked', 'start_date': '2026-09-18', 'end_date': '2026-09-30', 'baseline_start': '2026-09-17', 'baseline_end': '2026-09-22', 'progress': 38, 'milestone': False, 'owner': 'demo.quality', 'resource_group': 'Metrology', 'effort_hours': 28, 'capacity_hours': 20, 'notes': 'Blocked on maintenance review; baseline slip is visible in the schedule.'},
            {'title': 'Approve safe recipe window', 'status': 'ready', 'start_date': '2026-09-24', 'end_date': '2026-09-28', 'baseline_start': '2026-09-22', 'baseline_end': '2026-09-25', 'progress': 0, 'milestone': False, 'owner': 'demo.quality', 'resource_group': 'Process engineering', 'effort_hours': 24, 'capacity_hours': 24, 'notes': 'Depends on the repeated subgroup and review.'},
            {'title': 'Qualification sign-off', 'status': 'planned', 'start_date': '2026-10-03', 'end_date': '2026-10-03', 'baseline_start': '2026-09-29', 'baseline_end': '2026-09-29', 'progress': 0, 'milestone': True, 'owner': 'demo.operations', 'resource_group': 'Operations', 'effort_hours': 8, 'capacity_hours': 8, 'notes': 'Milestone for the qualification path.'},
        )
        diagram = add('diagram_documents',
            {'title': 'Chamber 5N process and telemetry flow', 'diagram_type': 'topology', 'status': 'active', 'nodes': {'sensor': {'label': 'Pressure bridge', 'type': 'source', 'x': 80, 'y': 150, 'entity': 'equipment', 'record_id': equipment[3].id}, 'controller': {'label': 'CAP-7 controller', 'type': 'process', 'x': 360, 'y': 150, 'entity': 'equipment', 'record_id': equipment[0].id}, 'service': {'label': 'Telemetry ingest', 'type': 'service', 'x': 650, 'y': 150, 'entity': 'software_services'}, 'spc': {'label': 'SPC review', 'type': 'analysis', 'x': 940, 'y': 150, 'entity': 'process_measurements'}}, 'edges': {'e-sensor-controller': {'source': 'sensor', 'target': 'controller', 'label': 'pressure samples', 'type': 'signal'}, 'e-controller-service': {'source': 'controller', 'target': 'service', 'label': 'metrics', 'type': 'telemetry'}, 'e-service-spc': {'source': 'service', 'target': 'spc', 'label': 'quality stream', 'type': 'data'}}, 'viewport': {'x': 0, 'y': 0, 'zoom': 0.9}, 'node_count': 4, 'edge_count': 3, 'notes': 'Synthetic local qualification graph with four linked stages.'},
        )
        measurements = []
        values = [99.4, 99.7, 100.1, 100.0, 100.3, 100.5, 101.0, 102.2, 104.7, 107.8]
        for index, value in enumerate(values):
            measurements.append(_record(session, actor, 'process_measurements', {
                'sample_label': f'CH5N uniformity subgroup {index+1:02}', 'process': 'Chamber 5 North · deposition', 'metric': 'Within-wafer uniformity',
                'value': value, 'unit': '%', 'sampled_at': f'2026-09-22T{6+index:02}:00:00Z', 'subgroup': f'Shift {"A" if index<5 else "B"}',
                'target': 100.0, 'lower_spec': 96.0, 'upper_spec': 106.0, 'lot': 'LOT-SYN-204',
                'category': 'alarm' if value>106 else 'measurement', 'context': {'fixture': FIXTURE_KIND, 'wafer_sample': index+1, 'instrument': 'MET-SYN-02'},
            }))
        records['process_measurements'] = measurements
        recipes = add('process_recipes',
            {'name': 'Uniformity recovery · Chamber 5N', 'version_name': '2.4.1', 'process': 'deposition', 'status': 'released', 'parameters': {'pressure_mTorr': 41.2, 'temperature_C': 385.0, 'gas_flow_sccm': 720}, 'limits': {'pressure_mTorr': [40.0, 42.0], 'temperature_C': [380.0, 390.0]}, 'approved_by': 'demo.quality', 'approved_at': '2026-09-18T14:00:00Z', 'notes': 'Synthetic local fixture approval; not company process authorization.'},
            {'name': 'Legacy reticle rinse', 'version_name': '1.8', 'process': 'wet_clean', 'status': 'deprecated', 'parameters': {'flow_l_min': 3.2}, 'limits': {}, 'approved_by': None, 'approved_at': None, 'notes': None},
        )
        lots = add('manufacturing_lots',
            {'lot_id': 'LOT-SYN-204', 'product': 'NX-14 sensor wafer', 'status': 'hold', 'current_step': 'metrology_review', 'priority': 'hot', 'quantity': 24, 'started_at': '2026-09-20T08:00:00Z', 'target_complete': '2026-09-25T18:00:00Z', 'route': {'steps': [{'id': 'load', 'name': 'Load and verify', 'status': 'completed'}, {'id': 'deposition', 'name': 'Chamber 5N deposition', 'status': 'completed', 'equipment': 'CAP-7 chamber controller'}, {'id': 'metrology', 'name': 'Metrology review', 'status': 'hold', 'equipment': 'TMP-04 chamber sensor bridge'}, {'id': 'release', 'name': 'Quality release', 'status': 'queued'}]}, 'hold_reason': 'Review upper-limit SPC samples before release.', 'owner': 'demo.quality'},
            {'lot_id': 'LOT-SYN-205', 'product': 'NX-14 sensor wafer', 'status': 'running', 'current_step': 'deposition', 'priority': 'normal', 'quantity': 18, 'started_at': '2026-09-22T07:30:00Z', 'target_complete': '2026-09-26T16:00:00Z', 'route': {'steps': [{'id': 'load', 'name': 'Load and verify', 'status': 'completed'}, {'id': 'deposition', 'name': 'Chamber 5N deposition', 'status': 'running', 'equipment': 'CAP-7 chamber controller'}, {'id': 'metrology', 'name': 'Metrology review', 'status': 'queued'}, {'id': 'release', 'name': 'Quality release', 'status': 'queued'}]}, 'hold_reason': None, 'owner': 'demo.operations'},
        )
        wafers = add('wafer_runs',
            {'wafer_id': 'WFR-SYN-204-03', 'lot_id': 'LOT-SYN-204', 'process_step': 'metrology_review', 'status': 'hold', 'die_rows': 12, 'die_cols': 12, 'bin_map': {'good_bins': ['GOOD', 'PASS', '1'], 'cells': [{'x': index % 12, 'y': index // 12, 'bin': 'PASS' if index < 139 else 'EDGE_REVIEW', **({'defect': 'edge site reinspection'} if index >= 139 else {})} for index in range(144)]}, 'completed_at': '2026-09-22T12:00:00Z', 'notes': 'Two edge sites require a second inspection.'},
            {'wafer_id': 'WFR-SYN-205-01', 'lot_id': 'LOT-SYN-205', 'process_step': 'deposition', 'status': 'processing', 'die_rows': 12, 'die_cols': 12, 'bin_map': {'good_bins': ['GOOD', 'PASS', '1'], 'cells': [{'x': index % 12, 'y': index // 12, 'bin': 'PENDING'} for index in range(144)]}, 'completed_at': None, 'notes': None},
        )
        states = add('equipment_states',
            {'label': 'CAP-7 deposition chamber', 'state': 'production', 'module': 'Chamber 5 North', 'started_at': '2026-09-22T06:00:00Z', 'ended_at': None, 'reason': 'Scheduled production run', 'alarm_code': None, 'context': {'shift': 'A', 'fixture': FIXTURE_KIND}},
            {'label': 'TMP-04 pressure bridge', 'state': 'unscheduled_down', 'module': 'Chamber 5 North', 'started_at': '2026-09-22T09:15:00Z', 'ended_at': None, 'reason': 'Intermittent uplink and sensor quality alarm', 'alarm_code': 'SYN-PRESS-17', 'context': {'severity': 'warning', 'review': 'open'}},
            {'label': 'Storage node N2', 'state': 'scheduled_down', 'module': 'Metrology history', 'started_at': '2026-09-22T18:00:00Z', 'ended_at': '2026-09-22T20:30:00Z', 'reason': 'Local fixture maintenance window', 'alarm_code': None, 'context': {}},
        )
        services = add('software_services',
            {'name': 'wafer-telemetry-api', 'status': 'healthy', 'tier': 'tier_1', 'owner': 'demo.platform', 'repository': 'https://example.invalid/wafer-telemetry', 'runtime': 'FastAPI · Python 3.11', 'environment': 'development', 'config': {'fixture': FIXTURE_KIND, 'region': 'local-lab'}, 'description': 'Synthetic event intake for the browser qualification fixture.'},
            {'name': 'process-control-ingest', 'status': 'degraded', 'tier': 'tier_0', 'owner': 'demo.platform', 'repository': 'https://example.invalid/process-ingest', 'runtime': 'Node · worker', 'environment': 'test', 'config': {'fixture': FIXTURE_KIND, 'retry_window_s': 90}, 'description': 'Degraded during the sample incident, then recovered after link cleanup.'},
            {'name': 'Engineering review portal', 'status': 'maintenance', 'tier': 'tier_2', 'owner': None, 'repository': None, 'runtime': None, 'environment': 'development', 'config': {}, 'description': None},
        )
        deliveries = add('delivery_runs',
            {'run_id': 'deploy-syn-2041', 'status': 'failed', 'environment': 'test', 'commit_sha': '7f5e11a1d28c', 'branch': 'feature/spc-recovery', 'started_at': '2026-09-22T08:00:00Z', 'completed_at': '2026-09-22T08:13:00Z', 'duration_minutes': 13, 'stages': {'build': 'passed', 'unit': 'passed', 'contract': 'failed'}, 'artifacts': {'report': 'synthetic://reports/2041'}, 'triggered_by': 'demo.engineer'},
            {'run_id': 'deploy-syn-2042', 'status': 'passed', 'environment': 'test', 'commit_sha': '6bd7c288a4e0', 'branch': 'feature/spc-recovery', 'started_at': '2026-09-22T10:00:00Z', 'completed_at': '2026-09-22T10:09:00Z', 'duration_minutes': 9, 'stages': {'build': 'passed', 'unit': 'passed', 'contract': 'passed'}, 'artifacts': {'report': 'synthetic://reports/2042'}, 'triggered_by': 'demo.engineer'},
            {'run_id': 'deploy-syn-2043', 'status': 'running', 'environment': 'development', 'commit_sha': None, 'branch': 'main', 'started_at': '2026-09-23T08:00:00Z', 'completed_at': None, 'duration_minutes': 0, 'stages': {'build': 'running'}, 'artifacts': {}, 'triggered_by': None},
        )
        events = add('observability_events',
            {'event_id': 'evt-syn-5001', 'signal': 'metric', 'severity': 'warning', 'timestamp': '2026-09-22T09:14:00Z', 'duration_ms': 820.4, 'trace_id': 'trace-syn-09ab', 'span_id': 'span-syn-a100', 'parent_span_id': None, 'operation': 'telemetry.ingest', 'message': 'P95 sample latency crossed the local warning threshold.', 'attributes': {'service': 'process-control-ingest', 'threshold_ms': 750, 'fixture': FIXTURE_KIND}},
            {'event_id': 'evt-syn-5002', 'signal': 'log', 'severity': 'error', 'timestamp': '2026-09-22T09:15:00Z', 'duration_ms': None, 'trace_id': 'trace-syn-09ac', 'span_id': 'span-syn-a101', 'parent_span_id': 'span-syn-a100', 'operation': 'sensor.bridge.read', 'message': 'Pressure bridge sample failed validation; value retained for investigation.', 'attributes': {'sensor': 'TMP-04', 'quality': 'suspect'}},
            {'event_id': 'evt-syn-5003', 'signal': 'trace', 'severity': 'info', 'timestamp': '2026-09-22T09:41:00Z', 'duration_ms': 184.0, 'trace_id': 'trace-syn-09b0', 'span_id': 'span-syn-b001', 'parent_span_id': None, 'operation': 'telemetry.retry', 'message': 'Retry succeeded after the local link cleanup.', 'attributes': {'attempt': 2, 'recovered': True}},
            {'event_id': 'evt-syn-5004', 'signal': 'metric', 'severity': 'info', 'timestamp': '2026-09-23T07:30:00Z', 'duration_ms': 204.2, 'trace_id': None, 'span_id': None, 'parent_span_id': None, 'operation': 'telemetry.ingest', 'message': 'P95 latency returned within the target window.', 'attributes': {'p95_ms': 204.2}},
            {'event_id': 'evt-syn-5005', 'signal': 'log', 'severity': 'debug', 'timestamp': '2026-09-23T07:42:00Z', 'duration_ms': None, 'trace_id': None, 'span_id': None, 'parent_span_id': None, 'operation': None, 'message': None, 'attributes': {}},
        )
        incidents = add('incidents',
            {'incident_number': 'INC-SYN-204', 'title': 'Pressure bridge drift interrupted Chamber 5N qualification', 'status': 'monitoring', 'severity': 'sev_2', 'started_at': '2026-09-22T09:15:00Z', 'resolved_at': None, 'duration_minutes': 103, 'commander': 'demo.incident', 'impact': 'One local synthetic lot is held for metrology review; no external process or customer impact is represented.', 'timeline': {'events': [{'at': '2026-09-22T09:15:00Z', 'kind': 'detected', 'message': 'Validation failed on bridge sample.', 'actor': 'demo.monitor'}, {'at': '2026-09-22T09:34:00Z', 'kind': 'mitigation', 'message': 'Route switched to redundant uplink.', 'actor': 'demo.operations'}, {'at': '2026-09-22T09:41:00Z', 'kind': 'recovery', 'message': 'Retry succeeded; monitoring continues.', 'actor': 'demo.incident'}]}, 'actions': {'next': 'Complete one verification sample', 'owner': 'demo.quality', 'due': '2026-09-24'}},
            {'incident_number': 'INC-SYN-198', 'title': 'Short telemetry retry delay', 'status': 'resolved', 'severity': 'sev_3', 'started_at': '2026-09-18T11:00:00Z', 'resolved_at': '2026-09-18T11:22:00Z', 'duration_minutes': 22, 'commander': None, 'impact': 'No records were dropped in this synthetic incident.', 'timeline': {'events': [{'at': '2026-09-18T11:22:00Z', 'kind': 'resolved', 'message': 'Retry queue drained.'}]}, 'actions': {}},
        )
        objectives = add('service_objectives',
            {'name': 'Telemetry ingest availability · 30 days', 'window_days': 30, 'target_percent': 99.9, 'current_percent': 99.76, 'error_budget_remaining': 18.0, 'burn_rate': 2.4, 'status': 'warning', 'notes': 'Synthetic local objective linked to the sample service and recovery event.'},
            {'name': 'Review portal request success', 'window_days': 7, 'target_percent': 99.5, 'current_percent': 99.92, 'error_budget_remaining': 82.0, 'burn_rate': 0.2, 'status': 'healthy', 'notes': None},
        )

        for item, start, size, face in [(equipment[0], 10, 4, 'front'), (equipment[1], 26, 1, 'front'), (equipment[2], 8, 4, 'rear'), (equipment[3], 4, 1, 'front')]:
            rack = racks[1] if item is equipment[2] else racks[0]
            _link(session, actor, entities, 'rack_equipment', rack, item, {'start_unit': start, 'size_u': size, 'face': face})
        for source, target, local, remote, cable, medium in [
            (equipment[0], equipment[1], 'eth0', 'Gi1/0/11', 'CAB-SYN-1001', 'fiber'),
            (equipment[0], equipment[2], 'eth1', 'FC0', 'CAB-SYN-1002', 'fiber'),
            (equipment[1], equipment[2], 'Gi1/0/24', 'FC1', 'CAB-SYN-1003', 'fiber'),
            (equipment[1], equipment[3], 'Gi1/0/18', 'eth0', 'CAB-SYN-1004', 'copper'),
        ]:
            _link(session, actor, entities, 'equipment_connections', source, target, {'source_port': local, 'target_port': remote, 'cable_id': cable, 'medium': medium, 'protocol': 'ethernet', 'status': 'connected', 'length_m': 12.5, 'label': 'Fixture link'})

        _link(session, actor, entities, 'project_work_items', projects[0], work_items[0])
        _link(session, actor, entities, 'project_work_items', projects[0], work_items[1])
        for task in plan_tasks:
            _link(session, actor, entities, 'project_plan_tasks', projects[0], task)
        _link(session, actor, entities, 'plan_task_parent', plan_tasks[0], plan_tasks[1])
        _link(session, actor, entities, 'plan_task_parent', plan_tasks[0], plan_tasks[2])
        _link(session, actor, entities, 'plan_task_parent', plan_tasks[0], plan_tasks[3])
        _link(session, actor, entities, 'plan_task_dependencies', plan_tasks[2], plan_tasks[1])
        _link(session, actor, entities, 'plan_task_dependencies', plan_tasks[3], plan_tasks[2])
        _link(session, actor, entities, 'knowledge_equipment', knowledge[0], equipment[0])
        _link(session, actor, entities, 'knowledge_work_items', knowledge[0], work_items[0])
        _link(session, actor, entities, 'investigation_equipment', investigations[0], equipment[3])
        _link(session, actor, entities, 'investigation_work_items', investigations[0], work_items[0])
        _link(session, actor, entities, 'investigation_knowledge', investigations[0], knowledge[0])
        _link(session, actor, entities, 'risk_investigation', risks[0], investigations[0])
        _link(session, actor, entities, 'risk_equipment', risks[0], equipment[0])
        _link(session, actor, entities, 'risk_knowledge', risks[0], knowledge[0])
        _link(session, actor, entities, 'risk_work_items', risks[0], work_items[0])
        _link(session, actor, entities, 'research_equipment', research[0], equipment[0])
        _link(session, actor, entities, 'research_knowledge', research[0], knowledge[0])
        _link(session, actor, entities, 'research_risks', research[0], risks[0])
        _link(session, actor, entities, 'research_work_items', research[0], work_items[0])
        for measurement in measurements:
            _link(session, actor, entities, 'measurement_equipment', measurement, equipment[0])
        for wafer, lot, machine in [(wafers[0], lots[0], equipment[0]), (wafers[1], lots[1], equipment[0])]:
            _link(session, actor, entities, 'wafer_lot', wafer, lot)
            _link(session, actor, entities, 'wafer_equipment', wafer, machine)
            _link(session, actor, entities, 'wafer_recipe', wafer, recipes[0])
        for state, machine in [(states[0], equipment[0]), (states[1], equipment[3]), (states[2], equipment[2])]:
            _link(session, actor, entities, 'equipment_state_equipment', state, machine)
        _link(session, actor, entities, 'delivery_service', deliveries[0], services[1])
        _link(session, actor, entities, 'delivery_service', deliveries[1], services[1])
        _link(session, actor, entities, 'delivery_service', deliveries[2], services[0])
        for index, event in enumerate(events):
            _link(session, actor, entities, 'observability_service', event, services[1] if index<3 else services[0])
        _link(session, actor, entities, 'incident_service', incidents[0], services[1])
        _link(session, actor, entities, 'incident_service', incidents[1], services[0])
        _link(session, actor, entities, 'incident_knowledge', incidents[0], knowledge[0])
        _link(session, actor, entities, 'incident_work_items', incidents[0], work_items[1])
        _link(session, actor, entities, 'slo_service', objectives[0], services[1])
        _link(session, actor, entities, 'slo_service', objectives[1], services[0])
        _link(session, actor, entities, 'service_dependencies', services[1], services[0])
        _link(session, actor, entities, 'service_projects', services[1], projects[0])
        _link(session, actor, entities, 'service_projects', services[0], projects[1])

        set_preference(session, actor, 'engineering.review', True, None)
        create_notification(session, actor, NotificationCreate(user_id=user_id, kind='engineering.review', title='Review SPC upper-limit samples', body='The synthetic Chamber 5 North series includes two exception values and a linked investigation.', data={'fixture': FIXTURE_KIND, 'workspace': 'process_measurements'}))
        create_notification(session, actor, NotificationCreate(user_id=user_id, kind='delivery.recovery', title='Telemetry retry recovered', body='A local retry event follows the sample delivery failure.', data={'fixture': FIXTURE_KIND, 'workspace': 'observability_events'}))

        counts = {workspace: len(rows) for workspace, rows in sorted(records.items())}
        counts['system'] = 2
        counts = dict(sorted(counts.items()))
        relationship_count = session.scalar(select(func.count()).select_from(EntityRelationship)) or 0
        result = {
            'fixture': FIXTURE_KIND,
            'disposable': True,
            'production_evidence': False,
            'record_counts': counts,
            'relationship_count': relationship_count,
            'coverage': sorted(counts),
        }
        session.commit()
        return result
