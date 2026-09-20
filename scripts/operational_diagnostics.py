"""Sanitized operational qualification diagnostics shared by operator tooling."""
from __future__ import annotations

from typing import Any


def safe_diagnostics_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Return only stable, non-secret metadata from an aggregate report."""
    return {
        'report_type': 'safe-operational-reliability-diagnostics',
        'candidate_version': report.get('candidate_version'),
        'candidate_head': report.get('candidate_head'),
        'executable_source_commit': report.get('executable_source_commit'),
        'source_digest': report.get('source_digest'),
        'contract_id': report.get('contract_id'),
        'contract_revision': report.get('contract_revision'),
        'contract_sha256': report.get('contract_sha256'),
        'repository_operations_status': report.get('repository_operations_status'),
        'company_operations_status': report.get('company_operations_status'),
        'production_ready': False,
        'scenario_statuses': [
            {
                'id': row.get('id'),
                'status': row.get('status'),
                'reason_code': row.get('reason_code'),
            }
            for row in report.get('scenario_results', [])
            if isinstance(row, dict)
        ],
        'external_blockers': [
            {
                'id': row.get('id'),
                'status': row.get('status'),
                'reason_code': row.get('reason_code'),
            }
            for row in report.get('external_blockers', [])
            if isinstance(row, dict)
        ],
    }
