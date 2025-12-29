import json
import logging
from nats.aio.client import Client as NATS
from app.config import settings

nc = NATS()

logger = logging.getLogger("nats")


async def connect_nats():
    await nc.connect(servers=[settings.NATS_URL])
    logger.info("Connected to NATS")


async def publish_event(subject: str, payload: dict):
    await nc.publish(subject, json.dumps(payload).encode())


async def subscribe_to_currency_updates(handler):
    await nc.subscribe("currency.updates", cb=handler)
