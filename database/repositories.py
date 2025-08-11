from modules.auth import Auth
from modules.db import *


class Repository:
	model = None

	def __init_subclass__(cls, **kwargs):
		if cls.model is None:
			raise ValueError("Model must be defined")

	@classmethod
	def _check_params(cls, args, has_data=True):
		if cls.model:
			if has_data and not isinstance(args[0], dict):
				raise ValueError(
					"Invalid data type. Expected a dictionary, but received: "
					f"{type(args[0])}"
				)
		else:
			if has_data:
				if len(args) != 2:
					raise ValueError(
						"Invalid arguments for creating a new instance. Expected two arguments: "
						"the model and the data for the new instance."
					)
				if not isinstance(args[0], type):
					raise ValueError(
						"Invalid model type. Expected a class, but received: "
						f"{type(args[0])}"
					)
				if not isinstance(args[1], dict):
					raise ValueError(
						"Invalid data type. Expected a dictionary, but received: "
						f"{type(args[1])}"
					)
			else:
				if len(args) != 1:
					raise ValueError(
						"Invalid arguments for creating a new instance. Expected one argument: "
						"the model."
					)
				if not isinstance(args[0], type):
					raise ValueError(
						"Invalid model type. Expected a class, but received: "
						f"{type(args[0])}"
					)

	@staticmethod
	def _create(session, **kwargs):
		model = kwargs['model'](**kwargs['data'])
		session.add(model)
		session.commit()
		return model.to_dict()

	@classmethod
	def create(cls, *args, **kwargs):
		cls._check_params(args)
		return DB.session_call(
			cls._create,
			{
				'model': cls.model if cls.model else args[0],
				'data': args[0] if cls.model else args[1]
			},
			kwargs.get('catch_exception', False),
			kwargs.get('show_error', True),
			kwargs.get('session')
		)

	@classmethod
	def find_by_id(cls, *args):
		cls._check_params(args)
		model = cls.model if cls.model else args[0]
		id = args[0] if cls.model else args[1]
		return DB.query(model).filter(model.id == id).first()

	@classmethod
	def find_all(cls, *args):
		cls._check_params(args, False)
		model = cls.model if cls.model else args[0]
		return DB.query(model).all()

	@classmethod
	def query_dataframe(cls, sql, **kwargs):
		return DB.query_dataframe(sql, **kwargs)

	@staticmethod
	def _update(session, **kwargs):
		data = kwargs['data']
		model = DB.query(kwargs['model']).filter(kwargs['model'].id == data['id']).first()
		for key, value in data.items():
			setattr(model, key, value)
		session.add(model)
		session.commit()
		return model.to_dict()

	@classmethod
	def update(cls, *args, **kwargs):
		cls._check_params(args)
		return DB.session_call(
			cls._update,
			{
				'model': cls.model if cls.model else args[0],
				'data': args[0] if cls.model else args[1]
			},
			kwargs.get('catch_exception', False),
			kwargs.get('show_error', True),
			kwargs.get('session')
		)

	@staticmethod
	def _delete(session, **kwargs):
		model = DB.query(kwargs['model']).filter(kwargs['model'].id == id).first()
		session.delete(model)
		session.commit()
		return model.to_dict()

	@classmethod
	def delete(cls, *args, **kwargs):
		cls._check_params(args)
		return DB.session_call(
			cls._delete,
			{
				'model': cls.model if cls.model else args[0],
				'id': args[0] if cls.model else args[1]
			},
			kwargs.get('catch_exception', False),
			kwargs.get('show_error', True),
			kwargs.get('session')
		)

	@classmethod
	def query(cls, *args, **kwargs):
		if cls.model:
			return DB.query(cls.model, *args, **kwargs)
		return DB.query(*args, **kwargs)


class UserRepository(Repository):
	model = User

	@classmethod
	def create(cls, *args, **kwargs):
		user = super(UserRepository, cls).create(*args, **kwargs)
		Auth.add_users([user])
		return user

	@classmethod
	def delete(cls, *args, **kwargs):
		user = super(UserRepository, cls).delete(*args, **kwargs)
		Auth.remove_users([user])
		return user

	@classmethod
	def update(cls, *args, **kwargs):
		user = super(UserRepository, cls).update(*args, **kwargs)
		Auth.update_users([user])
		return user


class StockRepository(Repository):
	model = Stock

class StockRecordRepository(Repository):
	model = StockRecord

class ProductRepository(Repository):
	model = Product

class SalesDepartmentRepository(Repository):
	model = SalesDepartment
