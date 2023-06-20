from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    text,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    due_date = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    is_completed = Column(Boolean, nullable=False, server_default="FALSE")
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    owner = relationship("User", back_populates="tasks")
    attachments = relationship("Attachment", back_populates="attachment")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_attachment = Column(LargeBinary)
    task_id = Column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    attachment = relationship("Task", back_populates="attachments")
