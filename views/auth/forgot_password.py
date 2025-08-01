from streamlit_authenticator import ForgotError

from page import Page, st


class ForgotPasswordPage(Page):
	def render(self):
		try:
			(username_of_forgotten_password,
			 email_of_forgotten_password,
			 new_random_password) = self.authenticator.forgot_password(
				two_factor_auth=True,
				fields={'Form name': 'Mot de passe oublié', 'Username': 'Nom d\'utilisateur', 'Submit': 'Soumettre',
				        'Dialog name': 'Code de vérification', 'Code': 'Code',
				        'Error': 'Le code est incorrect'
				        })

			if username_of_forgotten_password:
				st.success('🔑 Nouveau mot de passe généré')
				st.info(f'Nouveau mot de passe: `{new_random_password}`')
				self.save_config()
			elif username_of_forgotten_password is False:
				st.error('❌ Nom d\'utilisateur non trouvé')
		except ForgotError as e:
			st.error(e)


page = ForgotPasswordPage()
page.run()
