from datetime import date
import re
from functools import partial
from typing import Tuple, Optional

import pandas as pd

from database.repositories import SalesDepartmentRepository, ProductRepository, StockRecordRepository
from modules.db import *
from modules.page import Page as BasePage
from utils.crud.ie import render_import_export_interface, DynamicImportExport
from utils.data import get_attr


class Page(BasePage):
	id_stock_record = None

	@classmethod
	def render(cls):
		sd = st.date_input("Date de début", datetime.now() - timedelta(days=6))
		ed = st.date_input("Date de fin")
		s_d = st.selectbox("Service commercial", SalesDepartmentRepository.find_all())

		render_import_export_interface(
			DynamicImportExport(DB.connection, Stock, process_imported_dataframe=partial(cls.process_dataframe, (sd, ed, s_d))), can_export=False)

	@classmethod
	def parse_emballage(cls, emballage: str) -> Tuple[Optional[float], Optional[str]]:
		# Nettoyer l'emballage (supprimer espaces en trop)
		emballage = emballage.strip()

		# Pattern pour capturer nombre + unité
		pattern = r'^(\d+(?:\.\d+)?)\s*([A-Za-z]+)$'
		match = re.match(pattern, emballage)

		if match:
			quantity = float(match.group(1))
			unit = match.group(2).upper()
			return quantity, unit.lower()
		else:
			# Si le pattern ne match pas, essayer de gérer les cas spéciaux
			print(f"Attention: Format d'emballage non reconnu: '{emballage}'")
			return None, emballage

	@classmethod
	def process_dataframe(cls, params, df: pd.DataFrame) -> pd.DataFrame:
		# Vérifier les colonnes attendues
		expected_columns = ['NOM COMMERCIAL', 'EMBALLAGES', 'STOK']
		if not all(col in df.columns for col in expected_columns):
			print(f"Colonnes manquantes. Colonnes trouvées: {list(df.columns)}")
			return pd.DataFrame()

		# Créer le nouveau DataFrame
		processed_data = []
		if params[2] is None:
			raise ValueError("Le service commercial est obligatoire")

		with DB.connection.session as session:
			try:
				stock_record_id = cls.get_stock_record_id(*params, session=session)

				for index, row in df.iterrows():
					name = row['NOM COMMERCIAL'].strip()
					emballage = str(row['EMBALLAGES']).strip()
					stock = int(row['STOK'])

					# Parser l'emballage
					quantity, unit = cls.parse_emballage(emballage)

					processed_data.append({
						'id_product': cls.get_product_id(name, quantity, unit, session=session),
						'id_stock_record': stock_record_id,
						'quantity': stock
					})
			except Exception as e:
				session.rollback()
				raise e

		return pd.DataFrame(processed_data)

	@classmethod
	def get_stock_record_id(cls, start_date: date, end_date: date, sales_department: SalesDepartment, session=None):
		stock_record = StockRecordRepository.query(session=session).filter(StockRecord.start_date == start_date, StockRecord.end_date == end_date,
		                                           StockRecord.id_sales_department == sales_department.id).first()
		if stock_record:
			return get_attr(stock_record, 'id')
		else:
			stock_record = StockRecordRepository.create(
				{
					'id_sales_department': sales_department.id,
					'start_date': start_date,
					'end_date': end_date
				}, session=session
			)
			return get_attr(stock_record, 'id')

	@classmethod
	def get_product_id(cls, name: str, quantity: float, unit: str, session=None):
		product = ProductRepository.query(session=session).filter(Product.name.like(name), Product.quantity == quantity, Product.unit == unit).first()
		if product:
			return get_attr(product, 'id')
		else:
			product = ProductRepository.create(
				{
					'name': name,
					'quantity': quantity,
					'unit': unit
				}, session=session
			)
			return get_attr(product, 'id')


Page.run()
