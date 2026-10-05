from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.web import labels
from app.web.routes import router, templates

app = FastAPI(title="Kabinet agenta — AI-agent za nekretnine za Telegram")

templates.env.globals.update(
    status_labels=labels.STATUS_LABELS,
    temperature_labels=labels.TEMPERATURE_LABELS,
    deal_type_labels=labels.DEAL_TYPE_LABELS,
    property_type_labels=labels.PROPERTY_TYPE_LABELS,
    reaction_labels=labels.REACTION_LABELS,
    source_labels=labels.SOURCE_LABELS,
)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
