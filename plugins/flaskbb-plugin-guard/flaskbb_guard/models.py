"""Database model for FlaskBB-Guard: one row per checked post."""

from datetime import datetime

from flaskbb.utils.database import BaseModel, UTCDateTime
from flaskbb.utils.helpers import time_utcnow
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class ToxicityScore(BaseModel):
    __tablename__ = "toxicity_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=False
    )

    def __repr__(self):
        return f"<ToxicityScore post={self.post_id} score={self.score}>"
