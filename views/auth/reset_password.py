from streamlit_authenticator import CredentialsError, ResetError

from page import Page, st


class ResetPasswordPage(Page):
	def render(self):
		try:
			if self.authenticator.reset_password(st.session_state['username'], fields={
				'Form name': 'Réinitialiser le mot de passe', 'Current password': 'Mot de passe actuel',
				'New password': 'Nouveau mot de passe', 'Repeat password': 'Confirmer le nouveau mot de passe',
				'Reset': 'Réinitialiser'
			}):
				st.success('✅ Mot de passe modifié avec succès')
				self.save_config()
		except (CredentialsError, ResetError) as e:
			st.error(e)


page = ResetPasswordPage()
page.run()
