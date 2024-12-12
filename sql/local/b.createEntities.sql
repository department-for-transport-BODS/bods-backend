\c bodds
DO
$do$
BEGIN
   IF EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'bodds_rw') THEN

      RAISE NOTICE 'role "bodds_rw" already exists, skipping';
   ELSE
      BEGIN   -- nested block
         CREATE ROLE bodds_rw LOGIN PASSWORD 'password';
      EXCEPTION
         WHEN duplicate_object THEN
            RAISE NOTICE 'role "bodds_rw" was just created by a concurrent transaction, skipping';
      END;
   END IF;
END
$do$;

REVOKE ALL PRIVILEGES ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA IF NOT EXISTS public;
GRANT CONNECT ON DATABASE bodds to bodds_rw;
GRANT USAGE ON SCHEMA public TO bodds_rw;
GRANT CREATE ON SCHEMA public to bodds_rw;
CREATE EXTENSION IF NOT EXISTS postgis;