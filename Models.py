from sqlalchemy import FLOAT, Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, null, true
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql.expression import func
from datetime import datetime
from sqlalchemy import Date


from Database import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    firstName = Column(String(200), nullable=False)
    lastName = Column(String(200), nullable=False)
    birthDate = Column(Date, nullable=False)
    login_id = Column(String(36), nullable=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

class Candle(Base):
    __tablename__ = 'candle'
    id = Column(Integer, primary_key=True)
    openTime = Column(Date, nullable=False)
    closeTime = Column(Date, nullable=False)

class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False)
    information = Column(String, nullable=False)

class Signal(Base):
    __tablename__ = 'signal'
    id = Column(Integer, primary_key=True)
    information = Column(String, nullable=False)
    possition = Column(Boolean, nullable=False)
    data = Column(DateTime, nullable=False)
    stopLoss = Column(FLOAT, nullable=False)
    targetPrice = Column(FLOAT, nullable=False)
    openPrice = Column(FLOAT, nullable=False)
    closed = Column(Boolean, default=False)
    percentage = Column(FLOAT, nullable=True)
    closeDate = Column(DateTime, nullable=True)
    targetSMA = Column(Boolean, nullable=False, default=False)
    