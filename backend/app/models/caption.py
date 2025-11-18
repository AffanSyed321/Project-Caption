from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Caption(Base):
    __tablename__ = "captions"

    id = Column(Integer, primary_key=True, index=True)
    goal = Column(Text, nullable=False)
    caption = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "goal": self.goal,
            "caption": self.caption,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
