from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean
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
    confirmed = Column(Boolean, nullable=False, default=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

    def is_confirmed(self):
        return self.confirmed