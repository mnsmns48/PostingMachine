from sqlalchemy.orm import DeclarativeBase


class PostingMachineBase(DeclarativeBase):
    __abstract__ = True


class PreModData(PostingMachineBase):
    pass
