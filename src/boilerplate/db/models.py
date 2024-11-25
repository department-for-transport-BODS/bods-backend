from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship
import datetime

class Base(MappedAsDataclass, DeclarativeBase):
    pass


class AvlCavldataarchive(Base):
    __tablename__ = 'avl_cavldataarchive'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='avl_cavldataarchive_pkey'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    last_updated: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    data: Mapped[str] = mapped_column(String(100))
    data_format: Mapped[str] = mapped_column(String(2))


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
    pipelines_datasetetltaskresult: Mapped[List['PipelinesDatasetetltaskresult']] = relationship('PipelinesDatasetetltaskresult', back_populates='revision')
    pipelines_fileprocessingresult: Mapped[List['PipelinesFileprocessingresult']] = relationship('PipelinesFileprocessingresult', back_populates='revision')


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
