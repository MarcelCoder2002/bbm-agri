"""
Application Streamlit avec authentification et base de données
Structure modulaire avec streamlit-authenticator
"""

import streamlit as st

# Import des modules locaux
from config.settings import APP_CONFIG, AUTH_ACTIONS

# Configuration de la page
st.set_page_config(**APP_CONFIG)

pages = {
	'Compte': []
}
authentication_status = st.session_state.get('authentication_status')

if not authentication_status:
	if 'login' in AUTH_ACTIONS:
		pages['Compte'].append(st.Page('views/auth/login.py', title='Connexion', icon=":material/login:"))
	if 'register' in AUTH_ACTIONS:
		pages['Compte'].append(st.Page('views/auth/register.py', title='Inscription', icon=":material/app_registration:"))
	if 'forgot_password' in AUTH_ACTIONS:
		pages['Compte'].append(st.Page('views/auth/forgot_password.py', title='Mot de passe oublié', icon=":material/password:"))

if authentication_status:
	if 'reset_password' in AUTH_ACTIONS:
		pages['Compte'].append(st.Page('./views/auth/reset_password.py', title='Réinitialiser le mot de passe', icon=":material/password:"))
	if 'update_user_details' in AUTH_ACTIONS:
		pages['Compte'].append(st.Page('./views/auth/update_user_details.py', title='Mise à jour des informations', icon=":material/account_circle:"))

if __name__ == '__main__':
	app = st.navigation(pages)
	app.run()
