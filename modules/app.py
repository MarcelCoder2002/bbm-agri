from modules.config import Config
from modules.db import DB
from modules.auth import Auth
from modules.router import Router


class App:
	name = "app"
	version = "1.0"

	config = Config
	db = DB
	auth = Auth
	router = Router

	@classmethod
	def run(cls):
		cls.config.load_config()
		cls.auth.load_authenticator()
		cls.router.load_authentication_status()
		cls.router.load_routes()
		cls.router.run()
