import os

from yaml import dump, load, SafeLoader


class Config:
	config_file = 'config.yaml'
	config = None

	@classmethod
	def save_config(cls):
		"""Sauvegarde la configuration"""
		if cls.config:
			if os.getenv('STREAMLIT_ENV') == 'production':
				return
			with open(cls.config_file, 'w', encoding='utf-8') as file:
				dump(cls.config, file, default_flow_style=False, allow_unicode=True)
		else:
			cls.load_config()

	@classmethod
	def load_config(cls):
		"""Charge la configuration"""
		# En production, utiliser les variables d'environnement
		if not cls.config and os.getenv('STREAMLIT_ENV') == 'production':
			cls.config = {
				'credentials': {
					'usernames': {}
				},
				'cookie': {
					'name': os.getenv('COOKIE_NAME', 'streamlit_auth_cookie'),
					'key': os.getenv('COOKIE_KEY', 'random_signature_key_123456789'),
					'expiry_days': int(os.getenv('COOKIE_EXPIRY_DAYS', '30'))
				},
				'pre-authorized': {
					'emails': os.getenv('PRE_AUTHORIZED_EMAILS', '').split(',') if os.getenv(
						'PRE_AUTHORIZED_EMAILS') else []
				}
			}
			return

		# En local, utiliser le fichier
		try:
			with open(cls.config_file, 'r', encoding='utf-8') as file:
				cls.config = load(file, Loader=SafeLoader)
		except FileNotFoundError:
			cls.config = {
				'credentials': {'usernames': {}},
				'cookie': {
					'name': 'streamlit_auth_cookie',
					'key': 'random_signature_key_123456789',
					'expiry_days': 30
				},
				'pre-authorized': {'emails': []}
			}
			cls.save_config()
