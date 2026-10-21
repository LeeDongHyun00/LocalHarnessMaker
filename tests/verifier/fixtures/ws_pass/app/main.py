"""Reference FastAPI workspace; dependencies are intentionally not vendored."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
