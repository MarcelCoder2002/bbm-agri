from streamlit_authenticator import ForgotError

from modules.auth import Auth
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def render(cls):
		try:
			(username_of_forgotten_password,
			 email_of_forgotten_password,
			 new_random_password) = Auth.authenticator.forgot_password(
				fields={'Form name': 'Mot de passe oublié', 'Username': 'Nom d\'utilisateur', 'Submit': 'Soumettre',
				        'Dialog name': 'Code de vérification', 'Code': 'Code',
				        'Error': 'Le code est incorrect'
				        })

			if username_of_forgotten_password:
				st.success('🔑 Nouveau mot de passe généré')
				st.info(f'Nouveau mot de passe: `{new_random_password}`')
			elif username_of_forgotten_password is False:
				st.error('❌ Nom d\'utilisateur non trouvé')
		except ForgotError as e:
			st.error(e)


Page.run()
