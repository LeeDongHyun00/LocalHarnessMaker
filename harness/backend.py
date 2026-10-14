import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, ProxyHandler, build_opener

from .results import SubmissionError


class API:
    def __init__(self, service):
        self.service = service
        self.opener = build_opener(ProxyHandler({}))

    def call(self, method, path, body=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        request = Request(self.service.url + path, data=data, method=method,
                          headers={'Content-Type': 'application/json'})
        try:
            response = self.opener.open(request, timeout=3)
        except HTTPError as error:
            response = error
        except (URLError, TimeoutError) as error:
            raise SubmissionError(f"HTTP service unavailable: {error}") from error
        with response:
            try:
                value = json.loads(response.read())
            except (ValueError, UnicodeError) as error:
                raise SubmissionError('Response must contain valid JSON') from error
            return response.status, value

    def ok(self, method, path, body=None, status=200):
        actual, value = self.call(method, path, body)
        assert actual == status, f'{method} {path}: expected {status}, got {actual}'
        return value

    def equipment(self, name='커터'):
        value = self.ok('POST', '/equipment', {'name': name}, 201)
        assert isinstance(value, dict) and isinstance(value.get('id'), str) and value['id']
        assert value.get('name') == name.strip()
        return value

    def reservation(self, equipment, start='09:00', end='10:00', borrower='민수'):
        body = {'equipment_id': equipment['id'], 'borrower': borrower,
                'start_at': f'2026-10-20T{start}:00Z', 'end_at': f'2026-10-20T{end}:00Z'}
        value = self.ok('POST', '/reservations', body, 201)
        assert isinstance(value, dict) and isinstance(value.get('id'), str) and value['id']
        assert all(value.get(k) == v for k, v in body.items() if k != 'borrower')
        assert value.get('borrower') == borrower.strip() and value.get('status') == 'active'
        return value

    def cancel(self, reservation):
        value = self.ok('POST', f"/reservations/{quote(reservation['id'], safe='')}/cancel")
        assert isinstance(value, dict) and value.get('id') == reservation['id']
        assert value.get('status') == 'cancelled'
        return value

    def error(self, method, path, status, code, body=None, raw=None):
        actual, value = self.call(method, path, body, raw)
        assert actual == status, f'{method} {path}: expected {status}, got {actual}'
        assert isinstance(value, dict) and isinstance(value.get('error'), dict), 'Missing error object'
        error = value['error']
        assert error.get('code') == code, f"Expected {code}, got {error.get('code')}"
        assert isinstance(error.get('message'), str) and error['message'].strip(), 'Missing error explanation'


def cases():
    def empty(service):
        assert API(service).ok('GET', '/equipment') == []

    def registration(service):
        api = API(service)
        a, b = api.equipment(' 커터 '), api.equipment(' 커터 ')
        assert a['id'] != b['id']
        rows = api.ok('GET', '/equipment')
        assert isinstance(rows, list) and len(rows) == 2
        assert all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in rows)
        assert {r['id'] for r in rows} == {a['id'], b['id']} and all(r['name'] == '커터' for r in rows)

    def create(service):
        api = API(service)
        api.reservation(api.equipment(), borrower=' 민수 ')

    def overlap(service):
        api = API(service)
        e = api.equipment()
        r = api.reservation(e)
        body = {'equipment_id': e['id'], 'borrower': '지연',
                'start_at': '2026-10-20T09:30:00Z', 'end_at': '2026-10-20T10:30:00Z'}
        api.error('POST', '/reservations', 409, 'conflict', body)
        assert api.ok('GET', '/reservations') == [r]

    def adjacent(service):
        api = API(service)
        e = api.equipment()
        a = api.reservation(e)
        b = api.reservation(e, '10:00', '11:00')
        assert a['id'] != b['id']

    def different_equipment(service):
        api = API(service)
        e1, e2 = api.equipment(), api.equipment('레이저')
        a, b = api.reservation(e1), api.reservation(e2)
        assert a['id'] != b['id']

    def reuse_cancelled(service):
        api = API(service)
        e = api.equipment()
        r = api.reservation(e)
        api.cancel(r)
        new = api.reservation(e)
        assert new['id'] != r['id']

    def repeat_cancel(service):
        api = API(service)
        r = api.reservation(api.equipment())
        cancelled = api.cancel(r)
        assert api.cancel(r) == cancelled
        assert api.ok('GET', '/reservations') == [cancelled]

    def query_setup(service):
        api = API(service)
        e1, e2 = api.equipment(), api.equipment('다른 장비')
        late = api.reservation(e1, '11:00', '12:00')
        cancelled = api.cancel(api.reservation(e1))
        early = api.reservation(e2, '08:00', '09:00')
        return api, e1, e2, late, cancelled, early

    def combined(service):
        api, e1, e2, late, cancelled, early = query_setup(service)
        def filtered(**params):
            return api.ok('GET', '/reservations?' + urlencode(params))
        assert filtered(equipment_id=e1['id'], status='active') == [late]
        assert filtered(equipment_id=e1['id']) == [cancelled, late]
        assert filtered(status='cancelled') == [cancelled]
        assert filtered(status='active') == [early, late]

    def sorted_list(service):
        api, e1, e2, late, cancelled, early = query_setup(service)
        assert api.ok('GET', '/reservations') == [early, cancelled, late]
        tied = api.reservation(api.equipment('세 번째'), '08:00', '09:00')
        assert api.ok('GET', '/reservations') == [early, tied, cancelled, late]

    def unknown_filter(service):
        assert API(service).ok('GET', '/reservations?equipment_id=unknown') == []

    def invalid_reservations(service):
        api = API(service)
        e = api.equipment()
        existing = api.reservation(e, '12:00', '13:00')
        valid = {'equipment_id': e['id'], 'borrower': '민수',
                 'start_at': '2026-10-20T09:00:00Z', 'end_at': '2026-10-20T10:00:00Z'}
        for changes in ({'borrower': '   '}, {'end_at': valid['start_at']},
                        {'end_at': '2026-10-20T08:00:00Z'}, {'start_at': '2026-02-30T09:00:00Z'},
                        {'borrower': 1}, {'equipment_id': 1}, {'end_at': None}):
            api.error('POST', '/reservations', 400, 'invalid_input', valid | changes)
        for field in valid:
            api.error('POST', '/reservations', 400, 'invalid_input', {k: v for k, v in valid.items() if k != field})
        assert api.ok('GET', '/reservations') == [existing]
        assert api.ok('GET', '/equipment') == [e]

    def invalid_requests(service):
        api = API(service)
        e = api.equipment()
        r = api.reservation(e)
        api.error('POST', '/equipment', 400, 'invalid_input', raw=b'{')
        for body in ({}, {'name': 1}, {'name': '   '}, [], {'name': None}):
            api.error('POST', '/equipment', 400, 'invalid_input', body)
        api.error('GET', '/reservations?status=done', 400, 'invalid_input')
        assert api.ok('GET', '/equipment') == [e]
        assert api.ok('GET', '/reservations') == [r]

    def not_found(service):
        api = API(service)
        api.error('POST', '/reservations', 404, 'not_found',
                  {'equipment_id': 'unknown', 'borrower': '민수',
                   'start_at': '2026-10-20T09:00:00Z', 'end_at': '2026-10-20T10:00:00Z'})
        api.error('POST', '/reservations/unknown/cancel', 404, 'not_found')
        assert api.ok('GET', '/equipment') == [] and api.ok('GET', '/reservations') == []

    def persistence(service):
        api = API(service)
        e = api.equipment()
        active = api.reservation(e)
        cancelled = api.cancel(api.reservation(e, '11:00', '12:00'))
        service.restart()
        assert api.ok('GET', '/equipment') == [e]
        assert api.ok('GET', '/reservations') == [active, cancelled]

    return dict(zip(['B1.1', 'B1.2', 'B2.1', 'B3.1', 'B3.2', 'B3.3', 'B4.1', 'B4.2',
                     'B5.1', 'B5.2', 'B5.3', 'B6.1', 'B6.2', 'B6.3', 'B7.1'],
                    [empty, registration, create, overlap, adjacent, different_equipment,
                     reuse_cancelled, repeat_cancel, combined, sorted_list, unknown_filter,
                     invalid_reservations, invalid_requests, not_found, persistence]))
