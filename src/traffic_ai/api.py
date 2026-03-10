from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .network import build_demo_network


NETWORK = build_demo_network()


class TrafficAPIHandler(BaseHTTPRequestHandler):
    server_version = "TrafficAI/0.1"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/network":
            self._send_json(HTTPStatus.OK, NETWORK.snapshot())
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "route_not_found"})

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read_json_body()
        if payload is None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        try:
            if self.path == "/vision/update":
                result = NETWORK.ingest_detections(
                    payload["intersection_id"], payload["detections"]
                )
                self._send_json(HTTPStatus.OK, result)
                return
            if self.path == "/optimize":
                self._send_json(HTTPStatus.OK, NETWORK.optimize())
                return
            if self.path == "/emergency/corridor":
                result = NETWORK.activate_green_corridor(payload)
                self._send_json(HTTPStatus.OK, result)
                return
        except KeyError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "missing_field", "field": str(exc)},
            )
            return
        except Exception as exc:  # pragma: no cover - defensive handler
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal_error", "detail": str(exc)},
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "route_not_found"})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any] | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length) if content_length else b"{}"
            return json.loads(body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), TrafficAPIHandler)
    print(f"Traffic AI API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
