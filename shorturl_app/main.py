import string
import random

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import URLItem

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:8001",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLCreate(BaseModel):
    url: HttpUrl


class URLUpdate(BaseModel):
    url: HttpUrl


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_short_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@app.post("/shorten")
def shorten_url(item: URLCreate, db: Session = Depends(get_db)):
    # Генерируем уникальный short_id
    for _ in range(10):
        short_id = generate_short_id()
        existing = db.query(URLItem).filter(URLItem.short_id == short_id).first()
        if not existing:
            new_item = URLItem(short_id=short_id, full_url=str(item.url))
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            return {"short_url": f"http://localhost:8001/{short_id}"}
    raise HTTPException(status_code=500, detail="Не удалось сгенерировать короткую ссылку")


@app.get("/all")
def get_all_links(db: Session = Depends(get_db)):
    """Получение всех сокращенных ссылок"""
    urls = db.query(URLItem).all()
    return [
        {
            "short_id": item.short_id,
            "full_url": item.full_url,
        }
        for item in urls
    ]


@app.get("/{short_id}")
def redirect_to_full(short_id: str, db: Session = Depends(get_db)):
    """Перенаправление на полную ссылку"""
    url_item = db.query(URLItem).filter(URLItem.short_id == short_id).first()
    if not url_item:
        raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")
    return RedirectResponse(url=url_item.full_url)


@app.get("/stats/{short_id}")
def get_stats(short_id: str, db: Session = Depends(get_db)):
    """Получение информации об объекте сокращенных ссылок"""
    url_item = db.query(URLItem).filter(URLItem.short_id == short_id).first()
    if not url_item:
        raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")
    return {
        "short_id": url_item.short_id,
        "full_url": url_item.full_url
    }


@app.put("/{short_id}")
def update_link(short_id: str, update_data: URLUpdate, db: Session = Depends(get_db)):
    """Изменение коротких ссылок"""
    url_item = db.query(URLItem).filter(URLItem.short_id == short_id).first()
    if not url_item:
        raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")
    url_item.full_url = str(update_data.url)
    db.commit()
    db.refresh(url_item)
    return {
        "short_id": url_item.short_id,
        "full_url": url_item.full_url,
    }


@app.delete("/{short_id}")
def delete_link(short_id: str, db: Session = Depends(get_db)):
    """Удаление ссылок"""
    url_item = db.query(URLItem).filter(URLItem.short_id == short_id).first()
    if not url_item:
        raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")
    db.delete(url_item)
    db.commit()
    return {"detail": "Ссылка успешно удалена"}
