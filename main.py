import ipaddress
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from email_notifier import send_price_alert
from models import TrackedProduct, User
from scraper import fetch_price

scheduler = AsyncIOScheduler()


async def check_all_prices():
    db = next(get_db())
    try:
        products = db.query(TrackedProduct).all()
        for product in products:
            price = await fetch_price(product.url)
            if price is not None:
                if product.current_price is not None:
                    ratio = price / product.current_price
                    if ratio < 0.5:
                        print(
                            f"\u26a0\ufe0f WARNING: Price for {product.url} dropped {((1 - ratio) * 100):.0f}% "
                            f"(from {product.current_price} to {price}). Skipping update."
                        )
                        continue
                product.current_price = price
                product.last_checked = datetime.now(timezone.utc)
                if price <= product.target_price:
                    user = db.query(User).filter(User.id == product.user_id).first()
                    user_email = user.email if user else None
                    print(
                        f"\U0001f6a8 ALERT: Price dropped for {product.url} to {price}!"
                    )
                    if user_email:
                        send_price_alert(user_email, product.url, price, product.target_price)
        db.commit()
    except Exception as e:
        print(f"Error checking prices: {e}")
        db.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(check_all_prices, "interval", minutes=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Price Tracker API", lifespan=lifespan)


class TrackRequest(BaseModel):
    url: str
    user_email: str
    target_price: float

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("URL must have a valid hostname")
        try:
            host = parsed.hostname
            if host:
                addr = ipaddress.ip_address(host)
                if addr.is_private or addr.is_loopback or addr.is_link_local:
                    raise ValueError("URL must not point to a private or local address")
        except ValueError:
            pass
        return v


class ProductResponse(BaseModel):
    id: str
    url: str
    target_price: float
    current_price: float | None
    last_checked: datetime | None

    class Config:
        from_attributes = True


@app.get("/")
def root():
    return {
        "status": "success",
        "data": {
            "title": "Price Tracker API",
            "docs": "/docs",
            "endpoints": {
                "POST /track": "Track a product URL with target price",
                "GET /products/{user_email}": "List tracked products for a user",
            },
        },
        "message": "Price Tracker API is running",
    }


@app.post("/track")
async def track_product(body: TrackRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == body.user_email).first()
        if not user:
            user = User(id=uuid4(), email=body.user_email)
            db.add(user)
            db.flush()

        current_price = await fetch_price(body.url)

        product = TrackedProduct(
            id=uuid4(),
            user_id=user.id,
            url=body.url,
            target_price=body.target_price,
            current_price=current_price,
            last_checked=datetime.now(timezone.utc) if current_price else None,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "status": "success",
            "data": {"product_id": str(product.id)},
            "message": "Product tracked successfully",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{user_email}")
def get_products(user_email: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        products = (
            db.query(TrackedProduct)
            .filter(TrackedProduct.user_id == user.id)
            .all()
        )

        return {
            "status": "success",
            "data": [
                ProductResponse(
                    id=str(p.id),
                    url=p.url,
                    target_price=p.target_price,
                    current_price=p.current_price,
                    last_checked=p.last_checked,
                ).model_dump()
                for p in products
            ],
            "message": "Products retrieved successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
