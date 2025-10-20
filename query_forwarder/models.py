"""SQLAlchemy data models for query-forwarder."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Domain(Base):
    """Tenant in the multi-tenant application."""

    __tablename__ = "domain"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    config: Mapped[Optional["DomainConfig"]] = relationship(
        "DomainConfig", back_populates="domain", uselist=False
    )
    domain_users: Mapped[list["DomainUser"]] = relationship(
        "DomainUser", back_populates="domain"
    )

    def __repr__(self) -> str:
        return f"<Domain(id={self.id}, name={self.name})>"


class User(Base):
    """User account that can belong to one or more domains."""

    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)

    domain_users: Mapped[list["DomainUser"]] = relationship(
        "DomainUser", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class DomainUser(Base):
    """Many-to-many relationship between domains and users."""

    __tablename__ = "domain_user"
    __table_args__ = (UniqueConstraint("domain_id", "user_id", name="uq_domain_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("domain.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )

    domain: Mapped["Domain"] = relationship("Domain", back_populates="domain_users")
    user: Mapped["User"] = relationship("User", back_populates="domain_users")

    def __repr__(self) -> str:
        return f"<DomainUser(domain_id={self.domain_id}, user_id={self.user_id})>"


class DomainConfig(Base):
    """Configuration for a domain's database query and API forwarding settings."""

    __tablename__ = "domain_config"

    domain_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("domain.id"), primary_key=True, unique=True
    )
    db_uri: Mapped[str] = mapped_column(String(255), nullable=False)
    db_query: Mapped[str] = mapped_column(Text, nullable=False)
    api_auth_type: Mapped[str] = mapped_column(String(50), nullable=False)
    api_username: Mapped[str] = mapped_column(String(255), nullable=False)
    api_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Stored encrypted using AES-256-GCM
    api_endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    api_request_type: Mapped[str] = mapped_column(String(10), nullable=False)

    domain: Mapped["Domain"] = relationship("Domain", back_populates="config")

    def __repr__(self) -> str:
        return f"<DomainConfig(domain_id={self.domain_id}, api_endpoint={self.api_endpoint})>"


class APILog(Base):
    """Log entry for API requests and responses."""

    __tablename__ = "api_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("domain.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    query_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    query_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    request_url: Mapped[str] = mapped_column(String(255), nullable=False)
    request_headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    domain: Mapped["Domain"] = relationship("Domain")

    def __repr__(self) -> str:
        return f"<APILog(id={self.id}, domain_id={self.domain_id}, timestamp={self.timestamp})>"
