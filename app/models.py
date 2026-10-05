from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DealType(str, enum.Enum):
    BUY = "buy"
    RENT = "rent"
    SELL = "sell"


class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    LAND = "land"


class Temperature(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    QUALIFYING = "qualifying"
    OFFERS_SENT = "offers_sent"
    VIEWING_SCHEDULED = "viewing_scheduled"
    NEGOTIATION = "negotiation"
    DEAL = "deal"
    LOST = "lost"


class ReactionType(str, enum.Enum):
    INTERESTED = "interested"
    WANT_VIEWING = "want_viewing"
    NOT_SUITABLE = "not_suitable"


class PropertySource(str, enum.Enum):
    INTERNAL = "internal"
    RIELTOR_UA = "rieltor_ua"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    deal_type: Mapped[DealType | None] = mapped_column(Enum(DealType), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    property_type: Mapped[PropertyType | None] = mapped_column(Enum(PropertyType), nullable=True)
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(10), default="CAD")

    temperature: Mapped[Temperature | None] = mapped_column(Enum(Temperature), nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.NEW)

    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    next_action_due: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    conversation_history: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    reactions: Mapped[list["Reaction"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )

    def missing_required_fields(self) -> list[str]:
        required = {
            "deal_type": self.deal_type,
            "city": self.city,
            "property_type": self.property_type,
            "rooms": self.rooms,
            "budget_max": self.budget_max,
            "phone": self.phone,
        }
        return [name for name, value in required.items() if value in (None, "")]

    def is_qualified(self) -> bool:
        return not self.missing_required_fields()


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[PropertySource] = mapped_column(Enum(PropertySource), default=PropertySource.INTERNAL)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(120))
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), default=PropertyType.APARTMENT)
    deal_type: Mapped[DealType] = mapped_column(Enum(DealType), default=DealType.BUY)
    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="CAD")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    reactions: Mapped[list["Reaction"]] = relationship(back_populates="property")


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    reaction: Mapped[ReactionType] = mapped_column(Enum(ReactionType))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lead: Mapped[Lead] = relationship(back_populates="reactions")
    property: Mapped[Property] = relationship(back_populates="reactions")
