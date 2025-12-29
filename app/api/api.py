from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from datetime import datetime

from app.db.db import get_db, AsyncSessionLocal
from app.models.models import CurrencyRate
from app.nats.nats import publish_event
from app.ws.ws import manager
from app.tasks.task import fetch_rates

router = APIRouter()



class CurrencyCreate(BaseModel):
    code: str
    value: float


class CurrencyUpdate(BaseModel):
    value: float



@router.get("/items", summary="Получить список валют")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CurrencyRate))
    return result.scalars().all()


@router.get("/items/{item_id}", summary="Получить валюту по ID")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CurrencyRate).where(CurrencyRate.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post(
    "/items",
    status_code=status.HTTP_201_CREATED,
    summary="Создать валюту вручную",
)
async def create_item(
    data: CurrencyCreate,
    db: AsyncSession = Depends(get_db),
):
    item = CurrencyRate(
        code=data.code,
        value=data.value,
        updated_at=datetime.utcnow(),
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    event = {
        "type": "item_created",
        "id": item.id,
        "code": item.code,
        "value": item.value,
    }

    await publish_event("currency.updates", event)
    await manager.broadcast(event)

    return item


@router.patch(
    "/items/{item_id}",
    summary="Обновить курс валюты",
)
async def update_item(
    item_id: int,
    data: CurrencyUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CurrencyRate).where(CurrencyRate.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.value = data.value
    item.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)

    event = {
        "type": "item_updated",
        "id": item.id,
        "code": item.code,
        "value": item.value,
    }

    await publish_event("currency.updates", event)
    await manager.broadcast(event)

    return item


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить валюту",
)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CurrencyRate).where(CurrencyRate.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()

    event = {
        "type": "item_deleted",
        "id": item_id,
    }

    await publish_event("currency.updates", event)
    await manager.broadcast(event)


@router.post(
    "/tasks/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Принудительно запустить парсер ЦБ РФ",
)
async def run_background_task():
    async with AsyncSessionLocal() as db:
        await fetch_rates(db)

    return {
        "status": "ok",
        "message": "Currency rates fetched manually",
    }
