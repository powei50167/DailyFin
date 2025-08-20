from sqlalchemy import Column, Integer, String, Text, Date
from dailyfin.core.connection import Base



class NewsArticle(Base):
    __tablename__ = "news_list"
    __table_args__ = {'extend_existing': True}

    input_date =  Column(String(255), index=True)
    id = Column(Integer, index=True)
    title = Column(String(255), primary_key=True, nullable=False)
    link = Column(Text, nullable=False)
    content = Column(Text)
    source = Column(String(255), nullable=False)
    date = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    finance = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    aiSummary = Column(Text)