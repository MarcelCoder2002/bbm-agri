"""
Application Streamlit avec authentification et base de données
Structure modulaire avec streamlit-authenticator
"""
from abc import ABC, abstractmethod
from typing import Literal

import streamlit as st

from modules.auth import Auth
from modules.config import Config


class Page(ABC):
	@classmethod
	@abstractmethod
	def render(cls):
		"""Rend la page sélectionnée"""
		raise NotImplementedError

	@staticmethod
	def add_flash(message, __type: Literal['success', 'info', 'warning', 'error'] = 'info'):
		if not isinstance(st.session_state.get('flashes'), dict):
			st.session_state['flashes'] = {}
		if not isinstance(st.session_state['flashes'].get(__type), list):
			st.session_state['flashes'][__type] = []
		st.session_state['flashes'][__type].append(message)

	@staticmethod
	def show_flashes():
		"""Affiche les messages flash"""
		for flash_type, flash_messages in st.session_state.get('flashes', {}).items():
			for flash_message in flash_messages:
				getattr(st, flash_type)(flash_message)
		st.session_state['flashes'] = {}

	@classmethod
	def run(cls):
		"""Lance l'application"""
		cls.show_flashes()
		cls.render()
		with st.sidebar:
			if st.session_state.get('authentication_status'):
				Auth.authenticator.logout("Se déconnecter")
		# Sauvegarde automatique de la configuration à la fin
		Config.save_config()
