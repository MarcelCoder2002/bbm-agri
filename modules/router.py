import streamlit as st

from config.settings import AUTH_ACTIONS


class Router:
	pages = None
	need_reload = True
	authentication_status = None
	last_status = None

	@classmethod
	def load_authentication_status(cls):
		authentication_status = st.session_state.get('authentication_status')
		if authentication_status != cls.authentication_status:
			cls.need_reload = True
			cls.authentication_status = authentication_status
		return authentication_status

	@classmethod
	def load_routes(cls):
		if cls.pages is None:
			if cls.authentication_status:
				cls.pages = {}
			else:
				cls.pages = []

		if cls.need_reload:
			cls.need_reload = False
		elif len(cls.pages) > 0:
			return

		empty_pages = len(cls.pages) == 0

		if not cls.authentication_status and (cls.last_status != 'not_authenticated' or empty_pages):
			cls.pages = []
			cls.last_status = 'not_authenticated'
			if 'login' in AUTH_ACTIONS:
				cls.pages.append(st.Page('pages/auth/login.py', title='Connexion', icon=":material/login:"))
			if 'register' in AUTH_ACTIONS:
				cls.pages.append(
					st.Page('pages/auth/register.py', title='Inscription', icon=":material/app_registration:"))
			if 'forgot_password' in AUTH_ACTIONS:
				cls.pages.append(
					st.Page('pages/auth/forgot_password.py', title='Mot de passe oublié', icon=":material/password:"))

		if cls.authentication_status and (cls.last_status != 'authenticated' or empty_pages):
			dashboard = "Tableau de bord"
			account = "Compte"
			stock_management = "Gestion des stocks"
			global_management = "Gestion globale"

			cls.pages = {
				dashboard: [],
				global_management: [],
				stock_management: []
			}
			cls.last_status = 'authenticated'
			cls.pages[dashboard].append(
				st.Page('pages/dashboard/products.py', title='Produits', icon=":material/bar_chart:"))
			cls.pages[dashboard].append(
				st.Page('pages/dashboard/stocks.py', title='Stocks', icon=":material/area_chart:")
			)

			cls.pages[global_management].append(
				st.Page('pages/management/users.py', title='Utilisateurs', icon=":material/groups:",
				        url_path="management_users"))
			cls.pages[global_management].append(
				st.Page('pages/management/sales_departments.py', title='Services commerciaux',
				        icon=":material/sell:", url_path="management_sales_departments"))
			cls.pages[global_management].append(
				st.Page('pages/management/products.py', title='Produits', icon=":material/box:",
				        url_path="management_products")
			)

			cls.pages[stock_management].append(
				st.Page('pages/management/stock_records.py', title='Enregistrements', icon=":material/inventory:",
				        url_path="management_stock_records")
			)
			cls.pages[stock_management].append(
				st.Page('pages/management/stocks.py', title='Stocks', icon=":material/warehouse:",
				        url_path="management_stocks")
			)
			cls.pages[stock_management].append(
				st.Page('pages/management/import_stocks.py', title='Importation de stocks', icon=":material/list:",
				        url_path="management_import_stocks")
			)

			if any(map(lambda p: p in AUTH_ACTIONS, ['reset_password', 'update_user_details'])):
				cls.pages[account] = []
			if 'reset_password' in AUTH_ACTIONS:
				cls.pages[account].append(st.Page('pages/auth/reset_password.py', title='Réinitialiser le mot de passe',
				                                  icon=":material/password:"))
			if 'update_user_details' in AUTH_ACTIONS:
				cls.pages[account].append(
					st.Page('pages/auth/update_user_details.py', title='Mise à jour des informations',
					        icon=":material/account_circle:"))

	@classmethod
	def run(cls):
		if cls.pages:
			page = st.navigation(cls.pages)
			page.run()
