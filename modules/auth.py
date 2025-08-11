from time import time
from typing import Sequence

import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator import LoginError

from modules.config import Config
from utils.data import get_attr, has_attr, to_dict
from utils.validator import Validator


class Auth:
	authenticator = None

	@classmethod
	def load_authenticator(cls):
		"""Charge l'authentificateur"""
		if not Config.config:
			Config.load_config()
		stauth.Hasher.hash_passwords(Config.config['credentials'])

		# Création de l'authentificateur
		cls.authenticator = stauth.Authenticate(
			Config.config['credentials'],
			Config.config['cookie']['name'],
			Config.config['cookie']['key'],
			Config.config['cookie']['expiry_days'],
			validator=Validator()
		)

		cookie = cls.authenticator.cookie_controller.get_cookie()
		if cookie and cookie.get('username') and cookie.get('exp_date', 0) > time():
			try:
				cls.authenticator.login('unrendered')
			except LoginError:
				pass

	@classmethod
	def add_users(cls, users, username_field='email'):
		Config.load_config()
		if not isinstance(users, Sequence):
			users = [users]
		for user in users:
			username = get_attr(user, username_field)
			Config.config['credentials']['usernames'][username] = to_dict(user)
		Config.save_config()

	@classmethod
	def remove_users(cls, users, username_field='email', by_id=False):
		Config.load_config()
		connected = cls.get_authenticated_user()
		if not isinstance(users, Sequence):
			users = [users]
		if by_id:
			users = list(cls.find_users_by_id(users))
		for user in users:
			username = get_attr(user, username_field)
			if connected and username == get_attr(connected, username_field):
				cls.authenticator.logout(location='unrendered')
			del Config.config['credentials']['usernames'][username]
		Config.save_config()

	@classmethod
	def update_users(cls, users, username_field='email'):
		Config.load_config()
		connected = cls.get_authenticated_user()
		if not isinstance(users, Sequence):
			users = [users]
		for user in users:
			for loaded_user in Config.config['credentials']['usernames'].values():
				if (has_attr(loaded_user, 'id') and get_attr(user, 'id') == loaded_user['id']) or (
						get_attr(user, username_field) == loaded_user[username_field]
				):
					old_username = get_attr(loaded_user, username_field)
					new_username = get_attr(user, username_field)
					loaded_user.update(to_dict(user))
					Config.config['credentials']['usernames'][new_username] = loaded_user
					if old_username != new_username:
						del Config.config['credentials']['usernames'][old_username]
						if connected and get_attr(connected, username_field) == old_username:
							cls.authenticator.logout(location='unrendered')
					break
		Config.save_config()

	@classmethod
	def find_user(cls, username):
		Config.load_config()
		user = Config.config['credentials']['usernames'].get(username)
		return user

	@classmethod
	def find_all_users(cls):
		Config.load_config()
		return Config.config['credentials']['usernames'].values()

	@classmethod
	def find_users_by_id(cls, ids):
		Config.load_config()
		for user in Config.config['credentials']['usernames'].values():
			if get_attr(user, 'id') in ids:
				yield user

	@classmethod
	def get_authenticated_user(cls):
		if st.session_state.get('authentication_status'):
			return cls.find_user(st.session_state['username'])
		return None
