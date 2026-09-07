"""Bind routed skill observations and atomic body advisories to Executor context."""
from dataclasses import replace

from codex_harness.application.skill_history import SkillHistory
from codex_harness.domain.model import canonical, digest
from codex_harness.domain.skill_history import TOP_MATCHES


def prepare_history(store, artifacts, project, agent, task, objective, selection, items):
    if not selection.get('manifest_ref'):
        return items, None
    manifest = artifacts.document(selection['manifest_ref'])
    records = [r for r in manifest['skills'] if 'score' in r and r['tier'] != 'unmatched']
    if not records:
        return items, None
    project_key = digest(project)
    event_id = digest([agent, task, objective, selection['manifest_ref']])
    history = SkillHistory(store)
    assessment = history.snapshot(project_key, records, event_id)
    receipt = artifacts.put(canonical({'project': project_key, 'assessment': assessment,
                                      'current_event_excluded': event_id}), 'skill-history-assessment')
    selection['history'] = {'ref': receipt['ref'],
                           'file': str(artifacts.root / (receipt['ref'][7:] + '.txt'))}
    flagged = {(r['path'], r['content_ref']) for r in assessment if r['candidate']}
    full = {r['path'] for r in records if r['tier'] == 'full'}
    annotated = []
    for item in items:
        path = item.id.removeprefix('project-skill:')
        if path in full and (path, item.source_ref) in flagged:
            # INV-SKILL-HISTORY-001: body and advice are admitted/omitted atomically.
            item = replace(item, body=canonical({'skill_body': item.body,
                'historical_advisory': 'This skill often matched on weak signals. Review its guidance '
                    'critically; repeated false positives warrant narrowing its trigger metadata.',
                'history_ref': receipt['ref']}))
        annotated.append(item)
    top = sorted(records, key=lambda r: (-r['score'], r['path']))[:TOP_MATCHES]
    event = {'id': event_id, 'manifest_ref': selection['manifest_ref'],
             'top': [{key: r[key] for key in ('path', 'content_ref', 'score', 'base_score')}
                     for r in top], 'kind': 'compiled_skill_selection'}
    return annotated, (history, project_key, event)
