from typing import Callable

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from streamlit import session_state as ss
from streamlit.connections.sql_connection import SQLConnection
from streamlit.delta_generator import DeltaGenerator

from utils.crud import many
from utils.crud.filters import ExistingData
from utils.crud.input_fields import InputFields
from utils.crud.lib import get_pretty_name, log, set_state


class UpdateRow:
	def __init__(
			self,
			conn: SQLConnection,
			Model: type[DeclarativeBase],
			row_id: int,
			default_values: dict | None = None,
			update_show_many: bool = False,
			callback: Callable | None = None,
	) -> None:
		self.conn = conn
		self.Model = Model
		self.row_id = row_id
		self.default_values = default_values or {}
		self.update_show_many = update_show_many
		self.callback = callback

		set_state("stsql_updated", 0)

		with conn.session as s:
			self.row = s.get_one(Model, row_id)
			self.existing_data = ExistingData(s, Model, self.default_values, self.row)

		self.input_fields = InputFields(
			Model, "update", self.default_values, self.existing_data
		)

	def get_updates(self):
		cols = self.Model.__table__.columns
		updated = {}

		for col in cols:
			col_name = col.description
			assert col_name is not None
			col_value = getattr(self.row, col_name)
			default_value = self.default_values.get(col_name)

			if default_value:
				input_value = col_value
			else:
				input_value = self.input_fields.get_input_value(col, col_value)

			updated[col_name] = input_value

		return updated

	def save(self, updated: dict):
		with self.conn.session as s:
			try:
				stmt = select(self.Model).where(
					self.Model.__table__.columns.id == updated["id"]
				)
				row = s.execute(stmt).scalar_one()
				for k, v in updated.items():
					setattr(row, k, v)

				s.add(row)
				s.commit()
				self.callback(row) if self.callback else None
				log("UPDATE", self.Model.__tablename__, row)
				return True, f"{row} a été mis à jour avec succès"
			except Exception as e:
				updated_list = [f"{k}: {v}" for k, v in updated.items()]
				updated_str = ", ".join(updated_list)
				log("UPDATE", self.Model.__tablename__, updated_str)
				return False, str(e)

	def show(self):
		pretty_name = get_pretty_name(self.Model.__crud_tablename__)
		st.subheader(pretty_name)
		with st.form(f"update_model_form_{pretty_name}", border=False):
			updated = self.get_updates()
			update_btn = st.form_submit_button("Enregistrer", type="primary")

		if self.update_show_many:
			many.show_rels(self.conn, self.Model, self.row_id)

		if update_btn:
			ss.stsql_updated += 1
			return self.save(updated)
		return None, None

	def show_dialog(self):
		pretty_name = get_pretty_name(self.Model.__crud_tablename__)

		@st.dialog(f"Modification de {pretty_name}", width="large")  # pyright: ignore
		def wrap_show_update():
			set_state("stsql_updated", 0)
			updated_before = ss.stsql_updated
			status, msg = self.show()

			ss.stsql_update_ok = status
			ss.stsql_update_message = msg
			ss.stsql_opened = True

			if ss.stsql_updated > updated_before:
				st.rerun()

		wrap_show_update()


def action_btns(container: DeltaGenerator, qtty_selected: int, opened: bool):
	set_state("stsql_action", "")
	disabled_add = qtty_selected > 0
	disabled_edit = qtty_selected != 1
	disabled_delete = qtty_selected == 0

	with container:
		add_col, edit_col, del_col, _empty_col = st.columns([1, 1, 1, 6])

		add_btn = add_col.button(
			"",
			help="Ajouter",
			icon=":material/add:",
			type="secondary",
			disabled=disabled_add,
			use_container_width=True,
		)

		edit_btn = edit_col.button(
			"",
			help="Modifier",
			icon=":material/edit:",
			type="secondary",
			disabled=disabled_edit,
			use_container_width=True,
		)

		del_btn = del_col.button(
			"",
			help="Supprimer",
			icon=":material/delete:",
			type="primary",
			disabled=disabled_delete,
			use_container_width=True,
		)

		if opened:
			return None
		if add_btn:
			return "add"
		if edit_btn:
			return "edit"
		if del_btn:
			return "delete"

		return None
