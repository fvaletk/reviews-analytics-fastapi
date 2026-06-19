from fastapi import FastAPI

from app.routers import scrape

app = FastAPI(title="Reviews Analytics Scraper", version="1.0.0")

app.include_router(scrape.router)


@app.get("/health")
def health():
    return {"status": "ok"}