CREATE TABLE IF NOT EXISTS public.organisation_datasetrevision (
	id serial4 NOT NULL,
	filename varchar(255) NOT NULL,
	CONSTRAINT organisation_datasetrevision_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.pipeline_error_code (
	id serial4 NOT NULL,
	status varchar(255) NOT NULL,
	CONSTRAINT pipeline_error_code_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.pipeline_processing_step (
	id serial4 NOT NULL,
	name varchar(20) NOT NULL,
	CONSTRAINT pipeline_processing_step_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.file_processing_result (
	id serial4 NOT NULL,
	created timestamptz NOT NULL,
	modified timestamptz NOT NULL,
	task_id varchar(36) NOT NULL,
    status ENUM('active', 'inactive', 'pending') NOT NULL
    completed timestamptz NOT NULL,
    filename varchar(255) NOT NULL,
    error_message text,
    pipeline_error_code,
    pipeline_processing_step,
    revision,
    FOREIGN KEY (pipeline_error_code) REFERENCES pipeline_error_code(id),
    FOREIGN KEY (pipeline_processing_step) REFERENCES pipeline_processing_step(id),
    FOREIGN KEY (revision) REFERENCES organisation_datasetrevision(id),
	CONSTRAINT file_processing_result_pkey PRIMARY KEY (id)
);

INSERT INTO pipeline_error_code (status) VALUES
('DANGEROUS_XML_ERROR'), ('DATASET_EXPIRED'), ('FILE_TOO_LARGE'),
('NESTED_ZIP_FORBIDDEN'), ('NO_DATA_FOUND'), ('NO_VALID_FILE_TO_PROCESS'),
('POST_SCHEMA_ERROR'), ('SCHEMA_ERROR'), ('SCHEMA_VERSION_MISSING'),
('SCHEMA_VERSION_NOT_SUPPORTED'), ('SUSPICIOUS_FILE'), ('SYSTEM_ERROR'),
('XML_SYNTAX_ERROR'), ('ZIP_TOO_LARGE');

INSERT INTO pipeline_processing_step (name) VALUES
('FARES'), ('TIMETABLES');


INSERT INTO pipeline_processing_step (filename) VALUES
('abc.xml'), ('sample.zip'), ('test_a.xml'), ('sample_etx.zip');