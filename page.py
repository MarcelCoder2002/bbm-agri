"""
Application Streamlit avec authentification et base de données
Structure modulaire avec streamlit-authenticator
"""
from abc import ABC, abstractmethod

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from config.settings import APP_CONFIG
from database.models import init_database
# Import des modules locaux
from database.operations import DatabaseManager

# Configuration de la page
st.set_page_config(**APP_CONFIG)


class Page(ABC):
	def __init__(self):
		self.config = None
		self.config_file = 'config.yaml'
		self.db_manager = DatabaseManager()
		self.authenticator = None
		self.load_config()
		self.setup_authenticator()

	def load_config(self):
		"""Charge la configuration d'authentification"""
		try:
			with open(self.config_file, 'r', encoding='utf-8') as file:
				self.config = yaml.load(file, Loader=SafeLoader)
		except FileNotFoundError:
			# Configuration par défaut si le fichier n'existe pas
			self.config = {
				'credentials': {
					'usernames': {
						'admin': {
							'email': 'admin@example.com',
							'name': 'Administrateur',
							'password': 'admin123'  # Sera hashé automatiquement
						}
					}
				},
				'cookie': {
					'name': 'streamlit_auth_cookie',
					'key': 'random_signature_key_123456789',
					'expiry_days': 30
				},
				'pre-authorized': {
					'emails': []
				}
			}
			self.save_config()

	def save_config(self):
		"""Sauvegarde la configuration"""
		with open(self.config_file, 'w', encoding='utf-8') as file:
			yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)

	def setup_authenticator(self):
		"""Configure l'authentificateur"""
		# Hash des mots de passe en plain text
		stauth.Hasher.hash_passwords(self.config['credentials'])

		# Création de l'authentificateur
		self.authenticator = stauth.Authenticate(
			self.config['credentials'],
			self.config['cookie']['name'],
			self.config['cookie']['key'],
			self.config['cookie']['expiry_days']
		)

	@abstractmethod
	def render(self):
		"""Rend la page sélectionnée"""
		raise NotImplementedError

	def run(self):
		"""Lance l'application"""
		init_database()
		self.render()
		with st.sidebar:
			if st.session_state.get('authentication_status'):
				self.authenticator.logout("Se déconnecter")
		# Sauvegarde automatique de la configuration à la fin
		self.save_config()
