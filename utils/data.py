from database.base import Base


def has_attr(obj, attr):
	if isinstance(obj, dict):
		return attr in obj
	return hasattr(obj, attr)


def get_attr(obj, attr):
	if isinstance(obj, dict):
		return obj[attr]
	return getattr(obj, attr)


def to_dict(obj):
	if obj is None:
		return None
	if isinstance(obj, dict):
		return obj
	elif isinstance(obj, Base):
		return obj.to_dict()
	else:
		return obj.__dict__.copy()