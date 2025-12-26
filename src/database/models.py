from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from datetime import date


class Base(DeclarativeBase):
    def __repr__(self):
        cols = []
        for col in self.__table__.columns.keys():
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone: Mapped[str]
    birthday: Mapped[date]
    info: Mapped[str | None] = mapped_column(nullable=True)

    user: Mapped['User'] = relationship(back_populates='contacts')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username : Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)

    contacts:Mapped[list['Contact']] = relationship(back_populates="user")
