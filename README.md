# TDS Live MCP Server

Minimal stateless MCP Streamable HTTP server for the assignment. It exposes exactly one tool: `solve_challenge`.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export EXAM_EMAIL='24f3002072@ds.study.iitm.ac.in'
uvicorn app:app --host 0.0.0.0 --port 8000
```

MCP endpoint: `http://127.0.0.1:8000/mcp`; health check: `/health`.

## Deploy on Render

1. Create a public GitHub repository and upload `app.py`, `requirements.txt`, and `render.yaml` to its root.
2. In Render, choose **New + → Blueprint**, connect that repository, and deploy the service described by `render.yaml`.
3. After deployment, check `https://YOUR-SERVICE.onrender.com/health` and confirm it returns `{"status":"ok"}`.
4. Submit `https://YOUR-SERVICE.onrender.com/mcp` in the assignment.

The signature header is not verified because the assignment says signature verification is optional; the server reads `X-Exam-Challenge` from the incoming HTTP request headers on each `tools/call`. It never reads the challenge from the JSON tool arguments. The returned text is the first 16 lowercase hex characters of SHA-256 of `challenge:normalizedEmail`.

For Render Free, a service can spin down after inactivity. Open `/health` and then grade while the service is awake; for reliable always-on behavior, use a hosting plan/platform that does not sleep.
