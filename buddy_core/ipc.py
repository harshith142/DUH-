"""
Local IPC (Inter-Process Communication) Server & Client for Bahubali Desktop Buddy.
Enables instant CLI control of the live desktop buddy over local loopback.
"""

import json
import socket
import threading

DEFAULT_PORT = 18899
BUFFER_SIZE = 4096


class IPCServer:
    def __init__(self, port=DEFAULT_PORT, message_handler=None):
        self.port = port
        self.handler = message_handler
        self.server_sock = None
        self.is_running = False
        self.thread = None

    def start(self):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(("127.0.0.1", self.port))
            self.server_sock.listen(5)
            self.is_running = True

            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            err_msg = f"[IPC Server Init Error] {e}"
            print(err_msg)
            try:
                log_path = os.path.expanduser("~/.duh_buddy/gui_runtime.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(err_msg + "\n")
            except Exception:
                pass
            return False

    def _listen_loop(self):
        while self.is_running:
            try:
                client, addr = self.server_sock.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except Exception as e:
                if not self.is_running:
                    break
                try:
                    log_path = os.path.expanduser("~/.duh_buddy/gui_runtime.log")
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(f"[IPC Accept Error] {e}\n")
                except Exception:
                    pass

    def _handle_client(self, client):
        try:
            raw_data = client.recv(BUFFER_SIZE)
            if raw_data:
                msg = json.loads(raw_data.decode("utf-8"))
                response = {"status": "ok", "reply": "Received"}
                if self.handler:
                    reply_text = self.handler(msg)
                    response["reply"] = reply_text
                client.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            err_resp = {"status": "error", "error": str(e)}
            try:
                client.sendall(json.dumps(err_resp).encode("utf-8"))
            except Exception:
                pass
        finally:
            client.close()

    def stop(self):
        self.is_running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass


class IPCClient:
    def __init__(self, port=DEFAULT_PORT):
        self.port = port

    def is_daemon_running(self):
        """Check if DUH is currently active on desktop."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", self.port))
                return True
        except Exception:
            return False

    def send_command(self, cmd_type, payload):
        """Send command JSON to DUH daemon and wait for response."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15.0)
                s.connect(("127.0.0.1", self.port))
                req = {"type": cmd_type, "data": payload}
                s.sendall(json.dumps(req).encode("utf-8"))
                resp_bytes = s.recv(BUFFER_SIZE)
                if resp_bytes:
                    return json.loads(resp_bytes.decode("utf-8"))
                return {"status": "ok", "reply": "Executed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
