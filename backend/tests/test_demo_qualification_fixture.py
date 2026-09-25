from sqlalchemy import select

from app.features.plan_tasks.models import PlanTask
from app.features.process_measurements.models import ProcessMeasurement
from app.features.racks.models import Rack
from app.platform.models import EntityRelationship, Notification
from app.tooling.demo_qualification import FIXTURE_KIND, seed_demo_qualification


def test_disposable_demo_seed_populates_linked_workspace_families(env):
    summary = seed_demo_qualification(env['db'], env['tenant'], 'alice')
    assert summary == {
        'fixture': FIXTURE_KIND,
        'disposable': True,
        'production_evidence': False,
        'record_counts': {
            'delivery_runs': 3, 'diagram_documents': 1, 'equipment': 4,
            'equipment_states': 3, 'incidents': 2, 'investigations': 2,
            'knowledge_entries': 2, 'manufacturing_lots': 2, 'observability_events': 5,
            'plan_tasks': 4, 'process_measurements': 10, 'process_recipes': 2,
            'projects': 3, 'racks': 2, 'research': 2, 'risks': 2,
            'service_objectives': 2, 'software_services': 3, 'system': 2,
            'wafer_runs': 2, 'work_items': 3,
        },
        'relationship_count': 68,
        'coverage': [
            'delivery_runs', 'diagram_documents', 'equipment', 'equipment_states',
            'incidents', 'investigations', 'knowledge_entries', 'manufacturing_lots',
            'observability_events', 'plan_tasks', 'process_measurements', 'process_recipes',
            'projects', 'racks', 'research', 'risks', 'service_objectives',
            'software_services', 'system', 'wafer_runs', 'work_items',
        ],
    }
    with env['db'].session(env['tenant']) as session:
        racks = session.scalars(select(Rack).order_by(Rack.name)).all()
        assert [rack.status for rack in racks] == ['active', 'maintenance']
        tasks = session.scalars(select(PlanTask).order_by(PlanTask.title)).all()
        assert any(task.status == 'blocked' and task.end_date > task.baseline_end for task in tasks)
        measurements = session.scalars(select(ProcessMeasurement)).all()
        assert len(measurements) == 10
        assert max(value.value for value in measurements) == 107.8
        relationships = session.scalars(select(EntityRelationship)).all()
        assert sum(row.definition_key == 'rack_equipment' for row in relationships) == 4
        assert sum(row.definition_key == 'equipment_connections' for row in relationships) == 4
        assert all(row.metadata_json.get('cable_id') for row in relationships if row.definition_key == 'equipment_connections')
        assert sum(row.definition_key == 'plan_task_dependencies' for row in relationships) == 2
        notifications = session.scalars(select(Notification)).all()
        assert len(notifications) == 2
        assert all(item.user_id == 'alice' and item.data['fixture'] == FIXTURE_KIND for item in notifications)
