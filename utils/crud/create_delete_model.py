from typing import Callable

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from streamlit import session_state as ss
from streamlit.connections.sql_connection import SQLConnection

from utils.crud.filters import ExistingData
from utils.crud.input_fields import InputFields
from utils.crud.lib import get_pretty_name, log, set_state

class CreateRow:
    def __init__(
        self,
        conn: SQLConnection,
        Model: type[DeclarativeBase],
        default_values: dict | None = None,
        base_key: str = "create",
        create_show_many: bool = False,
        callback: Callable | None = None,
    ) -> None:
        self.conn = conn
        self.Model = Model

        self.default_values = default_values or {}
        self.base_key = base_key
        self.create_show_many = create_show_many
        self.callback = callback

        set_state("stsql_updated", 0)

        with conn.session as s:
            self.existing_data = ExistingData(s, Model, self.default_values)
            self.input_fields = InputFields(
                Model, base_key, self.default_values, self.existing_data
            )

    def get_fields(self):
        cols = self.Model.__table__.columns
        created = {}
        for col in cols:
            col_name = col.description
            assert col_name is not None
            default_value = self.default_values.get(col_name)

            if default_value:
                input_value = default_value
            else:
                input_value = self.input_fields.get_input_value(col, None)

            created[col_name] = input_value

        return created

    def show(self, pretty_name: str):
        st.subheader(pretty_name)

        with st.form(f"create_model_form_{pretty_name}_{self.base_key}", border=False):
            created = self.get_fields()
            create_btn = st.form_submit_button("Enregistrer", type="primary")

        if self.create_show_many:
            #show_rels(self.conn, self.Model, None)
            pass

        if create_btn:
            row = self.Model(**created)
            with self.conn.session as s:
                try:
                    s.add(row)
                    s.commit()
                    self.callback(row) if self.callback else None
                    ss.stsql_updated += 1
                    log("CREATE", self.Model.__tablename__, row)
                    return True, f"{row} a été créé avec succès"
                except Exception as e:
                    ss.stsql_updated += 1
                    log("CREATE", self.Model.__tablename__, row, success=False)
                    return False, str(e)
        else:
            return None, None

    def show_dialog(self):
        pretty_name = get_pretty_name(self.Model.__crud_tablename__)

        @st.dialog(f"Création de {pretty_name}", width="large")  # pyright: ignore
        def wrap_show_update():
            set_state("stsql_updated", 0)
            updated_before = ss.stsql_updated
            status, msg = self.show(pretty_name)

            ss.stsql_update_ok = status
            ss.stsql_update_message = msg
            ss.stsql_opened = True

            if ss.stsql_updated > updated_before:
                st.rerun()

        wrap_show_update()


class DeleteRows:
    def __init__(
        self,
        conn: SQLConnection,
        Model: type[DeclarativeBase],
        rows_id: list[int],
        base_key: str = "stsql_delete_rows",
        callback: Callable | None = None,
    ) -> None:
        self.conn = conn
        self.Model = Model
        self.rows_id = rows_id
        self.base_key = base_key
        self.callback = callback

    def get_rows_str(_self, rows_id: list[int]):
        id_col = _self.Model.__table__.columns.get("id")
        assert id_col is not None
        stmt = select(_self.Model).where(id_col.in_(rows_id))

        with _self.conn.session as s:
            rows = s.execute(stmt).scalars()
            rows_str = [str(row) for row in rows]

        return rows_str

    def show(self, pretty_name):
        st.subheader("Supprimer les éléments ci-dessous ?")

        rows_str = self.get_rows_str(self.rows_id)
        st.dataframe({pretty_name: rows_str}, hide_index=True)

        btn = st.button("Supprimer", key=self.base_key)
        if btn:
            id_col = self.Model.__table__.columns.get("id")
            assert id_col is not None
            lancs = []
            with self.conn.session as s:
                try:
                    for row_id in self.rows_id:
                        lanc = s.get(self.Model, row_id)
                        lancs.append(str(lanc))
                        s.delete(lanc)

                    s.commit()
                    ss.stsql_updated += 1
                    qtty = len(self.rows_id)
                    lancs_str = ", ".join(lancs)
                    log("DELETE", self.Model.__tablename__, lancs_str)
                    self.callback(self.rows_id) if self.callback else None
                    return True, f"{qtty} enregistrements supprimés avec succès"
                except Exception as e:
                    ss.stsql_updated += 1
                    log("DELETE", self.Model.__tablename__, "")
                    return False, str(e)
        else:
            return None, None

    def show_dialog(self):
        pretty_name = get_pretty_name(self.Model.__crud_tablename__)

        @st.dialog(f"Suppression de {pretty_name}", width="large")  # pyright: ignore
        def wrap_show_update():
            set_state("stsql_updated", 0)
            updated_before = ss.stsql_updated
            status, msg = self.show(pretty_name)

            ss.stsql_update_ok = status
            ss.stsql_update_message = msg
            ss.stsql_opened = True

            if ss.stsql_updated > updated_before:
                st.rerun()

        wrap_show_update()
