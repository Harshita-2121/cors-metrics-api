# CORS-Aware Metrics API

FastAPI API for the IIT Madras TDS CORS-aware metrics assignment.

- `GET /stats?values=1,2,3` calculates count, sum, min, max, and mean.
- The only allowed CORS origin is `https://dash-4ebo88.example.com`.
- Every response includes `X-Request-ID` and `X-Process-Time`.
- The student email must exactly match the signed-in course account.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Try `http://127.0.0.1:8000/stats?values=1,2,3`.

## Render deployment

Create a public GitHub repository, upload these files, then create a Render Web Service connected to that repository. Build command: `pip install -r requirements.txt`; start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

## Important

The assigned origin and email are set in `main.py`. Change them only if the assignment panel gives different values for your own account.
