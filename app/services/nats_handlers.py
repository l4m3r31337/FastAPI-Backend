import json
import logging
from nats.aio.msg import Msg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime

from db.db import AsyncSessionLocal
from models.models import CurrencyRate
from ws.ws import manager

logger = logging.getLogger("nats-handler")


async def currency_update_handler(msg: Msg):
    data = json.loads(msg.data.decode())
    logger.info(f"Received NATS message: {data}")

    await manager.broadcast(data)

    if data.get("type") == "currency_updated":
        async with AsyncSessionLocal() as db:
            stmt = select(CurrencyRate).where(
                CurrencyRate.code == data["code"]
            )
            result = await db.execute(stmt)
            rate = result.scalar_one_or_none()

            if rate:
                rate.value = data["value"]
                rate.updated_at = datetime.utcnow()
            else:
                rate = CurrencyRate(
                    code=data["code"],
                    value=data["value"],
                )
                db.add(rate)

            await db.commit()
