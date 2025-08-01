from streamlit_authenticator import RegisterError

from page import Page, st


class RegisterPage(Page):
	def sync_user_to_db(self, username, email, name):
		"""Synchronise un nouvel utilisateur avec la base de données"""
		try:
			self.db_manager.create_user(username, email, name)
		except Exception as e:
			st.error(f"Erreur lors de la synchronisation: {e}")

	def render(self):
		try:
			(email_of_registered_user,
			 username_of_registered_user,
			 name_of_registered_user) = self.authenticator.register_user(two_factor_auth=True, captcha=False, password_hint=False, fields={
				'Form name': 'Inscription', 'First name': 'Prénom',
				'Last name': 'Nom', 'Email': 'Adresse e-mail', 'Username': 'Nom d\'utilisateur',
				'Password': 'Mot de passe', 'Repeat password': 'Confirmer le mot de passe',
				'Register': 'S\'inscrire',
				'Dialog name': 'Code de vérification', 'Code': 'Code', 'Submit': 'Soumettre',
				'Error': 'Le code est incorrect'})

			if email_of_registered_user:
				st.success('✅ Utilisateur enregistré avec succès')
				# Synchroniser avec la base de données
				self.sync_user_to_db(username_of_registered_user,
				                     email_of_registered_user,
				                     name_of_registered_user)
				self.save_config()
		except RegisterError as e:
			st.error(e)


page = RegisterPage()
page.run()
