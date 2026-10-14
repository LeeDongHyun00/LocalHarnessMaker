"""Run submitted services without host mounts, credentials, or external network routes."""

import io
import json
import os
import subprocess
import tarfile
import time
import uuid
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

from .results import MeasurementError, SubmissionError
from .bridge import PortBridge

LOCK = Path(__file__).resolve().parent / 'runtime-lock.json'


def docker(*args, input=None, check=True):
    result = subprocess.run(['docker', *args], input=input, capture_output=True, timeout=90)
    if check and result.returncode:
        raise MeasurementError(result.stderr.decode(errors='replace')[-2000:])
    return result.stdout.decode(errors='replace').strip()


def source_files(source):
    """Enumerate artifact entries, including directories and safe relative links."""
    source = Path(source).resolve()
    excluded = {'.git', '.local', '__pycache__', '.DS_Store'}
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source)
        if any(part in excluded for part in relative.parts):
            continue
        if path.is_symlink():
            target = os.readlink(path)
            try:
                resolved = path.resolve()
            except (OSError, RuntimeError) as error:
                raise SubmissionError(f'Unresolvable artifact symlink: {relative}') from error
            if (os.path.isabs(target) or not resolved.is_relative_to(source) or
                    not resolved.exists() or any(p in excluded for p in resolved.relative_to(source).parts)):
                raise SubmissionError(f"Unsafe or broken artifact symlink: {relative}")
            yield path, relative
        elif path.is_file() or path.is_dir():
            yield path, relative
        else:
            raise SubmissionError(f"Unsupported artifact file: {relative}")


def source_archive(source):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w') as archive:
        for path, relative in source_files(source):
            info = archive.gettarinfo(str(path), arcname=str(relative))
            info.uid = info.gid = 1000
            info.uname = info.gname = ''
            if path.is_symlink() or path.is_dir():
                archive.addfile(info)
            else:
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
    return output.getvalue()


class ContainerService:
    def __init__(self, source, runtime, ready_timeout=15, environment=None):
        self.source = Path(source).resolve()
        self.image = json.loads(LOCK.read_text())['images'][runtime]['ref']
        self.runtime = runtime
        self.ready_timeout = ready_timeout
        self.environment = environment or {}
        if any(k not in {'FIXTURE_FAULT'} for k in self.environment):
            raise ValueError("Only the harness test fault selector is supported")
        token = uuid.uuid4().hex
        self.name, self.network, self.volume = [f'lhm-{x}-{token}' for x in ('app', 'net', 'data')]
        self.url = None
        self.bridge = None
        self.opener = build_opener(ProxyHandler({}))  # loopback only; never used for outbound traffic

    def __enter__(self):
        try:
            config = json.loads((self.source / 'run.json').read_text())
        except (OSError, ValueError) as error:
            raise SubmissionError(f"Invalid or missing run.json: {error}") from error
        if not isinstance(config, dict):
            raise SubmissionError('run.json must contain an object')
        command, ready = config.get('start_command'), config.get('ready_url')
        if not (isinstance(command, list) and command and
                all(isinstance(x, str) and x for x in command)):
            raise SubmissionError('start_command must be a nonempty string array')
        if ready not in ('/', '/equipment'):
            raise SubmissionError('ready_url must be the common-contract local path')
        payload = source_archive(self.source)
        try:
            docker('volume', 'create', self.volume)
            options = ['create', '--name', self.name, '--network', 'none',
                       '--user', '1000:1000', '--cap-drop', 'ALL',
                       '--security-opt', 'no-new-privileges', '--read-only',
                       '--pids-limit', '128', '--memory', '512m', '--cpus', '1',
                       '--stop-timeout', '5', '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m',
                       '--mount', f'type=volume,source={self.volume},target=/work',
                       '--workdir', '/work',
                       '-e', 'PORT=3000', '-e', 'TZ=Asia/Seoul', '-e', 'PYTHONDONTWRITEBYTECODE=1']
            for key, value in self.environment.items():
                options += ['-e', f'{key}={value}']
            docker(*options, self.image, *command)
            # Named-volume root must be writable by the service UID; no source mount.
            docker('run', '--rm', '--network', 'none', '--mount',
                   f'type=volume,source={self.volume},target=/work',
                   self.image, 'chown', '1000:1000', '/work')
            docker('cp', '-a', '-', f'{self.name}:/work', input=payload)
            docker('start', self.name)
            self.bridge = PortBridge(self.name, self.runtime)
            self.url = self.bridge.url
            self.ready_path = ready
            self.wait_ready()
            return self
        except BaseException:
            self.close()
            raise

    def wait_ready(self):
        deadline = time.monotonic() + self.ready_timeout
        while time.monotonic() < deadline:
            running = docker('inspect', '--format', '{{.State.Running}}', self.name)
            if running != 'true':
                raise SubmissionError('Submitted service exited before readiness')
            try:
                with self.opener.open(self.url + self.ready_path, timeout=1) as response:
                    if response.status == 200:
                        return
            except (OSError, HTTPException):
                pass
            time.sleep(.1)
        raise SubmissionError('Submitted service did not become ready within the timeout')

    def restart(self):
        docker('restart', self.name)
        self.wait_ready()

    def exec(self, *command):
        return docker('exec', self.name, *command)

    def close(self):
        if self.bridge:
            self.bridge.close()
            self.bridge = None
        docker('rm', '-f', self.name, check=False)
        docker('volume', 'rm', self.volume, check=False)

    def __exit__(self, *_):
        self.close()
