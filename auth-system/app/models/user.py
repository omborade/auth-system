from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.role import user_roles


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)  # indexed for fast lookups
    password_hash = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # M:N → roles
    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="selectin")

    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    @property
    def permission_names(self) -> list[str]:
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return list(perms)

    def __repr__(self) -> str:
        return f"<User email={self.email}>"
