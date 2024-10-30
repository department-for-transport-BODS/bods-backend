from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Date,
    Boolean,
    create_engine,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from types import SimpleNamespace

Base = declarative_base()


class avl_cavldataarchive(Base):
    __tablename__ = "avl_cavldataarchive"
    id = Column(Integer, primary_key=True)
    created = Column(TIMESTAMP)
    last_updated = Column(TIMESTAMP)
    data = Column(String)
    data_format = Column(String)


class MockedDB:
    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        Base.metadata.create_all(self.engine)
        self.classes = SimpleNamespace(
            avl_cavldataarchive=avl_cavldataarchive,
        )


if __name__ == "__main__":
    DB = MockedDB()
    print(DB.classes)
