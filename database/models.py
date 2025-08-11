# database/models.py
"""Modèles de base de données avec SQLAlchemy"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship

from database.base import Base


class User(Base):
	"""Modèle utilisateur"""
	__tablename__ = "users"
	__crud_tablename__ = "utilisateurs"

	id = Column(Integer, primary_key=True, index=True, info={'label': 'ID'})
	email = Column(String(100), unique=True, index=True, nullable=False, info={'label': 'E-mail'})
	first_name = Column(String(100), nullable=False, info={'label': 'Prénom'})
	last_name = Column(String(200), nullable=False, info={'label': 'Nom'})
	password = Column(String(100), nullable=False, info={'label': 'Mot de passe'})
	roles = Column(JSON, nullable=False, info={'label': 'Rôles'})
	created_at = Column(DateTime, default=datetime.utcnow, info={'label': "Date d'enregistrement"})

	def __str__(self):
		return f"{self.first_name} {self.last_name}"


class Product(Base):
	"""Modèle produit"""
	__tablename__ = "products"
	__crud_tablename__ = "produits"

	id = Column(Integer, primary_key=True, index=True, info={'label': 'ID'})
	name = Column(String(100), nullable=False, info={'label': 'Nom'})
	quantity = Column(Numeric(10, 2), nullable=False, info={'label': 'Quantité'})
	price = Column(Numeric(10, 2), nullable=True, info={'label': 'Prix'})
	unit = Column(Enum("kg", "l"), nullable=True, info={'label': 'Unité'})
	created_at = Column(DateTime, default=datetime.utcnow, info={'label': "Date d'enregistrement"})

	def __str__(self):
		return f"{self.name} ({self.quantity} {self.unit})"


class SalesDepartment(Base):
	__tablename__ = "sales_departments"
	__crud_tablename__ = "services commerciaux"

	id = Column(Integer, primary_key=True, index=True, info={'label': 'ID'})
	name = Column(String(100), nullable=False, info={'label': 'Nom'})
	created_at = Column(DateTime, default=datetime.utcnow, info={'label': "Date d'enregistrement"})

	stock_records = relationship("StockRecord", back_populates="sales_department")

	def __str__(self):
		return f"{self.name}"


class StockRecord(Base):
	__tablename__ = "stock_records"
	__crud_tablename__ = "enregistrements de stocks"

	id = Column(Integer, primary_key=True, index=True, info={'label': 'ID'})
	id_sales_department = Column(ForeignKey("sales_departments.id"), nullable=False, info={'label': 'Service commercial'})
	start_date = Column(Date, nullable=False, info={'label': "Date de début"})
	end_date = Column(Date, nullable=False, info={'label': "Date de fin"})
	created_at = Column(DateTime, default=datetime.utcnow, info={'label': "Date d'enregistrement"})

	sales_department = relationship("SalesDepartment")
	stocks = relationship("Stock", back_populates="stock_record")

	def __str__(self):
		return f"{self.sales_department} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"


class Stock(Base):
	__tablename__ = "stocks"
	__crud_tablename__ = "stocks"

	id = Column(Integer, primary_key=True, index=True, info={'label': 'ID'})
	id_product = Column(ForeignKey("products.id"), nullable=False, info={'label': 'Produit'})
	id_stock_record = Column(ForeignKey("stock_records.id"), nullable=False, info={'label': 'Enregistrement de stock'})
	quantity = Column(Integer, nullable=False, info={'label': "Quantité"})

	product = relationship("Product")
	stock_record = relationship("StockRecord", back_populates="stocks")

	def __str__(self):
		return f"{self.product} ({self.stock_record})"
