from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    registered_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    description = Column(String)
    city = Column(String)
    delivery_meetup = Column(Boolean)
    delivery_shipping = Column(Boolean)
    photo_ids = Column(String)  # comma-separated file_ids
    status = Column(String, default='pending')  # pending/approved/rejected
    created_at = Column(DateTime, default=datetime.utcnow)
