from streamlit_authenticator import LoginError

from page import Page, st


class LoginPage(Page):
	def render(self):
		try:
			self.authenticator.login(single_session=True,
			                         fields={'Form name': 'Connexion', 'Username': "Nom d'utilisateur",
			                                 'Password': 'Mot de passe',
			                                 'Login': 'Se connecter'})
			if st.session_state.get('authentication_status') is False:
				st.error('❌ Nom d\'utilisateur/mot de passe incorrect')
		except LoginError as e:
			st.error(e)


page = LoginPage()
page.run()
