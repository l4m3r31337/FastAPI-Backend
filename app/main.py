import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from app.db.db import engine, AsyncSessionLocal
from app.models.models import SQLModel
from app.api.api import router
from app.tasks.task import periodic_task
from app.nats.nats import connect_nats, subscribe_to_currency_updates
from app.services.nats_handlers import currency_update_handler
from app.ws.ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await connect_nats()

    await subscribe_to_currency_updates(currency_update_handler)

    task = asyncio.create_task(periodic_task(AsyncSessionLocal))

    yield

    task.cancel()



app = FastAPI(title="Currency Async Backend", lifespan=lifespan)
app.include_router(router)


@app.websocket("/ws/items")
async def websocket_items(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
