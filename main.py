import time
import uuid
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="CORS-Aware Metrics API")

# These values are assigned by the IITM question. Keep them exact.
ALLOWED_ORIGIN = "https://dash-4ebo88.example.com"
STUDENT_EMAIL = "24f3002072@ds.study.iitm.ac.in"


@app.middleware("http")
async def cors_and_required_headers(request, call_next):
    """Enforce the one allowed origin and attach timing/ID headers to responses."""
    started = time.perf_counter()
    origin = request.headers.get("origin")

    # Handle browser CORS preflights explicitly. Never reflect an unapproved origin.
    if request.method == "OPTIONS" and request.url.path == "/stats":
        if origin == ALLOWED_ORIGIN:
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            requested_headers = request.headers.get("access-control-request-headers")
            if requested_headers:
                response.headers["Access-Control-Allow-Headers"] = requested_headers
            response.headers["Vary"] = "Origin"
        else:
            response = Response(status_code=403)
    else:
        response = await call_next(request)
        if origin == ALLOWED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Vary"] = "Origin"

    elapsed = max(0.0, time.perf_counter() - started)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"
    return response


@app.get("/stats")
async def stats(values: Annotated[str, Query(description="Comma-separated integers")]):
    try:
        numbers = [int(part.strip()) for part in values.split(",")]
        if not numbers:
            raise ValueError("At least one integer is required")
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={"error": "values must be a comma-separated list of integers"},
        )

    total = sum(numbers)
    return {
        "email": STUDENT_EMAIL,
        "count": len(numbers),
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / len(numbers),
    }


@app.get("/")
async def health():
    return {"status": "ok", "service": "CORS-Aware Metrics API"}
