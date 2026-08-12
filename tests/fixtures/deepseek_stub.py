from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class DeepSeekStubHandler(BaseHTTPRequestHandler):
    """Return a local deterministic completion without logging prompt content."""

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self.path != "/chat/completions":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload: Any = json.loads(raw_body)
        except json.JSONDecodeError:
            self.send_error(400)
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
            self.send_error(400)
            return

        response = {
            "id": "local-docker-smoke",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            "Supplier defect rate is Defect Count divided by "
                            "Inspected Count, expressed as a percentage [1]."
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DeepSeekStubHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
