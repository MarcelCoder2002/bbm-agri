from datetime import timedelta
from typing import Any

import streamlit as st

from database.models import *


class DB:
	connection = st.connection("sql")
	Base.metadata.create_all(connection.engine)

	@classmethod
	def session_call(cls, callback, params=None, catch_exception=False, show_error=True, session=None):
		if session:
			return callback(session, **(params if params else {}))
		else:
			with cls.connection.session as session:
				if catch_exception:
					try:
						return callback(session, **(params if params else {}))
					except Exception as e:
						session.rollback()
						if show_error:
							st.error(e)
						return None
				else:
					return callback(session, **(params if params else {}))

	@classmethod
	def execute(cls, sql: str, catch_exception=False, show_error=True, session=None, **kwargs):
		return cls.session_call(lambda s: s.execute(sql, **kwargs), catch_exception, show_error, session=session)

	@classmethod
	def query(cls, *entities, catch_exception=False, show_error=True, session=None, **kwargs):
		return cls.session_call(lambda s: s.query(*entities, **kwargs), catch_exception, show_error, session=session)

	@classmethod
	def query_dataframe(
			cls,
			sql: str,
			*,
			show_spinner: bool | str = "Chargement des données en cours...",
			ttl: float | int | timedelta | None = None,
			index_col: str | list[str] | None = None,
			chunksize: int | None = None,
			params: Any | None = None,
			**kwargs: Any
	):
		return cls.connection.query(
			sql,
			show_spinner=show_spinner, ttl=ttl, index_col=index_col, chunksize=chunksize,
			params=params, **kwargs
		)
