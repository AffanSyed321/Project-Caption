from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    is_rural = Column(Boolean, default=False)

    # Full research data
    gpt_research = Column(Text)
    chamber_info = Column(Text)
    government_info = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "is_rural": self.is_rural,
            "gpt_research": self.gpt_research,
            "chamber_info": self.chamber_info,
            "government_info": self.government_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
