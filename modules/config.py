from yaml import dump, load, SafeLoader


class Config:
	config_file = '/app/config.yaml'
	config = None

	@classmethod
	def save_config(cls):
		"""Sauvegarde la configuration"""
		if cls.config:
			with open(cls.config_file, 'w', encoding='utf-8') as file:
				dump(cls.config, file, default_flow_style=False, allow_unicode=True)
		else:
			cls.load_config()

	@classmethod
	def load_config(cls):
		"""Charge la configuration"""
		try:
			with open(cls.config_file, 'r', encoding='utf-8') as file:
				cls.config = load(file, Loader=SafeLoader)
		except FileNotFoundError:
			# Configuration par défaut si le fichier n'existe pas
			cls.config = {
				'credentials': {
					'usernames': {}
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
			cls.save_config()
