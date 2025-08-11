from streamlit_authenticator import RegisterError

from database.repositories import UserRepository
from modules.auth import Auth
from modules.config import Config
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def sync_user_to_db(cls, username):
		"""Synchronise un nouvel utilisateur avec la base de données"""
		try:
			Config.load_config()
			user = Config.config['credentials']['usernames'][username]
			UserRepository.create({
				'email': user['email'],
				'first_name': user['first_name'],
				'last_name': user['last_name'],
				'password': user['password'],
				'roles': user['roles']
			})
		except Exception as e:
			st.error(f"Erreur lors de la synchronisation: {e}")

	@classmethod
	def render(cls):
		try:
			(email_of_registered_user,
			 username_of_registered_user,
			 name_of_registered_user) = Auth.authenticator.register_user(merge_username_email=True, captcha=False,
			                                                            password_hint=False, fields={
					'Form name': 'Inscription', 'First name': 'Prénom',
					'Last name': 'Nom', 'Email': 'Adresse e-mail', 'Username': 'Nom d\'utilisateur',
					'Password': 'Mot de passe', 'Repeat password': 'Confirmer le mot de passe',
					'Register': 'S\'inscrire',
					'Dialog name': 'Code de vérification', 'Code': 'Code', 'Submit': 'Soumettre',
					'Error': 'Le code est incorrect'})

			if email_of_registered_user:
				Config.save_config()
				cls.sync_user_to_db(username_of_registered_user)
				cls.add_flash("✅ Utilisateur enregistré avec succès", 'success')
				st.switch_page('pages/auth/login.py')

		except RegisterError as e:
			st.error(e)


Page.run()
