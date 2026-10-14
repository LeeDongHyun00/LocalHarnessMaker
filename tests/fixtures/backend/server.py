"""Small HTTP reference and intentional mutants. Never a performance experiment result."""
import json
import os
import re
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FAULT = os.environ.get('FIXTURE_FAULT', '')
FILE = Path('data.json')
state = json.loads(FILE.read_text()) if FILE.exists() and FAULT != 'no_persistence' else {'equipment': [], 'reservations': []}


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError('UTC timestamp required')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error(self, status, code):
        self.send(status, {'error': {'code': code, 'message': code}})

    def save(self):
        FILE.write_text(json.dumps(state))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/equipment':
            return self.send(200, state['equipment'])
        if parsed.path != '/reservations':
            return self.error(404, 'not_found')
        query = parse_qs(parsed.query, keep_blank_values=True)
        status = query.get('status', [None])[0]
        equipment = query.get('equipment_id', [None])[0]
        if status is not None and status not in ('active', 'cancelled'):
            return self.error(400, 'invalid_input')
        rows = [r for r in state['reservations'] if
                ((equipment is None or r['equipment_id'] == equipment) and
                 (status is None or r['status'] == status))]
        if FAULT == 'filter_or' and equipment and status:
            rows = [r for r in state['reservations'] if r['equipment_id'] == equipment or r['status'] == status]
        if FAULT != 'unsorted':
            rows = sorted(rows, key=lambda r: r['start_at'])
        self.send(200, rows)

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith('/reservations/') and path.endswith('/cancel'):
            identifier = path.split('/')[2]
            row = next((r for r in state['reservations'] if r['id'] == identifier), None)
            if row is None:
                return self.error(404, 'not_found')
            row['status'] = 'cancelled'
            if FAULT == 'delete_cancelled':
                state['reservations'].remove(row)
            self.save()
            return self.send(200, row)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            if not isinstance(body, dict):
                raise ValueError('Object required')
            if path == '/equipment':
                name = body.get('name')
                if not isinstance(name, str) or not name.strip():
                    raise ValueError('Name required')
                row = {'id': uuid.uuid4().hex, 'name': name.strip()}
                state['equipment'].append(row)
            elif path == '/reservations':
                for key in ('equipment_id', 'borrower', 'start_at', 'end_at'):
                    if not isinstance(body.get(key), str) or not body[key].strip():
                        raise ValueError('Required string')
                start, end = timestamp(body['start_at']), timestamp(body['end_at'])
                if end <= start:
                    raise ValueError('End must follow start')
                if not any(e['id'] == body['equipment_id'] for e in state['equipment']):
                    return self.error(404, 'not_found')
                for existing in state['reservations']:
                    same = existing['equipment_id'] == body['equipment_id'] or FAULT == 'cross_equipment'
                    active = existing['status'] == 'active' or FAULT == 'cancel_blocks'
                    a, b = timestamp(existing['start_at']), timestamp(existing['end_at'])
                    overlap = start <= b and end >= a if FAULT == 'closed_boundary' else start < b and end > a
                    if same and active and overlap:
                        return self.error(409, 'conflict')
                row = {k: body[k] for k in ('equipment_id', 'borrower', 'start_at', 'end_at')}
                row.update(id=uuid.uuid4().hex, borrower=body['borrower'].strip(), status='active')
                state['reservations'].append(row)
            else:
                return self.error(404, 'not_found')
        except (ValueError, TypeError):
            if FAULT == 'invalid_mutates':
                state['equipment'].append({'id': uuid.uuid4().hex, 'name': 'corruption'})
                self.save()
            return self.error(400, 'invalid_input')
        self.save()
        self.send(201, row)


HTTPServer(('0.0.0.0', int(os.environ.get('PORT', '3000'))), Handler).serve_forever()
