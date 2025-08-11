from sqlalchemy import select

from modules.db import *
from modules.page import Page as BasePage
from utils.crud.sql_iu import show_sql_ui


class Page(BasePage):
	@classmethod
	def render(cls):
		show_sql_ui(DB.connection, select(
			SalesDepartment.id,
			SalesDepartment.name.label("Nom"),
		), SalesDepartment, read_use_container_width=True)


Page.run()
