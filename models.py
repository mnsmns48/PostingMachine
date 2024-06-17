from datetime import datetime

from sqlalchemy import BIGINT, DateTime, func, Sequence, BigInteger
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PostingMachineBase(DeclarativeBase):
    __abstract__ = True


class PreModData(PostingMachineBase):
    __tablename__ = 'premoderate'
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=False))
    url: Mapped[str]
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


class Posts(PostingMachineBase):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, default=Sequence('posts_id_seq', start=1))
    post_id: Mapped[int | None] = mapped_column(BigInteger)
    time: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), server_default=func.now())
    group_id: Mapped[int | None] = mapped_column(BigInteger)
    group_name: Mapped[str | None]
    signer_id: Mapped[int | None] = mapped_column(BigInteger)
    signer_name: Mapped[str]
    phone_number: Mapped[int | None] = mapped_column(BigInteger)
    text: Mapped[str | None]
    is_repost: Mapped[bool | None]
    repost_source_id: Mapped[int | None] = mapped_column(BigInteger)
    repost_source_name: Mapped[str | None]
    attachments: Mapped[str | None]
    source: Mapped[str | None]


class BadPosts(PostingMachineBase):
    __tablename__ = 'badposts'
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=False))
    url: Mapped[str]
    source: Mapped[str]
    internal_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    source_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
