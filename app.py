"""Minimal stateless MCP Streamable HTTP server for the TDS live-MCP task."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="TDS Live MCP Server", docs_url="/docs", redoc_url=None)
EXAM_EMAIL = os.getenv("EXAM_EMAIL", "24f3002072@ds.study.iitm.ac.in").strip().lower()
SERVER_VERSION = "1.0.0"
DEFAULT_PROTOCOL_VERSION = "2025-03-26"


def rpc_result(request_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def rpc_error(request_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}},
        status_code=200,
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "TDS live MCP server", "endpoint": "/mcp", "health": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    """Handle MCP JSON-RPC messages over Streamable HTTP."""
    try:
        message = await request.json()
    except Exception:
        return JSONResponse({"error": "Request body must be valid JSON"}, status_code=400)

    if not isinstance(message, dict):
        return JSONResponse({"error": "Expected a JSON-RPC object"}, status_code=400)

    method = message.get("method")
    request_id = message.get("id")
    has_id = "id" in message

    # MCP notifications are one-way messages and should not return a JSON-RPC body.
    if isinstance(method, str) and method.startswith("notifications/") and not has_id:
        return Response(status_code=202)

    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return rpc_error(request_id, -32600, "Invalid JSON-RPC request")

    if method == "initialize":
        params = message.get("params") or {}
        requested_version = params.get("protocolVersion") if isinstance(params, dict) else None
        protocol_version = requested_version if isinstance(requested_version, str) else DEFAULT_PROTOCOL_VERSION
        return rpc_result(
            request_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "tds-live-challenge-server", "version": SERVER_VERSION},
            },
        )

    if method == "ping":
        return rpc_result(request_id, {})

    if method == "tools/list":
        return rpc_result(
            request_id,
            {
                "tools": [
                    {
                        "name": "solve_challenge",
                        "description": "Return the required digest for the X-Exam-Challenge header and registered exam email.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    }
                ]
            },
        )

    if method == "tools/call":
        params = message.get("params") or {}
        if not isinstance(params, dict) or params.get("name") != "solve_challenge":
            return rpc_error(request_id, -32602, "Unknown tool. The only tool is solve_challenge.")

        # The challenge is intentionally taken from HTTP headers, never from JSON arguments.
        challenge = request.headers.get("x-exam-challenge")
        if challenge is None:
            return rpc_result(
                request_id,
                {"content": [{"type": "text", "text": "Missing X-Exam-Challenge header."}], "isError": True},
            )

        normalized_email = EXAM_EMAIL.strip().lower()
        digest = hashlib.sha256(f"{challenge}:{normalized_email}".encode("utf-8")).hexdigest()[:16]
        return rpc_result(
            request_id,
            {"content": [{"type": "text", "text": digest}], "isError": False},
        )

    if not has_id:
        # Other notifications are also accepted as one-way messages.
        return Response(status_code=202)
    return rpc_error(request_id, -32601, f"Method not found: {method}")


# A minimal public preflight response helps browsers / hosted MCP test clients.
@app.options("/mcp")
async def mcp_options() -> Response:
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, X-Exam-Challenge, X-Exam-Timestamp, X-Exam-Signature",
        },
    )
