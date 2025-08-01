# database/operations.py
"""Opérations sur la base de données"""

import pandas as pd
from sqlalchemy.exc import IntegrityError
from .models import SessionLocal, User, UserData
from datetime import datetime


class DatabaseManager:
	"""Gestionnaire des opérations de base de données"""

	def __init__(self):
		self.session_factory = SessionLocal

	def get_session(self):
		"""Retourne une nouvelle session de base de données"""
		return self.session_factory()

	def create_user(self, username, email, name):
		"""Crée un nouvel utilisateur"""
		session = self.get_session()
		try:
			user = User(username=username, email=email, name=name)
			session.add(user)
			session.commit()
			return user.id
		except IntegrityError:
			session.rollback()
			raise ValueError("Utilisateur ou email déjà existant")
		finally:
			session.close()

	def get_user_id_by_username(self, username):
		"""Récupère l'ID utilisateur par nom d'utilisateur"""
		session = self.get_session()
		try:
			user = session.query(User).filter(User.username == username).first()
			return user.id if user else None
		finally:
			session.close()

	def get_user_info(self, user_id):
		"""Récupère les informations d'un utilisateur"""
		session = self.get_session()
		try:
			user = session.query(User).filter(User.id == user_id).first()
			if user:
				return {
					'username': user.username,
					'email': user.email,
					'name': user.name,
					'created_at': user.created_at.strftime('%d/%m/%Y')
				}
			return {}
		finally:
			session.close()

	def get_user_data(self, user_id):
		"""Récupère toutes les données d'un utilisateur"""
		session = self.get_session()
		try:
			data = session.query(UserData).filter(UserData.user_id == user_id).all()

			if not data:
				return pd.DataFrame()

			data_list = []
			for item in data:
				data_list.append({
					'id': item.id,
					'title': item.title,
					'content': item.content,
					'category': item.category,
					'priority': item.priority,
					'status': item.status,
					'tags': item.tags,
					'created_at': item.created_at,
					'updated_at': item.updated_at
				})

			return pd.DataFrame(data_list)
		finally:
			session.close()

	def add_user_data(self, user_id, title, content, category, priority, status, tags):
		"""Ajoute une nouvelle entrée de données"""
		session = self.get_session()
		try:
			new_data = UserData(
				user_id=user_id,
				title=title,
				content=content,
				category=category,
				priority=priority,
				status=status,
				tags=tags
			)
			session.add(new_data)
			session.commit()
			return True, "Données ajoutées avec succès!"
		except Exception as e:
			session.rollback()
			return False, f"Erreur: {str(e)}"
		finally:
			session.close()

	def update_user_data(self, data_id, user_id, title, content, category, priority, status, tags):
		"""Met à jour une entrée existante"""
		session = self.get_session()
		try:
			data = session.query(UserData).filter(
				UserData.id == data_id,
				UserData.user_id == user_id
			).first()

			if data:
				data.title = title
				data.content = content
				data.category = category
				data.priority = priority
				data.status = status
				data.tags = tags
				data.updated_at = datetime.utcnow()

				session.commit()
				return True, "Données mises à jour avec succès!"
			else:
				return False, "Données non trouvées"
		except Exception as e:
			session.rollback()
			return False, f"Erreur: {str(e)}"
		finally:
			session.close()

	def delete_user_data(self, data_id, user_id):
		"""Supprime une entrée de données"""
		session = self.get_session()
		try:
			data = session.query(UserData).filter(
				UserData.id == data_id,
				UserData.user_id == user_id
			).first()

			if data:
				session.delete(data)
				session.commit()
				return True, "Données supprimées avec succès!"
			else:
				return False, "Données non trouvées"
		except Exception as e:
			session.rollback()
			return False, f"Erreur: {str(e)}"
		finally:
			session.close()

	def get_user_stats(self, user_id):
		"""Récupère les statistiques d'un utilisateur"""
		session = self.get_session()
		try:
			total = session.query(UserData).filter(UserData.user_id == user_id).count()
			completed = session.query(UserData).filter(
				UserData.user_id == user_id,
				UserData.status == 'Completed'
			).count()

			return {
				'total': total,
				'completed': completed,
				'active': session.query(UserData).filter(
					UserData.user_id == user_id,
					UserData.status == 'Active'
				).count(),
				'high_priority': session.query(UserData).filter(
					UserData.user_id == user_id,
					UserData.priority == 'High'
				).count()
			}
		finally:
			session.close()
