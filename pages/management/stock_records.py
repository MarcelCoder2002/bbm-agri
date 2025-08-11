from sqlalchemy import select

from modules.db import *
from modules.page import Page as BasePage
from utils.crud.sql_iu import show_sql_ui


class Page(BasePage):
	@classmethod
	def render(cls):
		show_sql_ui(DB.connection, select(
			StockRecord.id,
			SalesDepartment.name.label("Service commercial"),
			StockRecord.start_date.label("Date de début"),
			StockRecord.end_date.label("Date de fin"),
			StockRecord.created_at.label("Date d'enregistrement")
		).join(
			SalesDepartment, StockRecord.id_sales_department == SalesDepartment.id
		), StockRecord, read_use_container_width=True)


Page.run()
