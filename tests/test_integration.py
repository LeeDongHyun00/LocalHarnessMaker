"""Opt-in Docker/Chromium evaluator checks; no paid model calls."""
import json
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

from harness import backend, frontend
from harness.container import ContainerService, docker
from harness.packages import PILOT, ROOT
from harness.results import MeasurementError, evaluate_cases

OUTPUT = ROOT / '.local/harness-validation'
FIXTURES = ROOT / 'tests/fixtures'


def save(name, value):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class IntegrationTests(unittest.TestCase):
    def test_nested_directories_and_links_are_preserved_in_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / 'nested').mkdir()
            (source / 'empty-data').mkdir()
            shutil.copyfile(FIXTURES / 'backend/server.py', source / 'nested/server.py')
            shutil.copyfile(FIXTURES / 'backend/run.json', source / 'run.json')
            (source / 'server.py').symlink_to('nested/server.py')
            with ContainerService(source, 'python') as service:
                checks = json.loads(service.exec('python', '-c', "import json,os;from pathlib import Path;print(json.dumps({'empty_directory_preserved':Path('empty-data').is_dir(),'nested_directory_writable':os.access('nested',os.W_OK),'internal_link_preserved':Path('server.py').is_symlink()}))"))
                self.assertTrue(all(checks.values()), checks)
                save('filesystem-packaging.json', checks)

    def test_frontend_additional_requirement_probes(self):
        adapter = json.loads((FIXTURES / 'frontend/ui-adapter.json').read_text())
        factory = lambda: ContainerService(FIXTURES / 'frontend', 'node')
        results = []
        with sync_playwright() as pw:
            with pw.chromium.launch(headless=True) as browser:
                for case_id in ('F4.1', 'F6.1'):
                    with frontend.browser_subject(factory, browser, adapter) as ui:
                        frontend.cases()[case_id](ui)
                    results.append({'case_id': case_id, 'status': 'pass',
                                    'extra_probe': 'whole-name vs substring search' if case_id=='F4.1' else 'negative quantity'})
        save('frontend-extra.json', results)

    def test_backend_reference_and_mutants(self):
        card = json.loads((PILOT / 'backend-001/intent-card.json').read_text())
        source = FIXTURES / 'backend'
        factory = lambda: ContainerService(source, 'python')
        report = evaluate_cases(card, backend.cases(), factory)
        save('backend-reference.json', report)
        self.assertTrue(report['complete'], json.dumps(report, ensure_ascii=False))
        probes = [('closed_boundary', 'B3.2'), ('cross_equipment', 'B3.3'),
                  ('cancel_blocks', 'B4.1'), ('delete_cancelled', 'B4.2'),
                  ('filter_or', 'B5.1'), ('unsorted', 'B5.2'),
                  ('invalid_mutates', 'B6.2'), ('no_persistence', 'B7.1')]
        results = []
        for fault, case in probes:
            with self.subTest(fault=fault):
                with ContainerService(source, 'python', environment={'FIXTURE_FAULT': fault}) as service:
                    with self.assertRaises(AssertionError):
                        backend.cases()[case](service)
                results.append({'fault': fault, 'case_id': case, 'detected': True})
        save('backend-mutants.json', results)

    def test_frontend_reference_and_mutants(self):
        card = json.loads((PILOT / 'frontend-001/intent-card.json').read_text())
        source = FIXTURES / 'frontend'
        adapter = json.loads((source / 'ui-adapter.json').read_text())
        factory = lambda: ContainerService(source, 'node')
        with sync_playwright() as pw:
            with pw.chromium.launch(headless=True) as browser:
                report = evaluate_cases(card, frontend.cases(),
                                        lambda: frontend.browser_subject(factory, browser, adapter))
                save('frontend-reference.json', report)
                self.assertTrue(report['complete'], json.dumps(report, ensure_ascii=False))
                probes = [('exclusive_imminent', 'F3.1'), ('untrimmed_search', 'F4.1'),
                          ('reverse_ties', 'F4.2'), ('zero_retained', 'F2.2'),
                          ('no_persistence', 'F5.1'), ('invalid_accepted', 'F6.1'),
                          ('missing_notices', 'F7.1'), ('keyboard_unreachable', 'F7.2')]
                results = []
                for fault, case in probes:
                    with self.subTest(fault=fault):
                        faulty = lambda: ContainerService(source, 'node', environment={'FIXTURE_FAULT': fault})
                        with frontend.browser_subject(faulty, browser, adapter) as ui:
                            with self.assertRaises(AssertionError):
                                frontend.cases()[case](ui)
                        results.append({'fault': fault, 'case_id': case, 'detected': True})
                save('frontend-mutants.json', results)
                missing = json.loads(json.dumps(adapter))
                missing['review']['visible_focus_verified'] = None
                with frontend.browser_subject(factory, browser, missing) as ui:
                    with self.assertRaises(MeasurementError):
                        frontend.cases()['F7.2'](ui)

    def test_container_isolation_and_cleanup(self):
        with ContainerService(FIXTURES / 'backend', 'python') as service:
            name = service.name
            script = """
import json, os, socket
from pathlib import Path
checks = {
 'nonroot': os.getuid() == 1000,
 'hidden_intent_absent': not Path('/workspace/LocalHarnessMaker/experiments/pilot-v1/projects/backend-001/intent-card.json').exists(),
 'host_credentials_unreadable': not os.access('/root/.codex/auth.json', os.R_OK),
 'docker_socket_absent': not Path('/var/run/docker.sock').exists(),
 'no_model_credentials_in_environment': all(k not in os.environ for k in ('OPENAI_API_KEY','CODEX_API_KEY','CODEX_AUTH_TOKEN')),
 'work_writable': os.access('/work',os.W_OK),
}
for key, host, port in [('outbound_blocked','example.com',443),('proxy_blocked','proxy',8080)]:
 try:
  with socket.create_connection((host,port),timeout=1): checks[key]=False
 except OSError: checks[key]=True
try:
 Path('/host-write-probe').write_text('unexpected')
 checks['root_readonly']=False
except OSError: checks['root_readonly']=True
print(json.dumps(checks))
"""
            checks = json.loads(service.exec('python', '-c', script))
            self.assertTrue(all(checks.values()), checks)
            mounts = json.loads(docker('inspect', '--format', '{{json .Mounts}}', name))
            self.assertTrue(all(m['Type'] != 'bind' for m in mounts))
            state = json.loads(docker('inspect', '--format', '{{json .HostConfig}}', name))
            self.assertTrue(state['ReadonlyRootfs'])
            self.assertEqual(state['CapDrop'], ['ALL'])
            self.assertEqual(state['NetworkMode'], 'none')
            save('isolation.json', {'checks': checks, 'host_bind_mount_count': 0,
                                    'scope': 'offline submitted-service containers, not live teacher session'})
        self.assertEqual(docker('ps', '-aq', '--filter', f'name=^{name}$'), '')
        self.assertEqual(docker('volume', 'ls', '-q', '--filter', f'name=^{service.volume}$'), '')
        self.assertEqual(docker('network', 'ls', '-q', '--filter', f'name=^{service.network}$'), '')

    def test_browser_outbound_requests_are_blocked(self):
        adapter = json.loads((FIXTURES / 'frontend/ui-adapter.json').read_text())
        factory = lambda: ContainerService(FIXTURES / 'frontend', 'node')
        with sync_playwright() as pw:
            with pw.chromium.launch(headless=True) as browser:
                with frontend.browser_subject(factory, browser, adapter) as ui:
                    # Start asynchronously, then use a bounded Playwright wait. Awaiting
                    # fetch inside evaluate can deadlock synchronous route callbacks.
                    ui.page.evaluate("""() => {
                      window.isolationChecks = {http_outbound_blocked:null, websocket_outbound_blocked:null};
                      fetch('http://example.com/hidden')
                        .then(() => window.isolationChecks.http_outbound_blocked = false)
                        .catch(() => window.isolationChecks.http_outbound_blocked = true);
                      const ws = new WebSocket('ws://example.com/hidden');
                      ws.onopen = () => { window.isolationChecks.websocket_outbound_blocked=false; ws.close(); };
                      ws.onerror = () => window.isolationChecks.websocket_outbound_blocked=true;
                      ws.onclose = () => { if(window.isolationChecks.websocket_outbound_blocked===null) window.isolationChecks.websocket_outbound_blocked=true; };
                    }""")
                    ui.page.wait_for_function('Object.values(window.isolationChecks).every(x=>x!==null)', timeout=3000)
                    checks = ui.page.evaluate('window.isolationChecks')
                    self.assertTrue(all(checks.values()), checks)
                    save('browser-isolation.json', checks)


if __name__ == '__main__':
    unittest.main()
