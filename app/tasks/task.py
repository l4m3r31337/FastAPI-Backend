import httpx
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime

from app.models.models import CurrencyRate
from app.config import settings
from app.nats.nats import publish_event
from app.ws.ws import manager


async def fetch_rates(db: AsyncSession):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(settings.CBR_URL)
        data = response.json()

    rates = {
        "USD": data["Valute"]["USD"]["Value"],
        "EUR": data["Valute"]["EUR"]["Value"],
        "JPY": data["Valute"]["JPY"]["Value"],
    }

    for code, value in rates.items():
        stmt = select(CurrencyRate).where(CurrencyRate.code == code)
        result = await db.execute(stmt)
        rate = result.scalar_one_or_none()

        if rate:
            rate.value = value
            rate.updated_at = datetime.utcnow()
        else:
            rate = CurrencyRate(code=code, value=value)
            db.add(rate)

        await db.commit()
        await db.refresh(rate)

        event = {
            "type": "currency_updated",
            "code": code,
            "value": value,
        }

        await publish_event("currency.updates", event)
        await manager.broadcast(event)


async def periodic_task(db_factory):
    while True:
        async with db_factory() as db:
            await fetch_rates(db)
        await asyncio.sleep(settings.TASK_INTERVAL_SECONDS)
