from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Text,
    create_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from types import SimpleNamespace

Base = declarative_base()


class avl_cavldataarchive(Base):
    __tablename__ = "avl_cavldataarchive"
    id = Column(Integer, primary_key=True)
    created = Column(TIMESTAMP)
    last_updated = Column(TIMESTAMP)
    data = Column(String)
    data_format = Column(String)


class pipelines_fileprocessingresult(Base):
    __tablename__ = "pipelines_fileprocessingresult"
    id = Column(Integer, primary_key=True)
    created = Column(TIMESTAMP)
    modified = Column(TIMESTAMP)
    task_id = Column(String(36))
    status = Column(String(36))
    completed = Column(TIMESTAMP)
    filename = Column(String(255))
    error_message = Column(Text)
    pipeline_error_code = Column(Integer)
    pipeline_processing_step = Column(Integer)
    revision = Column(Integer)


class pipeline_processing_step(Base):
    __tablename__ = "pipeline_processing_step"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class pipeline_error_code(Base):
    __tablename__ = "pipeline_error_code"
    id = Column(Integer, primary_key=True)
    status = Column(String(255))


class MockedDB:
    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        Base.metadata.create_all(self.engine)
        self.classes = SimpleNamespace(
            avl_cavldataarchive=avl_cavldataarchive,
            pipelines_fileprocessingresult=pipelines_fileprocessingresult,
            pipeline_processing_step = pipeline_processing_step,
            pipeline_error_code=pipeline_error_code,
        )


if __name__ == "__main__":
    DB = MockedDB()
    print(DB.classes)
