from streamlit_authenticator import UpdateError

from page import Page, st


class UpdateUserDetailsPage(Page):
	def render(self):
		try:
			if self.authenticator.update_user_details(st.session_state['username'], fields={
				'Form name': 'Mise à jour des informations', 'Field': 'Attribut', 'First name': 'Prénom',
				'Last name': 'Nom', 'Email': 'Adresse e-mail', 'New value': 'Nouvelle valeur',
				'Update': 'Mettre à jour'
			}):
				st.success('✅ Informations mises à jour')
				self.save_config()
		except UpdateError as e:
			st.error(e)


page = UpdateUserDetailsPage()
page.run()
