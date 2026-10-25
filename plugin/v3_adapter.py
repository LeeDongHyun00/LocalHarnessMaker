"""The sole cross-package spelling/message adapter for the v3 hook path."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import pwd
import sys
import time
from typing import Any, Callable

from plugin.hooks._process import run_group


# Resolve from this installed module, independently of cwd and schema lookup roots.
RUNTIME_ROOT = Path(__file__).resolve().parents[1]


def redact_home(text: str) -> str:
    for home in sorted({str(Path.home()), pwd.getpwuid(os.getuid()).pw_dir, os.environ.get('HOME', ''),
                        os.environ.get('CODEX_HOME', '')}, key=len, reverse=True):
        if home and home != '/':
            text = text.replace(home, '<HOME>')
    return text


class CallFailure(RuntimeError):
    """A retained subprocess failure that the hook can surface without blocking."""


class Adapter:
    def __init__(self, runner: Callable[..., Any] = run_group, *, budget: float = 650) -> None:
        self.runner = runner
        self.deadline = time.monotonic() + budget
        self.seconds = 0.0
        self.on_failure: Callable[[dict[str, Any]], None] | None = None

    def call(self, module: str, operation: str, *, session_id: str, directory: Path,
             workspace: Path | None = None, prompt: Path | None = None,
             requirements: Path | None = None, final: Path | None = None,
             round_number: int | None = None, audit: Path | None = None,
             ledger: Path | None = None) -> Any:
        args = ['--session-id', session_id, '--artifacts', str(directory)]
        for flag, value in (('--workspace', workspace), ('--prompt', prompt),
                            ('--requirements', requirements), ('--final-message', final),
                            ('--round', round_number), ('--claim-audit', audit), ('--ledger', ledger)):
            if value is not None:
                args += [flag, str(value)]
        command = [os.environ.get('HARNESS_PYTHON', sys.executable), '-m', module, operation, *args]
        timeout = min(30 if module == 'controller' else 480 if operation == 'check' else 2,
                      self.deadline - time.monotonic())
        if timeout <= 0:
            detail = self.failure(module, operation, None, 'hook cumulative deadline exhausted')
            raise CallFailure(detail)
        child_env = {**os.environ, 'HARNESS_NESTED': '1'}
        if executable := child_env.get('HARNESS_CODEX'):
            directory_path = str(Path(executable).parent)
            prior_path = child_env.get('PATH', '')
            child_env['PATH'] = directory_path + (os.pathsep + prior_path if prior_path else '')
        started = time.monotonic()
        try:
            result = self.runner(command, cwd=RUNTIME_ROOT, env=child_env,
                                 shell=False, text=True, capture_output=True, check=False, timeout=timeout)
        except Exception as exc:
            stderr = getattr(exc, 'stderr', '') or ''
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors='replace')
            self.failure(module, operation, None, stderr or str(exc))
            raise CallFailure(redact_home(f'{module} {operation}: {type(exc).__name__}: {exc}').splitlines()[0]) from exc
        finally:
            self.seconds += time.monotonic() - started
        if result.returncode:
            detail = self.failure(module, operation, result.returncode, result.stderr or '')
            if not (operation == 'ledger-validate' and result.returncode == 1):
                raise CallFailure(detail)

        return result

    def failure(self, module: str, operation: str, exit_code: int | None, stderr: str) -> str:
        tail = redact_home(stderr)[-1000:]
        record = {'module': module, 'operation': operation, 'exit_code': exit_code,
                  'stderr_tail': tail}
        if self.on_failure is not None:
            self.on_failure(record)
        first = tail.splitlines()[0] if tail else '(no stderr)'
        return f'{module} {operation} exited {exit_code}: {first}'

    def repair_text(self, requirements: dict[str, Any], report: dict[str, Any],
                    failed_rows: list[str]) -> str:
        # Retained verifier formatter is usable without inheriting its retry policy.
        from verifier.reinstruct import reinstruct
        criteria = [{'id': r['id'], 'description': r['text'], 'check': r['check']}
                    for r in requirements['requirements'] if r['id'] in failed_rows]
        items = [{'id': r['requirement_id'], 'status': 'fail', 'reason': r['reason'],
                  'evidence': '\n'.join(e['excerpt'] for e in r['evidence'])}
                 for r in report['items'] if r['requirement_id'] in failed_rows and r['status'] == 'fail']
        message = reinstruct(criteria, items, 1, 2)
        if not message:
            raise ValueError('verifier supplied no executed-failure repair message')
        return message

    def ledger_text(self, directory: Path, session_id: str) -> str:
        """Resolve Role 4's pending in-package formatter in this one adapter seam.

        No locally authored ledger fallback: missing formatter is visible and
        fail-open. Adjust here when the concurrently implemented package lands.
        """
        module = importlib.import_module('verifier.ledger')
        message = module.ledger_request(ledger=directory / 'ledger.json',
                                        requirements=directory / 'requirements.json', session_id=session_id)
        if not isinstance(message, str) or not message.strip():
            raise ValueError('verifier ledger request is empty')
        return message
