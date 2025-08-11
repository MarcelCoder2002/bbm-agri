from streamlit_authenticator import CredentialsError, ResetError

from modules.auth import Auth
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def render(cls):
		try:
			if Auth.authenticator.reset_password(st.session_state['username'], fields={
				'Form name': 'Réinitialiser le mot de passe', 'Current password': 'Mot de passe actuel',
				'New password': 'Nouveau mot de passe', 'Repeat password': 'Confirmer le nouveau mot de passe',
				'Reset': 'Réinitialiser'
			}):
				st.success('✅ Mot de passe modifié avec succès')
		except (CredentialsError, ResetError) as e:
			st.error(e)


Page.run()
