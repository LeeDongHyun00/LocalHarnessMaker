"""Browser proxy that can connect only to one assigned loopback service.

HTTP and WebSocket CONNECT requests for every other host or local port are
rejected. This avoids reliance on JavaScript route callbacks for WebSocket
isolation and never forwards a request through the environment's outbound proxy.
"""
import socket
import socketserver
import threading
from urllib.parse import urlsplit


class BrowserProxy:
    def __init__(self, service_url):
        target = urlsplit(service_url)
        if target.hostname != '127.0.0.1' or not target.port:
            raise ValueError('Browser proxy target must be an assigned loopback port')
        proxy = self
        self.sockets = set()
        self.lock = threading.Lock()

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                upstream = None
                try:
                    self.request.settimeout(5)
                    header = b''
                    while b'\r\n\r\n' not in header:
                        chunk = self.request.recv(65536)
                        if not chunk or len(header) + len(chunk) > 65536:
                            return
                        header += chunk
                    head, rest = header.split(b'\r\n\r\n', 1)
                    lines = head.split(b'\r\n')
                    method, destination, version = lines[0].decode('ascii').split(' ', 2)
                    tunnel = method == 'CONNECT'
                    requested = urlsplit('http://' + destination if tunnel else destination)
                    if requested.hostname != target.hostname or requested.port != target.port:
                        self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                        return
                    upstream = socket.create_connection((target.hostname, target.port), timeout=3)
                    upstream.settimeout(None)
                    self.request.settimeout(None)
                    with proxy.lock:
                        proxy.sockets.update((self.request, upstream))
                    if tunnel:
                        self.request.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                        initial = rest
                    else:
                        path = requested.path or '/'
                        if requested.query:
                            path += '?' + requested.query
                        upgrade = any(line.lower().startswith(b'upgrade:') for line in lines[1:])
                        forwarded = [line for line in lines[1:] if not line.lower().startswith(b'proxy-connection:')]
                        if not upgrade:
                            forwarded = [line for line in forwarded if not line.lower().startswith(b'connection:')]
                            forwarded.append(b'Connection: close')
                        first = f'{method} {path} {version}'.encode('ascii')
                        initial = b'\r\n'.join([first, *forwarded]) + b'\r\n\r\n' + rest
                    if initial:
                        upstream.sendall(initial)
                    def incoming():
                        try:
                            while data := self.request.recv(65536):
                                upstream.sendall(data)
                        except OSError:
                            pass
                        finally:
                            try:
                                upstream.shutdown(socket.SHUT_WR)
                            except OSError:
                                pass
                    threading.Thread(target=incoming, daemon=True).start()
                    while data := upstream.recv(65536):
                        self.request.sendall(data)
                except (OSError, ValueError, UnicodeError):
                    pass
                finally:
                    with proxy.lock:
                        proxy.sockets.discard(self.request)
                        if upstream:
                            proxy.sockets.discard(upstream)
                    if upstream:
                        upstream.close()

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            block_on_close = False

        self.server = Server(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        with self.lock:
            for stream in self.sockets:
                try:
                    stream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                stream.close()
        self.thread.join(timeout=2)
