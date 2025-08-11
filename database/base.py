from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	__crud_tablename__: str = None

	def to_dict(self):
		return {
			c.key: getattr(self, c.name)
			for c in self.__table__.columns
		}

	def __repr__(self):
		return self.__str__()
