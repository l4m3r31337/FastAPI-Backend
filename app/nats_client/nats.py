import json
import logging
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
import nats as nats_py
from nats.aio.client import Client as NATS
from config import settings

nc = NATS()

logger = logging.getLogger("nats")


async def connect_nats():
    await nc.connect(servers=[settings.NATS_URL])
    logger.info("Connected to NATS")


async def publish_event(subject: str, payload: dict):
    await nc.publish(subject, json.dumps(payload).encode())


async def subscribe_to_currency_updates(handler):
    await nc.subscribe("currency.updates", cb=handler)


async def subscribe_for_logging():
    async def log_handler(msg: Msg):
        subject = msg.subject
        data = msg.data.decode()
        logger.info(f" NATS Message - Subject: {subject}, Data: {data}")
        print(f"\n NATS Notification:")
        print(f"   Subject: {subject}")
        print(f"   Message: {data}")
        print("-" * 50)
    
    await nc.subscribe("currency.updates", cb=log_handler)
    await nc.subscribe(">", cb=log_handler)