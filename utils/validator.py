from streamlit_authenticator.utilities.validator import Validator as BaseValidator

class Validator(BaseValidator):
	def validate_password(self, password: str) -> bool:
		return len(password) >= 8