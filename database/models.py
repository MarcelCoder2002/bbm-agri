# database/models.py
"""Modèles de base de données avec SQLAlchemy"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config.settings import DATABASE_CONFIG

# Configuration de la base de données
engine = create_engine(DATABASE_CONFIG["url"], echo=DATABASE_CONFIG["echo"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
	"""Modèle utilisateur"""
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String(50), unique=True, index=True, nullable=False)
	email = Column(String(100), unique=True, index=True, nullable=False)
	name = Column(String(100), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)

	# Relations
	data_entries = relationship("UserData", back_populates="owner", cascade="all, delete-orphan")


class UserData(Base):
	"""Modèle des données utilisateur"""
	__tablename__ = "user_data"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(200), nullable=False)
	content = Column(Text)
	category = Column(String(50), nullable=False)
	priority = Column(String(20), default="Medium")
	status = Column(String(20), default="Active")
	tags = Column(String(500))
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

	# Relations
	owner = relationship("User", back_populates="data_entries")


def init_database():
	"""Initialise la base de données"""
	Base.metadata.create_all(bind=engine)
