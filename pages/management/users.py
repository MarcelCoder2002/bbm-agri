from sqlalchemy import select

from modules.auth import Auth
from modules.db import *
from modules.page import Page as BasePage
from utils.crud.sql_iu import SqlUi


class Page(BasePage):
	@classmethod
	def render(cls):
		ui = SqlUi(
			DB.connection,
			select(
				User.id,
				User.first_name.label("Prénom"),
				User.last_name.label("Nom"),
				User.email.label("E-mail"),
				User.roles.label("Rôles"),
				User.created_at.label("Date d'inscription")
			),
			User,
			read_use_container_width=True,
			create_callback=cls._create_callback,
			update_callback=cls._update_callback,
			delete_callback=cls._delete_callback
		)

	@staticmethod
	def _create_callback(user):
		Auth.add_users([user])

	@staticmethod
	def _update_callback(user):
		Auth.update_users([user])

	@staticmethod
	def _delete_callback(users_id: list[int]):
		Auth.remove_users(users_id, by_id=True)


Page.run()
