from sqlalchemy import Column, Integer, String, Boolean, JSON, TIMESTAMP, Text, create_engine, event
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
    __tablename__ = "pipelines_pipelineprocessingstep"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    category = Column(String(20))


class pipeline_error_code(Base):
    __tablename__ = "pipelines_pipelineerrorcode"
    id = Column(Integer, primary_key=True)
    status = Column(String(255))


class organisation_datasetrevision(Base):
    __tablename__ = "organization_datasetrevision"

    id = Column(Integer, primary_key=True)
    status = Column(String(20))


class organisation_txcfileattributes(Base):
    __tablename__ = "organisation_txcfileattributes"
    id = Column(Integer, primary_key=True)
    revision_id = Column(Integer)
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


class data_quality_postschemaviolation(Base):
    __tablename__ = "data_quality_postschemaviolation"

    id = Column(Integer, primary_key=True)
    filename = Column(String(512))
    line = Column(Integer)
    details = Column(String(1024))
    revision_id = Column(Integer)


class organisation_dataset(Base):
    __tablename__ = "organisation_dataset"
    id = Column(Integer, primary_key=True)


class naptan_stoppoint(Base):
    __tablename__ = "naptan_stoppoint"
    id = Column(Integer, primary_key=True)
    atco_code = Column(String(255))
    stop_type = Column(String(255))
    bus_stop_type = Column(String(255))
    stop_areas = Column(JSON)


class otc_service(Base):
    __tablename__ = "otc_service"
    id = Column(Integer, primary_key=True)
    registration_number = Column(String(25))
    api_type = Column(String(10))
    atco_code = Column(String(255))


class naptan_adminarea(Base):
    __tablename__ = "naptan_adminarea"
    id = Column(Integer, primary_key=True)
    atco_code = Column(String(255))
    traveline_region_id = Column(String(255))
    ui_lta_id = Column(Integer)


class ui_lta(Base):
    __tablename__ = "ui_lta"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class otc_localauthority(Base):
    __tablename__ = "otc_localauthority"
    id = Column(Integer, primary_key=True)
    ui_lta_id = Column(Integer)


class otc_localauthority_registration_numbers(Base):
    __tablename__ = "otc_localauthority_registration_numbers"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer)
    localauthority_id = Column(Integer)


class StringAgg:
    """
    Temporary patch to support string_agg function
    TODO: Remove this once we're running tests in postgres
    """
    def __init__(self):
        self.values = set()

    def step(self, value, delimiter):
        self.values.add(value)

    def finalize(self):
        return "|".join(self.values)

class MockedDB:
    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:")
        
        # Register the custom string_agg aggregate function
        @event.listens_for(self.engine, "connect")
        def register_custom_functions(dbapi_connection, connection_record):
            dbapi_connection.create_aggregate("string_agg", 2, StringAgg)
        
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        Base.metadata.create_all(self.engine)
        self.classes = SimpleNamespace(
            avl_cavldataarchive=avl_cavldataarchive,
            pipelines_fileprocessingresult=pipelines_fileprocessingresult,
            pipelines_pipelineprocessingstep=pipeline_processing_step,
            pipelines_pipelineerrorcode=pipeline_error_code,
            organisation_datasetrevision=organisation_datasetrevision,
            organisation_txcfileattributes=organisation_txcfileattributes,
            data_quality_postschemaviolation=data_quality_postschemaviolation,
            organisation_dataset=organisation_dataset,
            naptan_stoppoint=naptan_stoppoint,
            otc_service=otc_service,
            naptan_adminarea=naptan_adminarea,
            ui_lta=ui_lta,
            otc_localauthority=otc_localauthority,
            otc_localauthority_registration_numbers=otc_localauthority_registration_numbers,
        )




if __name__ == "__main__":
    DB = MockedDB()
    print(DB.classes)
