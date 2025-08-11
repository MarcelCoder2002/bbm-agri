from streamlit_authenticator import LoginError

from modules.auth import Auth
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def render(cls):
		try:
			Auth.authenticator.login(
				fields={'Form name': 'Connexion', 'Username': "Nom d'utilisateur",
				        'Password': 'Mot de passe',
				        'Login': 'Se connecter'})
			if st.session_state.get('authentication_status') is False:
				st.error('❌ Nom d\'utilisateur/mot de passe incorrect')
		except LoginError as e:
			st.error(e)


Page.run()
