"""Inbound-only local port bridge to a container with --network=none.

Docker exec pipes carry bytes to the service's loopback port. The container gets
no host interface, published port, socket mount, gateway, or outbound route.
"""
import os
import socketserver
import subprocess
import threading

PYTHON_RELAY = """
import os, socket, threading
s = socket.create_connection(('127.0.0.1', 3000), timeout=3)
s.settimeout(None)
def forward_input():
 try:
  while True:
   data = os.read(0, 65536)
   if not data: break
   s.sendall(data)
 finally:
  s.shutdown(socket.SHUT_WR)
threading.Thread(target=forward_input,daemon=True).start()
while True:
 data = s.recv(65536)
 if not data: break
 os.write(1,data)
"""
NODE_RELAY = """
const socket=require('node:net').connect(3000,'127.0.0.1');
socket.on('error',()=>process.exit(1));
socket.on('close',()=>process.exit(0));
process.stdin.pipe(socket);socket.pipe(process.stdout);
"""


class PortBridge:
    def __init__(self, container, runtime):
        bridge = self
        self.processes = set()
        self.lock = threading.Lock()
        relay = ['python', '-u', '-c', PYTHON_RELAY] if runtime == 'python' else ['node', '-e', NODE_RELAY]

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                child = subprocess.Popen(['docker', 'exec', '-i', container, *relay],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, bufsize=0)
                with bridge.lock:
                    bridge.processes.add(child)
                def send():
                    try:
                        while data := self.request.recv(65536):
                            child.stdin.write(data)
                    except (OSError, ValueError):
                        pass
                    finally:
                        try:
                            child.stdin.close()
                        except OSError:
                            pass
                threading.Thread(target=send, daemon=True).start()
                try:
                    while data := os.read(child.stdout.fileno(), 65536):
                        self.request.sendall(data)
                except OSError:
                    pass
                finally:
                    child.terminate()
                    try:
                        child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    child.stdout.close()
                    with bridge.lock:
                        bridge.processes.discard(child)

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            block_on_close = False

        self.server = Server(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        with self.lock:
            for process in self.processes:
                process.terminate()
