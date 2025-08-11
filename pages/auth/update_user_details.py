from streamlit_authenticator import UpdateError

from modules.auth import Auth
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def render(cls):
		try:
			if Auth.authenticator.update_user_details(st.session_state['username'], fields={
				'Form name': 'Mise à jour des informations', 'Field': 'Attribut', 'First name': 'Prénom',
				'Last name': 'Nom', 'Email': 'Adresse e-mail', 'New value': 'Nouvelle valeur',
				'Update': 'Mettre à jour'
			}):
				st.success('✅ Informations mises à jour')
		except UpdateError as e:
			st.error(e)


Page.run()
