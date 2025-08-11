from datetime import date
from decimal import Decimal

import streamlit as st
from sqlalchemy import Numeric
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import KeyedColumnElement
from sqlalchemy.types import Enum as SQLEnum

from utils.crud.filters import ExistingData


class InputFields:
	def __init__(
			self,
			Model: type[DeclarativeBase],
			key_prefix: str,
			default_values: dict,
			existing_data: ExistingData,
	) -> None:
		self.Model = Model
		self.key_prefix = key_prefix
		self.default_values = default_values
		self.existing_data = existing_data

	def input_fk(self, col_name: str, label, value: int | None):
		key = f"{self.key_prefix}_{col_name}"
		opts = self.existing_data.fk[col_name]

		index = next((i for i, opt in enumerate(opts) if opt.idx == value), None)
		input_value = st.selectbox(
			label,
			options=opts,
			format_func=lambda opt: opt.name,
			index=index,
			key=key,
		)
		if not input_value:
			return None
		return input_value.idx

	def input_enum(self, col_enum: SQLEnum,label, col_value=None):
		opts = col_enum.enums
		if col_value:
			index = opts.index(col_value)
		else:
			index = None
		input_value = st.selectbox(label, opts, index=index)
		return input_value

	def input_str(self, col_name: str, label, value=None):
		key = f"{self.key_prefix}_{col_name}"
		input_value = st.text_input(label, value=value, key=key)
		result = str(input_value)
		return result

	def input_numeric(self, col_name, scale: int | None, value=None):
		step = None
		if scale:
			step = 10 ** (scale * -1)

		value_float = None
		if value:
			value_float = float(value)

		input_value = st.number_input(col_name, value=value_float, step=step)

		if not input_value:
			return None

		value_dec = Decimal(str(input_value))
		if step:
			value_dec = value_dec.quantize(Decimal(str(step)))

		return value_dec

	def get_input_value(self, col: KeyedColumnElement, col_value):
		col_name = col.description
		label = col.info.get("label")
		assert col_name is not None
		assert label is not None

		if col.primary_key:
			input_value = col_value
		elif len(col.foreign_keys) > 0:
			input_value = self.input_fk(col_name, label, col_value)
		elif isinstance(col.type, SQLEnum):
			input_value = self.input_enum(col.type, label, col_value)
		elif col.type.python_type is str:
			input_value = self.input_str(col_name, label, col_value)
		elif col.type.python_type is int:
			input_value = st.number_input(label, value=col_value, step=1)
		elif col.type.python_type is float:
			input_value = st.number_input(label, value=col_value, step=0.1)
		elif isinstance(col.type, Numeric):
			scale = col.type.scale
			input_value = self.input_numeric(label, scale, col_value)
		elif col.type.python_type is date:
			input_value = st.date_input(label, value=col_value)
		elif col.type.python_type is bool:
			input_value = st.checkbox(label, value=col_value)
		else:
			input_value = None

		return input_value
