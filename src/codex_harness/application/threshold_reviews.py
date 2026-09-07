"""Leased, ordered assessment of calculated threshold evidence; no apply authority."""
from codex_harness.domain.model import digest, envelope, require, utcnow


class ThresholdReviews:
    def __init__(self, workflow, artifacts):
        self.workflow, self.artifacts = workflow, artifacts
        self.store, self.org = workflow.store, workflow.org

    def _row(self, tx, row_id):
        row = tx.get('threshold_proposals', row_id)
        require(row is not None and row['activation_ready'] is False
                and 'native_task_success_and_release_review_required' in row['activation_blockers'],
                'Calculated threshold record required')
        document = self.artifacts.document(row['evidence_ref'])
        require(document['project_key'] == row['project_key']
                and row['proposal'] in document['proposals'], 'Threshold artifact binding changed')
        require(row['run_id'] == digest([row['project_key'], row['evidence_ref']])
                and row['id'] == digest([row['run_id'], row['proposal']['id']]), 'Threshold record identity changed')
        return row

    def request(self, row_id):
        self.org.actor('lead:improvement', 'lead')
        self.org.actor('conductor', 'conductor')
        with self.store.transaction() as tx:
            row = self._row(tx, row_id)
            binding = digest(row)
            identity = digest(['threshold-assessment-v1', binding])
            old = tx.get('threshold_review_requests', identity)
            if old:
                return old
            request = {'id': identity, 'row_id': row_id, 'binding': binding,
                'status': 'awaiting_lead', 'reviews': [], 'activation_ready': False,
                'scope': 'assessment_only_no_dispatch_or_activation', 'created_at': utcnow()}
            tx.put('threshold_review_requests', identity, request)
            self._queue(tx, request, 'lead:improvement')
            return request

    def _queue(self, tx, request, actor):
        key = digest([request['id'], actor])
        sender = 'conductor' if actor == 'lead:improvement' else 'lead:improvement'
        message = envelope('task.assign' if actor == 'lead:improvement' else 'review.result',
            sender, actor, 'assess_threshold', {'request_id': request['id'],
                'binding': request['binding']}, request['id'])
        self.org.authorize(message)
        tx.put('decisions_pending', key, {'id': key, 'actor': actor, 'phase': 'threshold_review',
            'input': {'request_id': request['id']}, 'message': message, 'status': 'pending', 'attempt': 0})

    def _prepare(self, tx, lease):
        current = self.workflow._owned(tx, lease)
        require(current['phase'] == 'threshold_review', 'Wrong threshold decision phase')
        request = tx.get('threshold_review_requests', current['input']['request_id'])
        require(request is not None, 'Threshold review request missing')
        expected = {'awaiting_lead': 'lead:improvement', 'awaiting_conductor': 'conductor'}.get(request['status'])
        require(current['actor'] == expected, 'Threshold review order changed')
        row = self._row(tx, request['row_id'])
        require(digest(row) == request['binding'], 'Threshold review input changed')
        return current, request, {'request_id': request['id'], 'binding': request['binding'],
            'record': row, 'prior_reviews': request['reviews'], 'scope': request['scope']}

    def prepare(self, lease):
        with self.store.transaction() as tx:
            return self._prepare(tx, lease)[2]

    def complete(self, lease, bundle, result):
        require(type(result.get('accepted')) is bool and isinstance(result.get('reason'), str),
                'Invalid threshold assessment')
        self.artifacts.inspect(result['execution_ref'])
        blocked = bool(result.get('blocked') or result.get('inspection_blocked'))
        require(not blocked or not result['accepted'], 'Blocked threshold review cannot accept')
        with self.store.transaction() as tx:
            current, request, expected = self._prepare(tx, lease)
            # INV-THRESHOLD-REVIEW-001: lease, exact input and ordered review commit together.
            require(bundle == expected, 'Threshold review basis changed')
            request['reviews'].append({'actor': current['actor'], 'result': result,
                'decision_id': current['id'], 'generation': current['generation'], 'at': utcnow()})
            request['status'] = ('blocked' if blocked else 'rejected' if not result['accepted'] else
                'awaiting_conductor' if current['actor'] == 'lead:improvement' else 'assessed')
            current.update(status='blocked' if blocked else 'succeeded', result=result, completed_at=utcnow())
            tx.put('decisions_pending', current['id'], current)
            tx.put('threshold_review_requests', request['id'], request)
            if request['status'] == 'awaiting_conductor':
                self._queue(tx, request, 'conductor')
            return current
