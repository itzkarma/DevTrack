"""API views for DevTrack.

Endpoints are plain function views returning JsonResponse. POST handlers build
the appropriate OOP class, call validate() and to_dict(), then persist to JSON.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from issues.models import Reporter, Issue, CriticalIssue, LowPriorityIssue
from issues import storage


def _parse_body(request):
    """Parse a JSON request body, returning {} if empty/invalid."""
    if not request.body:
        return {}
    return json.loads(request.body)


@csrf_exempt
def reporters(request):
    """POST -> create a reporter. GET -> list all, or one by ?id=."""
    if request.method == 'POST':
        return create_reporter(request)
    if request.method == 'GET':
        return get_reporters(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def create_reporter(request):
    """Validate and persist a new reporter; return 201 with the record."""
    try:
        data = _parse_body(request)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    records = storage.read_reporters()
    reporter = Reporter(
        entity_id=data.get('id') or storage.next_id(records),
        name=data.get('name', ''),
        email=data.get('email', ''),
        team=data.get('team', ''),
    )

    try:
        reporter.validate()
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    record = reporter.to_dict()
    records.append(record)
    storage.write_reporters(records)
    return JsonResponse(record, status=201)


def get_reporters(request):
    """Return one reporter by ?id= or the full list."""
    records = storage.read_reporters()

    reporter_id = request.GET.get('id')
    if reporter_id is not None:
        for record in records:
            if record['id'] == int(reporter_id):
                return JsonResponse(record, status=200)
        return JsonResponse({'error': 'Reporter not found'}, status=404)

    return JsonResponse(records, safe=False, status=200)


@csrf_exempt
def issues(request):
    """POST -> create an issue. GET -> list all, or filter by ?id= / ?status=."""
    if request.method == 'POST':
        return create_issue(request)
    if request.method == 'GET':
        return get_issues(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def create_issue(request):
    """Validate and persist a new issue; return 201 with record and message."""
    try:
        data = _parse_body(request)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    records = storage.read_issues()
    priority = data.get('priority')

    # Pick the subclass based on priority (medium/high use base Issue).
    if priority == 'critical':
        issue_cls = CriticalIssue
    elif priority == 'low':
        issue_cls = LowPriorityIssue
    else:
        issue_cls = Issue

    issue = issue_cls(
        entity_id=data.get('id') or storage.next_id(records),
        title=data.get('title', ''),
        description=data.get('description', ''),
        status=data.get('status', ''),
        priority=priority,
        reporter_id=data.get('reporter_id'),
    )

    try:
        issue.validate()
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    record = issue.to_dict()
    records.append(record)
    storage.write_issues(records)

    # Response echoes the stored record plus the polymorphic describe() message.
    response_data = dict(record)
    response_data['message'] = issue.describe()
    return JsonResponse(response_data, status=201)


def get_issues(request):
    """Return one issue by ?id=, filter by ?status=, or the full list."""
    records = storage.read_issues()

    issue_id = request.GET.get('id')
    if issue_id is not None:
        for record in records:
            if record['id'] == int(issue_id):
                return JsonResponse(record, status=200)
        return JsonResponse({'error': 'Issue not found'}, status=404)

    status = request.GET.get('status')
    if status is not None:
        filtered = [r for r in records if r['status'] == status]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(records, safe=False, status=200)
