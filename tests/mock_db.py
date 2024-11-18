from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Text,
    create_engine
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
    pipeline_error_code_id = Column(Integer)
    pipeline_processing_step_id = Column(Integer)
    revision_id = Column(Integer)


class pipeline_processing_step(Base):
    __tablename__ = "pipeline_processing_step"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    category = Column(String(20))


class pipeline_error_code(Base):
    __tablename__ = "pipeline_error_code"
    id = Column(Integer, primary_key=True)
    status = Column(String(255))

class organisation_datasetrevision(Base):
    __tablename__ = "organization_datasetrevision"

    id = Column(Integer, primary_key=True)
    status = Column(String(20))

class organisation_txcfileattributes(Base):
    __tablename__ = "organisation_txcfileattributes"
    revision_id = Column(Integer, primary_key=True)
    schema_version = Column(String(10))
    revision_number = Column(Integer)
    modification = Column(String(28))
    creation_datetime = Column(TIMESTAMP)
    modification_datetime = Column(TIMESTAMP)
    filename = Column(String(512))
    service_code = Column(String(100))
    national_operator_code = Column(String(100))
    licence_number = Column(String(56))
    operating_period_start_date = Column(TIMESTAMP)
    operating_period_end_date = Column(TIMESTAMP)
    public_use = Column(Boolean, default=True)
    line_names = Column(JSON)
    origin = Column(String(512))
    destination = Column(String(512))
    hash = Column(String(40))


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
            organisation_txcfileattributes=organisation_txcfileattributes,
        )


if __name__ == "__main__":
    DB = MockedDB()
    print(DB.classes)
