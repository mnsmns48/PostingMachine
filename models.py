from sqlalchemy import BIGINT, DateTime, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PostingMachineBase(DeclarativeBase):
    __abstract__ = True


class PreModData(PostingMachineBase):
    __tablename__ = 'premoderate'
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    source: Mapped[str]
    internal_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(BIGINT)
    source_title: Mapped[str | None]
    signer_id: Mapped[int | None] = mapped_column(BIGINT)
    signer_name: Mapped[str | None]
    phone_number: Mapped[int | None] = mapped_column(BIGINT)
    text: Mapped[str | None]
    is_repost: Mapped[bool | None]
    repost_source_id: Mapped[int | None] = mapped_column(BIGINT)
    repost_source_title: Mapped[str | None]
    attachments_info: Mapped[str | None]
    attachments: Mapped[dict | None] = mapped_column(type_=JSON)
    url: Mapped[str]