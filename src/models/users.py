from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    is_verified = Column(Boolean, nullable=False, server_default=text("FALSE"))
    is_oauth = Column(Boolean, server_default=text("FALSE"))

    tasks = relationship("Task", back_populates="owner")
    verifications = relationship("Verification", back_populates="tokens")


class Verification(Base):
    __tablename__ = "verifications"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    token = Column(Integer, nullable=False, unique=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

    tokens = relationship("User", back_populates="verifications")
