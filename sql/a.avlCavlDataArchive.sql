CREATE TABLE IF NOT EXISTS public.avl_cavldataarchive (
	id serial4 NOT NULL,
	created timestamptz NOT NULL,
	last_updated timestamptz NOT NULL,
	"data" varchar(100) NOT NULL,
	data_format varchar(2) NOT NULL,
	CONSTRAINT avl_cavldataarchive_pkey PRIMARY KEY (id)
);