from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dailyfin.core.connection import SessionLocal
from dailyfin.backend.models import NewsArticle
from fastapi.responses import JSONResponse
from datetime import date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/api/news", response_class=JSONResponse)
def get_news(date_filter: date = None, db: Session = Depends(get_db)):
    query = db.query(NewsArticle)
    if date_filter:
        query = query.filter(NewsArticle.input_date.like(f"{date_filter}%"))
    results = query.order_by(NewsArticle.date, NewsArticle.category).all()
    news_list = [{
        "input_date": news.input_date,
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "source": news.source,
        "date": news.date,
        "link": news.link,
        "category": news.category,
        "aiSummary" : news.aiSummary

    } for news in results]
    return news_list
