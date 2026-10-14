import json
import tempfile
import socket
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from harness.packages import PILOT, ROOT, artifact_digest, blind_package, inventory, judge_order, prepare, review_package
from harness.results import MeasurementError, SubmissionError, correction_message, evaluate_cases
from harness.browser_proxy import BrowserProxy
from harness.container import ContainerService


@contextmanager
def local_reference_server():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_GET(self):
            data = self.path.encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def proxy_socket(proxy):
    from urllib.parse import urlsplit
    parsed = urlsplit(proxy.url)
    return socket.create_connection((parsed.hostname, parsed.port), timeout=3)


def read_all(stream):
    chunks = []
    while data := stream.recv(65536):
        chunks.append(data)
    return b''.join(chunks)


class HarnessUnitTests(unittest.TestCase):
    def test_invalid_execution_contract_is_a_product_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in ([], 'python server.py', {'start_command':'python server.py','ready_url':'/'},
                          {'start_command':['python'],'ready_url':'https://example.com/'}):
                (Path(tmp) / 'run.json').write_text(json.dumps(value))
                with self.assertRaises(SubmissionError):
                    with ContainerService(tmp, 'python'):
                        pass
    def test_browser_proxy_blocks_external_hosts_and_other_local_ports(self):
        with local_reference_server() as url, BrowserProxy(url) as proxy:
            for target in ('example.com:443', proxy.url.split('//')[1]):
                with proxy_socket(proxy) as stream:
                    stream.sendall(f'CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n'.encode())
                    self.assertIn(b'403 Forbidden', read_all(stream))
            with proxy_socket(proxy) as stream:
                stream.sendall(b'GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n')
                self.assertIn(b'403 Forbidden', read_all(stream))

    def test_browser_proxy_preserves_assigned_http_and_connect_tunnel(self):
        with local_reference_server() as url, BrowserProxy(url) as proxy:
            with proxy_socket(proxy) as stream:
                stream.sendall(f'GET {url}/case?x=1 HTTP/1.1\r\nHost: {url.split("//")[1]}\r\n\r\n'.encode())
                response = read_all(stream)
                self.assertIn(b'200 OK', response)
                self.assertTrue(response.endswith(b'/case?x=1'))
            with proxy_socket(proxy) as stream:
                stream.sendall(f'CONNECT {url.split("//")[1]} HTTP/1.1\r\nHost: assigned\r\n\r\n'.encode())
                header = b''
                while b'\r\n\r\n' not in header:
                    header += stream.recv(1024)
                self.assertIn(b'200 Connection Established', header)
                stream.sendall(b'GET /tunnel HTTP/1.1\r\nHost: assigned\r\nConnection: close\r\n\r\n')
                response = read_all(stream)
                self.assertIn(b'200 OK', response)
                self.assertTrue(response.endswith(b'/tunnel'))

    def test_prepared_workspace_contains_only_common_and_assigned_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            for arm in 'ABCDE':
                destination = Path(tmp) / arm
                result = prepare('frontend-001', arm, destination)
                self.assertEqual(result['files'], ['COMMON_CONTEXT.md', 'TASK.md'])
                self.assertEqual((destination / 'TASK.md').read_bytes(),
                                 (PILOT / 'frontend-001/prompts' / f'{arm}.md').read_bytes())
                with self.assertRaises(FileExistsError):
                    prepare('frontend-001', arm, destination)

    def test_blind_package_preserves_bytes_and_keeps_mapping_private(self):
        with tempfile.TemporaryDirectory() as public_tmp, tempfile.TemporaryDirectory() as private_tmp:
            source = ROOT / 'tests/fixtures/backend'
            metadata = {'arm': 'C', 'run_id': 'secret-run', 'phase': 'first', 'model': 'gpt-6.1-sol'}
            first = blind_package(source, 'backend-001', public_tmp, private_tmp, metadata)
            second = blind_package(source, 'backend-001', public_tmp, private_tmp, metadata | {'phase': 'final'})
            self.assertNotEqual(first['artifact_id'], second['artifact_id'])
            package = Path(public_tmp) / first['artifact_id']
            self.assertEqual(inventory(source), inventory(package / 'artifact'))
            self.assertEqual(first['artifact_digest'], artifact_digest(source))
            manifest = json.loads((package / 'manifest.json').read_text())
            self.assertFalse({'arm', 'run_id', 'model', 'phase'} & manifest.keys())
            private_file = Path(private_tmp) / (first['artifact_id'] + '.json')
            self.assertEqual(private_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(private_file.read_text())['metadata'], metadata)
            with self.assertRaises(ValueError):
                judge_order(public_tmp)
            review_package(package, private_tmp, 'fixture-operator')
            review_package(Path(public_tmp) / second['artifact_id'], private_tmp, 'fixture-operator')
            self.assertEqual(set(judge_order(public_tmp)), {first['artifact_id'], second['artifact_id']})
            (package / 'artifact/README.md').write_text('changed after snapshot')
            with self.assertRaises(AssertionError):
                judge_order(public_tmp)
            with self.assertRaises(ValueError):
                blind_package(source, 'backend-001', public_tmp, ROOT / '.local/mapping', metadata)

    def test_symlink_cannot_import_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'leak').symlink_to(PILOT / 'frontend-001/intent-card.json')
            with self.assertRaises(AssertionError):
                inventory(tmp)

    def test_review_cannot_redefine_the_original_snapshot(self):
        with tempfile.TemporaryDirectory() as public, tempfile.TemporaryDirectory() as private:
            result = blind_package(ROOT / 'tests/fixtures/backend', 'backend-001', public, private, {'phase':'first'})
            package = Path(public) / result['artifact_id']
            (package / 'artifact/README.md').write_text('changed before review')
            manifest_path = package / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['artifact_digest'] = artifact_digest(package / 'artifact')
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):
                review_package(package, private, 'fixture-operator')

    def test_internal_relative_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            source.mkdir()
            (source / 'tool.js').write_text('fixture')
            (source / 'bin').mkdir()
            (source / 'bin/tool').symlink_to('../tool.js')
            (source / 'empty-data').mkdir()
            self.assertEqual(inventory(source)['bin/tool']['kind'], 'symlink')
            result = blind_package(source, 'backend-001', Path(tmp) / 'public', Path(tmp) / 'private', {})
            copied = Path(tmp) / 'public' / result['artifact_id'] / 'artifact'
            self.assertEqual(inventory(source), inventory(copied))
            self.assertTrue((copied / 'empty-data').is_dir())
            self.assertTrue((copied / 'bin/tool').is_symlink())

    def test_symlink_loop_is_an_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'loop').symlink_to('loop')
            with self.assertRaises(AssertionError):
                inventory(tmp)

    def test_measurement_error_is_not_product_correction(self):
        card = {'project_id': 'test', 'requirements': [
            {'id': 'X1', 'critical': True, 'acceptance': [{}], 'correction_feedback': 'critical'},
            {'id': 'X2', 'critical': False, 'acceptance': [{}], 'correction_feedback': 'secondary'}]}
        @contextmanager
        def factory():
            yield None
        def failure(_):
            raise AssertionError('wrong behavior')
        def broken(_):
            raise MeasurementError('broken evaluator')
        report = evaluate_cases(card, {'X1.1': failure, 'X2.1': broken}, factory)
        self.assertEqual([r['status'] for r in report['requirements']], ['fail', 'not_evaluated'])
        self.assertFalse(report['complete'])
        with self.assertRaises(MeasurementError):
            correction_message(card, report)
        failed = evaluate_cases(card, {'X2.1': failure, 'X1.1': failure}, factory)
        self.assertEqual(correction_message(card, failed), 'critical\nsecondary')
        with self.assertRaises(MeasurementError):
            evaluate_cases(card, {'X1.1': failure}, factory)


if __name__ == '__main__':
    unittest.main()
