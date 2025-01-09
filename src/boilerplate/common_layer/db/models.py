from typing import Any, List, Optional

from geoalchemy2.types import Geometry
from sqlalchemy import ARRAY, Boolean, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship
import datetime

class Base(MappedAsDataclass, DeclarativeBase):
    pass

test: str = 1

class NaptanDistrict(Base):
    __tablename__ = 'naptan_district'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='naptan_district_pkey'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    naptan_locality: Mapped[List['NaptanLocality']] = relationship('NaptanLocality', back_populates='district')


class OrganisationDataset(Base):
    __tablename__ = 'organisation_dataset'
    __table_args__ = (
        ForeignKeyConstraint(['contact_id'], ['public.users_user.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_contact_id_b440c22b_fk_users_user_id'),
        ForeignKeyConstraint(['live_revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_live_revision_id_e30c3fa4_fk_organisat'),
        ForeignKeyConstraint(['organisation_id'], ['public.organisation_organisation.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_organisation_id_384c7a11_fk_organisat'),
        PrimaryKeyConstraint('id', name='organisation_dataset_pkey'),
        UniqueConstraint('live_revision_id', name='organisation_dataset_live_revision_id_key'),
        Index('organisation_dataset_contact_id_b440c22b', 'contact_id'),
        Index('organisation_dataset_organisation_id_384c7a11', 'organisation_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    organisation_id: Mapped[int] = mapped_column(Integer)
    contact_id: Mapped[int] = mapped_column(Integer)
    dataset_type: Mapped[int] = mapped_column(Integer)
    avl_feed_status: Mapped[str] = mapped_column(String(20))
    is_dummy: Mapped[bool] = mapped_column(Boolean)
    live_revision_id: Mapped[Optional[int]] = mapped_column(Integer)
    avl_feed_last_checked: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    contact: Mapped['UsersUser'] = relationship('UsersUser', back_populates='organisation_dataset')
    live_revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', foreign_keys=[live_revision_id], back_populates='organisation_dataset')
    organisation: Mapped['OrganisationOrganisation'] = relationship('OrganisationOrganisation', back_populates='organisation_dataset')
    organisation_datasetrevision: Mapped[List['OrganisationDatasetrevision']] = relationship('OrganisationDatasetrevision', foreign_keys='[OrganisationDatasetrevision.dataset_id]', back_populates='dataset')


class OrganisationDatasetrevision(Base):
    __tablename__ = 'organisation_datasetrevision'
    __table_args__ = (
        CheckConstraint('num_of_bus_stops >= 0', name='organisation_datasetrevision_num_of_bus_stops_check'),
        CheckConstraint('num_of_lines >= 0', name='organisation_datasetrevision_num_of_lines_check'),
        CheckConstraint('num_of_operators >= 0', name='organisation_datasetrevision_num_of_operators_check'),
        CheckConstraint('num_of_timing_points >= 0', name='organisation_datasetrevision_num_of_timing_points_check'),
        ForeignKeyConstraint(['dataset_id'], ['public.organisation_dataset.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_dataset_id_f0cd70df_fk_organisat'),
        ForeignKeyConstraint(['last_modified_user_id'], ['public.users_user.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_last_modified_user_i_cfda7737_fk_users_use'),
        ForeignKeyConstraint(['published_by_id'], ['public.users_user.id'], deferrable=True, initially='DEFERRED', name='organisation_dataset_published_by_id_4e5c02d1_fk_users_use'),
        PrimaryKeyConstraint('id', name='organisation_datasetrevision_pkey'),
        UniqueConstraint('dataset_id', 'created', name='organisation_datasetrevision_unique_revision'),
        UniqueConstraint('name', name='organisation_datasetrevision_name_24f6c4c0_uniq'),
        Index('organisatio_is_publ_bee2ff_idx', 'is_published'),
        Index('organisation_datasetrevision_dataset_id_f0cd70df', 'dataset_id'),
        Index('organisation_datasetrevision_last_modified_user_id_cfda7737', 'last_modified_user_id'),
        Index('organisation_datasetrevision_name_24f6c4c0_like', 'name'),
        Index('organisation_datasetrevision_published_by_id_4e5c02d1', 'published_by_id'),
        Index('organisation_datasetrevision_unique_draft_revision', 'dataset_id', unique=True),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    status: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    comment: Mapped[str] = mapped_column(String(255))
    is_published: Mapped[bool] = mapped_column(Boolean)
    url_link: Mapped[str] = mapped_column(String(500))
    transxchange_version: Mapped[str] = mapped_column(String(8))
    dataset_id: Mapped[int] = mapped_column(Integer)
    password: Mapped[str] = mapped_column(String(255))
    requestor_ref: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(String(30))
    modified_file_hash: Mapped[str] = mapped_column(String(40))
    original_file_hash: Mapped[str] = mapped_column(String(40))
    upload_file: Mapped[Optional[str]] = mapped_column(String(100))
    num_of_lines: Mapped[Optional[int]] = mapped_column(Integer)
    num_of_operators: Mapped[Optional[int]] = mapped_column(Integer)
    imported: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    bounding_box: Mapped[Optional[str]] = mapped_column(String(8096))
    publisher_creation_datetime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    publisher_modified_datetime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    first_expiring_service: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_expiring_service: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    first_service_start: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    num_of_bus_stops: Mapped[Optional[int]] = mapped_column(Integer)
    last_modified_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    published_by_id: Mapped[Optional[int]] = mapped_column(Integer)
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    num_of_timing_points: Mapped[Optional[int]] = mapped_column(Integer)

    organisation_dataset: Mapped['OrganisationDataset'] = relationship('OrganisationDataset', uselist=False, foreign_keys='[OrganisationDataset.live_revision_id]', back_populates='live_revision')
    dataset: Mapped['OrganisationDataset'] = relationship('OrganisationDataset', foreign_keys=[dataset_id], back_populates='organisation_datasetrevision')
    last_modified_user: Mapped['UsersUser'] = relationship('UsersUser', foreign_keys=[last_modified_user_id], back_populates='organisation_datasetrevision')
    published_by: Mapped['UsersUser'] = relationship('UsersUser', foreign_keys=[published_by_id], back_populates='organisation_datasetrevision_')
    data_quality_postschemaviolation: Mapped[List['DataQualityPostschemaviolation']] = relationship('DataQualityPostschemaviolation', back_populates='revision')
    data_quality_ptiobservation: Mapped[List['DataQualityPtiobservation']] = relationship('DataQualityPtiobservation', back_populates='revision')
    data_quality_ptivalidationresult: Mapped['DataQualityPtivalidationresult'] = relationship('DataQualityPtivalidationresult', uselist=False, back_populates='revision')
    data_quality_schemaviolation: Mapped[List['DataQualitySchemaviolation']] = relationship('DataQualitySchemaviolation', back_populates='revision')
    organisation_txcfileattributes: Mapped[List['OrganisationTxcfileattributes']] = relationship('OrganisationTxcfileattributes', back_populates='revision')
    pipelines_datasetetltaskresult: Mapped[List['PipelinesDatasetetltaskresult']] = relationship('PipelinesDatasetetltaskresult', back_populates='revision')
    pipelines_fileprocessingresult: Mapped[List['PipelinesFileprocessingresult']] = relationship('PipelinesFileprocessingresult', back_populates='revision')


class OtcLicence(Base):
    __tablename__ = 'otc_licence'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='otc_licence_pkey'),
        UniqueConstraint('number', name='otc_licence_number_key'),
        Index('otc_licence_number_d0c037ba_like', 'number'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    number: Mapped[str] = mapped_column(String(9))
    status: Mapped[str] = mapped_column(String(30))
    granted_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[datetime.date]] = mapped_column(Date)

    otc_service: Mapped[List['OtcService']] = relationship('OtcService', back_populates='licence')


class OtcOperator(Base):
    __tablename__ = 'otc_operator'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='otc_operator_pkey'),
        UniqueConstraint('operator_id', name='otc_operator_operator_id_key'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    operator_id: Mapped[int] = mapped_column(Integer)
    operator_name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(Text)
    discs_in_possession: Mapped[Optional[int]] = mapped_column(Integer)
    authdiscs: Mapped[Optional[int]] = mapped_column(Integer)

    otc_service: Mapped[List['OtcService']] = relationship('OtcService', back_populates='operator')


class PipelinesPipelineerrorcode(Base):
    __tablename__ = 'pipelines_pipelineerrorcode'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pipelines_pipelineerrorcode_pkey'),
        UniqueConstraint('error', name='pipelines_pipelineerrorcode_error_key'),
        Index('pipelines_pipelineerrorcode_error_df120360_like', 'error'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    error: Mapped[str] = mapped_column(String(255))

    pipelines_fileprocessingresult: Mapped[List['PipelinesFileprocessingresult']] = relationship('PipelinesFileprocessingresult', back_populates='pipeline_error_code')


class PipelinesPipelineprocessingstep(Base):
    __tablename__ = 'pipelines_pipelineprocessingstep'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pipelines_pipelineprocessingstep_pkey'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(20))

    pipelines_fileprocessingresult: Mapped[List['PipelinesFileprocessingresult']] = relationship('PipelinesFileprocessingresult', back_populates='pipeline_processing_step')


class PipelinesSchemadefinition(Base):
    __tablename__ = 'pipelines_schemadefinition'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pipelines_schemadefinition_pkey'),
        UniqueConstraint('category', name='pipelines_schemadefinition_category_key'),
        Index('pipelines_schemadefinition_category_bfea9f81_like', 'category'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    category: Mapped[str] = mapped_column(String(6))
    checksum: Mapped[str] = mapped_column(String(40))
    schema: Mapped[str] = mapped_column(String(100))


class UiLta(Base):
    __tablename__ = 'ui_lta'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='ui_lta_pkey'),
        UniqueConstraint('id', 'name', name='ui_lta_id_name_304a2476_uniq'),
        UniqueConstraint('name', name='ui_lta_name_key'),
        Index('ui_lta_name_8bea4104_like', 'name'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(Text)

    naptan_adminarea: Mapped[List['NaptanAdminarea']] = relationship('NaptanAdminarea', back_populates='ui_lta')
    otc_localauthority: Mapped[List['OtcLocalauthority']] = relationship('OtcLocalauthority', back_populates='ui_lta')


class UsersUser(Base):
    __tablename__ = 'users_user'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_user_pkey'),
        UniqueConstraint('username', name='users_user_username_key'),
        Index('users_user_username_06e46fe6_like', 'username'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    password: Mapped[str] = mapped_column(String(128))
    is_superuser: Mapped[bool] = mapped_column(Boolean)
    username: Mapped[str] = mapped_column(String(150))
    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    is_staff: Mapped[bool] = mapped_column(Boolean)
    is_active: Mapped[bool] = mapped_column(Boolean)
    date_joined: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    account_type: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(254))
    description: Mapped[str] = mapped_column(String(400))
    dev_organisation: Mapped[str] = mapped_column(String(60))
    agent_organisation: Mapped[str] = mapped_column(String(60))
    notes: Mapped[str] = mapped_column(String(150))
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    organisation_dataset: Mapped[List['OrganisationDataset']] = relationship('OrganisationDataset', back_populates='contact')
    organisation_datasetrevision: Mapped[List['OrganisationDatasetrevision']] = relationship('OrganisationDatasetrevision', foreign_keys='[OrganisationDatasetrevision.last_modified_user_id]', back_populates='last_modified_user')
    organisation_datasetrevision_: Mapped[List['OrganisationDatasetrevision']] = relationship('OrganisationDatasetrevision', foreign_keys='[OrganisationDatasetrevision.published_by_id]', back_populates='published_by')
    organisation_organisation: Mapped['OrganisationOrganisation'] = relationship('OrganisationOrganisation', uselist=False, back_populates='key_contact')


class DataQualityPostschemaviolation(Base):
    __tablename__ = 'data_quality_postschemaviolation'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='data_quality_postsch_revision_id_d236c059_fk_organisat'),
        PrimaryKeyConstraint('id', name='data_quality_postschemaviolation_pkey'),
        Index('data_quality_postschemaviolation_revision_id_d236c059', 'revision_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256))
    details: Mapped[str] = mapped_column(String(1024))
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    revision_id: Mapped[int] = mapped_column(Integer)

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='data_quality_postschemaviolation')


class DataQualityPtiobservation(Base):
    __tablename__ = 'data_quality_ptiobservation'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='data_quality_ptiobse_revision_id_3206212f_fk_organisat'),
        PrimaryKeyConstraint('id', name='data_quality_ptiobservation_pkey'),
        Index('data_quality_ptiobservation_revision_id_3206212f', 'revision_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256))
    line: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(String(1024))
    element: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(1024))
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    revision_id: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str] = mapped_column(String(64))

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='data_quality_ptiobservation')


class DataQualityPtivalidationresult(Base):
    __tablename__ = 'data_quality_ptivalidationresult'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='data_quality_ptivali_revision_id_a90de4ea_fk_organisat'),
        PrimaryKeyConstraint('id', name='data_quality_ptivalidationresult_pkey'),
        UniqueConstraint('revision_id', name='data_quality_ptivalidationresult_revision_id_key'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    report: Mapped[str] = mapped_column(String(100))
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    revision_id: Mapped[int] = mapped_column(Integer)

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='data_quality_ptivalidationresult')


class DataQualitySchemaviolation(Base):
    __tablename__ = 'data_quality_schemaviolation'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='data_quality_schemav_revision_id_09049f6e_fk_organisat'),
        PrimaryKeyConstraint('id', name='data_quality_schemaviolation_pkey'),
        Index('data_quality_schemaviolation_revision_id_09049f6e', 'revision_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256))
    line: Mapped[int] = mapped_column(Integer)
    details: Mapped[str] = mapped_column(String(1024))
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    revision_id: Mapped[int] = mapped_column(Integer)

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='data_quality_schemaviolation')


class NaptanAdminarea(Base):
    __tablename__ = 'naptan_adminarea'
    __table_args__ = (
        ForeignKeyConstraint(['ui_lta_id'], ['public.ui_lta.id'], deferrable=True, initially='DEFERRED', name='naptan_adminarea_ui_lta_id_c37d8a17_fk_ui_lta_id'),
        PrimaryKeyConstraint('id', name='naptan_adminarea_pkey'),
        UniqueConstraint('atco_code', name='naptan_adminarea_atco_code_key'),
        Index('naptan_adminarea_atco_code_167e083c_like', 'atco_code'),
        Index('naptan_adminarea_ui_lta_id_c37d8a17', 'ui_lta_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    traveline_region_id: Mapped[str] = mapped_column(String(255))
    atco_code: Mapped[str] = mapped_column(String(255))
    ui_lta_id: Mapped[Optional[int]] = mapped_column(Integer)

    ui_lta: Mapped['UiLta'] = relationship('UiLta', back_populates='naptan_adminarea')
    naptan_locality: Mapped[List['NaptanLocality']] = relationship('NaptanLocality', back_populates='admin_area')
    naptan_stoppoint: Mapped[List['NaptanStoppoint']] = relationship('NaptanStoppoint', back_populates='admin_area')


class OrganisationOrganisation(Base):
    __tablename__ = 'organisation_organisation'
    __table_args__ = (
        ForeignKeyConstraint(['key_contact_id'], ['public.users_user.id'], deferrable=True, initially='DEFERRED', name='organisation_organis_key_contact_id_df58d4ce_fk_users_use'),
        PrimaryKeyConstraint('id', name='organisation_organisation_pkey'),
        UniqueConstraint('key_contact_id', name='organisation_organisation_key_contact_id_key'),
        UniqueConstraint('name', name='organisation_organisation_name_6b81abae_uniq'),
        Index('organisation_name_idx', 'name'),
        Index('organisation_organisation_name_6b81abae_like', 'name'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    name: Mapped[str] = mapped_column(String(255))
    short_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_abods_global_viewer: Mapped[bool] = mapped_column(Boolean)
    key_contact_id: Mapped[Optional[int]] = mapped_column(Integer)
    licence_required: Mapped[Optional[bool]] = mapped_column(Boolean)

    organisation_dataset: Mapped[List['OrganisationDataset']] = relationship('OrganisationDataset', back_populates='organisation')
    key_contact: Mapped['UsersUser'] = relationship('UsersUser', back_populates='organisation_organisation')


class OrganisationTxcfileattributes(Base):
    __tablename__ = 'organisation_txcfileattributes'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='organisation_txcfile_revision_id_ddb2f841_fk_organisat'),
        PrimaryKeyConstraint('id', name='organisation_txcfileattributes_pkey'),
        Index('organisation_txcfileattributes_revision_id_ddb2f841', 'revision_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(10))
    revision_number: Mapped[int] = mapped_column(Integer)
    creation_datetime: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modification_datetime: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    filename: Mapped[str] = mapped_column(String(512))
    service_code: Mapped[str] = mapped_column(String(100))
    revision_id: Mapped[int] = mapped_column(Integer)
    modification: Mapped[str] = mapped_column(String(28))
    national_operator_code: Mapped[str] = mapped_column(String(100))
    licence_number: Mapped[str] = mapped_column(String(56))
    public_use: Mapped[bool] = mapped_column(Boolean)
    line_names: Mapped[list] = mapped_column(ARRAY(String(length=255)))
    destination: Mapped[str] = mapped_column(String(512))
    origin: Mapped[str] = mapped_column(String(512))
    hash: Mapped[str] = mapped_column(String(40))
    service_mode: Mapped[str] = mapped_column(String(20))
    operating_period_end_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    operating_period_start_date: Mapped[Optional[datetime.date]] = mapped_column(Date)

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='organisation_txcfileattributes')


class OtcLocalauthority(Base):
    __tablename__ = 'otc_localauthority'
    __table_args__ = (
        ForeignKeyConstraint(['ui_lta_id'], ['public.ui_lta.id'], deferrable=True, initially='DEFERRED', name='otc_localauthority_ui_lta_id_f47b3d37_fk_ui_lta_id'),
        PrimaryKeyConstraint('id', name='otc_localauthority_pkey'),
        UniqueConstraint('name', name='otc_localauthority_name_5e53a784_uniq'),
        Index('otc_localauthority_name_5e53a784_like', 'name'),
        Index('otc_localauthority_ui_lta_id_f47b3d37', 'ui_lta_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    ui_lta_id: Mapped[Optional[int]] = mapped_column(Integer)

    ui_lta: Mapped['UiLta'] = relationship('UiLta', back_populates='otc_localauthority')
    otc_localauthority_registration_numbers: Mapped[List['OtcLocalauthorityRegistrationNumbers']] = relationship('OtcLocalauthorityRegistrationNumbers', back_populates='localauthority')


class OtcService(Base):
    __tablename__ = 'otc_service'
    __table_args__ = (
        ForeignKeyConstraint(['licence_id'], ['public.otc_licence.id'], deferrable=True, initially='DEFERRED', name='otc_service_licence_id_8b93ea5f_fk_otc_licence_id'),
        ForeignKeyConstraint(['operator_id'], ['public.otc_operator.id'], deferrable=True, initially='DEFERRED', name='otc_service_operator_id_26fe49fe_fk_otc_operator_id'),
        PrimaryKeyConstraint('id', name='otc_service_pkey'),
        Index('otc_service_api_type_c542e069', 'api_type'),
        Index('otc_service_api_type_c542e069_like', 'api_type'),
        Index('otc_service_licence_id_8b93ea5f', 'licence_id'),
        Index('otc_service_operator_id_26fe49fe', 'operator_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(25))
    variation_number: Mapped[int] = mapped_column(Integer)
    service_number: Mapped[str] = mapped_column(String(1000))
    current_traffic_area: Mapped[str] = mapped_column(String(1))
    start_point: Mapped[str] = mapped_column(Text)
    finish_point: Mapped[str] = mapped_column(Text)
    via: Mapped[str] = mapped_column(Text)
    service_type_other_details: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(25))
    registration_status: Mapped[str] = mapped_column(String(20))
    public_text: Mapped[str] = mapped_column(Text)
    service_type_description: Mapped[str] = mapped_column(String(1000))
    subsidies_description: Mapped[str] = mapped_column(String(7))
    subsidies_details: Mapped[str] = mapped_column(Text)
    effective_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    received_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    registration_code: Mapped[Optional[int]] = mapped_column(Integer)
    short_notice: Mapped[Optional[bool]] = mapped_column(Boolean)
    licence_id: Mapped[Optional[int]] = mapped_column(Integer)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_modified: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    api_type: Mapped[Optional[str]] = mapped_column(Text)
    atco_code: Mapped[Optional[str]] = mapped_column(Text)

    licence: Mapped['OtcLicence'] = relationship('OtcLicence', back_populates='otc_service')
    operator: Mapped['OtcOperator'] = relationship('OtcOperator', back_populates='otc_service')
    otc_localauthority_registration_numbers: Mapped[List['OtcLocalauthorityRegistrationNumbers']] = relationship('OtcLocalauthorityRegistrationNumbers', back_populates='service')


class PipelinesDatasetetltaskresult(Base):
    __tablename__ = 'pipelines_datasetetltaskresult'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='pipelines_datasetetl_revision_id_9f9d619c_fk_organisat'),
        PrimaryKeyConstraint('id', name='pipelines_datasetetltaskresult_pkey'),
        UniqueConstraint('task_id', name='pipelines_datasetetltaskresult_task_id_key'),
        Index('pipelines_datasetetltaskresult_completed_97747a58', 'completed'),
        Index('pipelines_datasetetltaskresult_error_code_0b028d32', 'error_code'),
        Index('pipelines_datasetetltaskresult_error_code_0b028d32_like', 'error_code'),
        Index('pipelines_datasetetltaskresult_revision_id_9f9d619c', 'revision_id'),
        Index('pipelines_datasetetltaskresult_status_20d0d30c', 'status'),
        Index('pipelines_datasetetltaskresult_status_20d0d30c_like', 'status'),
        Index('pipelines_datasetetltaskresult_task_id_a8bbc9bf_like', 'task_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    progress: Mapped[int] = mapped_column(Integer)
    revision_id: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    task_id: Mapped[str] = mapped_column(String(255))
    task_name_failed: Mapped[str] = mapped_column(String(255))
    completed: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    additional_info: Mapped[Optional[str]] = mapped_column(String(512))

    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='pipelines_datasetetltaskresult')


class PipelinesFileprocessingresult(Base):
    __tablename__ = 'pipelines_fileprocessingresult'
    __table_args__ = (
        ForeignKeyConstraint(['pipeline_error_code_id'], ['public.pipelines_pipelineerrorcode.id'], deferrable=True, initially='DEFERRED', name='pipelines_fileproces_pipeline_error_code__90e865f3_fk_pipelines'),
        ForeignKeyConstraint(['pipeline_processing_step_id'], ['public.pipelines_pipelineprocessingstep.id'], deferrable=True, initially='DEFERRED', name='pipelines_fileproces_pipeline_processing__97aa79bd_fk_pipelines'),
        ForeignKeyConstraint(['revision_id'], ['public.organisation_datasetrevision.id'], deferrable=True, initially='DEFERRED', name='pipelines_fileproces_revision_id_9ecfda53_fk_organisat'),
        PrimaryKeyConstraint('id', name='pipelines_fileprocessingresult_pkey'),
        UniqueConstraint('task_id', name='pipelines_fileprocessingresult_task_id_key'),
        Index('pipelines_fileprocessingre_pipeline_processing_step_i_97aa79bd', 'pipeline_processing_step_id'),
        Index('pipelines_fileprocessingresult_completed_d46c00f8', 'completed'),
        Index('pipelines_fileprocessingresult_pipeline_error_code_id_90e865f3', 'pipeline_error_code_id'),
        Index('pipelines_fileprocessingresult_revision_id_9ecfda53', 'revision_id'),
        Index('pipelines_fileprocessingresult_status_8119c347', 'status'),
        Index('pipelines_fileprocessingresult_status_8119c347_like', 'status'),
        Index('pipelines_fileprocessingresult_task_id_d8a57a58_like', 'task_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    modified: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    task_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(255))
    pipeline_processing_step_id: Mapped[int] = mapped_column(Integer)
    revision_id: Mapped[int] = mapped_column(Integer)
    completed: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    pipeline_error_code_id: Mapped[Optional[int]] = mapped_column(Integer)

    pipeline_error_code: Mapped['PipelinesPipelineerrorcode'] = relationship('PipelinesPipelineerrorcode', back_populates='pipelines_fileprocessingresult')
    pipeline_processing_step: Mapped['PipelinesPipelineprocessingstep'] = relationship('PipelinesPipelineprocessingstep', back_populates='pipelines_fileprocessingresult')
    revision: Mapped['OrganisationDatasetrevision'] = relationship('OrganisationDatasetrevision', back_populates='pipelines_fileprocessingresult')


class NaptanLocality(Base):
    __tablename__ = 'naptan_locality'
    __table_args__ = (
        ForeignKeyConstraint(['admin_area_id'], ['public.naptan_adminarea.id'], deferrable=True, initially='DEFERRED', name='naptan_locality_admin_area_id_0765cd72_fk_naptan_adminarea_id'),
        ForeignKeyConstraint(['district_id'], ['public.naptan_district.id'], deferrable=True, initially='DEFERRED', name='naptan_locality_district_id_39815ea9_fk_naptan_district_id'),
        PrimaryKeyConstraint('gazetteer_id', name='naptan_locality_pkey'),
        Index('naptan_locality_admin_area_id_0765cd72', 'admin_area_id'),
        Index('naptan_locality_district_id_39815ea9', 'district_id'),
        Index('naptan_locality_gazetteer_id_6170fc8e_like', 'gazetteer_id'),
        {'schema': 'public'}
    )

    gazetteer_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    easting: Mapped[int] = mapped_column(Integer)
    northing: Mapped[int] = mapped_column(Integer)
    admin_area_id: Mapped[Optional[int]] = mapped_column(Integer)
    district_id: Mapped[Optional[int]] = mapped_column(Integer)

    admin_area: Mapped['NaptanAdminarea'] = relationship('NaptanAdminarea', back_populates='naptan_locality')
    district: Mapped['NaptanDistrict'] = relationship('NaptanDistrict', back_populates='naptan_locality')
    naptan_stoppoint: Mapped[List['NaptanStoppoint']] = relationship('NaptanStoppoint', back_populates='locality')


class OtcLocalauthorityRegistrationNumbers(Base):
    __tablename__ = 'otc_localauthority_registration_numbers'
    __table_args__ = (
        ForeignKeyConstraint(['localauthority_id'], ['public.otc_localauthority.id'], deferrable=True, initially='DEFERRED', name='otc_localauthority_r_localauthority_id_7b261027_fk_otc_local'),
        ForeignKeyConstraint(['service_id'], ['public.otc_service.id'], deferrable=True, initially='DEFERRED', name='otc_localauthority_r_service_id_75d70959_fk_otc_servi'),
        PrimaryKeyConstraint('id', name='otc_localauthority_registration_numbers_pkey'),
        UniqueConstraint('localauthority_id', 'service_id', name='otc_localauthority_regis_localauthority_id_servic_708d1fe0_uniq'),
        Index('otc_localauthority_registr_localauthority_id_7b261027', 'localauthority_id'),
        Index('otc_localauthority_registration_numbers_service_id_75d70959', 'service_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    localauthority_id: Mapped[int] = mapped_column(Integer)
    service_id: Mapped[int] = mapped_column(Integer)

    localauthority: Mapped['OtcLocalauthority'] = relationship('OtcLocalauthority', back_populates='otc_localauthority_registration_numbers')
    service: Mapped['OtcService'] = relationship('OtcService', back_populates='otc_localauthority_registration_numbers')


class NaptanStoppoint(Base):
    __tablename__ = 'naptan_stoppoint'
    __table_args__ = (
        ForeignKeyConstraint(['admin_area_id'], ['public.naptan_adminarea.id'], deferrable=True, initially='DEFERRED', name='naptan_stoppoint_admin_area_id_6ccac623_fk_naptan_adminarea_id'),
        ForeignKeyConstraint(['locality_id'], ['public.naptan_locality.gazetteer_id'], deferrable=True, initially='DEFERRED', name='naptan_stoppoint_locality_id_4ef6e016_fk_naptan_lo'),
        PrimaryKeyConstraint('id', name='naptan_stoppoint_pkey'),
        UniqueConstraint('atco_code', name='naptan_stoppoint_atco_code_key'),
        Index('naptan_stoppoint_admin_area_id_6ccac623', 'admin_area_id'),
        Index('naptan_stoppoint_atco_code_b99b7c43_like', 'atco_code'),
        Index('naptan_stoppoint_locality_id_4ef6e016', 'locality_id'),
        Index('naptan_stoppoint_locality_id_4ef6e016_like', 'locality_id'),
        Index('naptan_stoppoint_location_741ad66c_id', 'location'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    atco_code: Mapped[str] = mapped_column(String(255))
    common_name: Mapped[str] = mapped_column(String(255))
    location: Mapped[Any] = mapped_column(Geometry('POINT', 4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False))
    stop_areas: Mapped[list] = mapped_column(ARRAY(String(length=255)))
    naptan_code: Mapped[Optional[str]] = mapped_column(String(12))
    street: Mapped[Optional[str]] = mapped_column(String(255))
    indicator: Mapped[Optional[str]] = mapped_column(String(255))
    admin_area_id: Mapped[Optional[int]] = mapped_column(Integer)
    locality_id: Mapped[Optional[str]] = mapped_column(String(8))
    bus_stop_type: Mapped[Optional[str]] = mapped_column(String(255))
    stop_type: Mapped[Optional[str]] = mapped_column(String(255))

    admin_area: Mapped['NaptanAdminarea'] = relationship('NaptanAdminarea', back_populates='naptan_stoppoint')
    locality: Mapped['NaptanLocality'] = relationship('NaptanLocality', back_populates='naptan_stoppoint')
