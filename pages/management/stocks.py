from sqlalchemy import select

from modules.db import *
from modules.page import Page as BasePage
from utils.crud.sql_iu import show_sql_ui


class Page(BasePage):
	@classmethod
	def render(cls):
		show_sql_ui(DB.connection, select(
			Stock.id,
			Product.name.label("Produit"),
			Stock.quantity.label("Quantité")
		).join(
			Product, Stock.id_product == Product.id
		), Stock, read_use_container_width=True)


Page.run()
