CREATE SCHEMA IF NOT EXISTS test_tenant;
SET search_path TO test_tenant;
--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 17.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: template_schema; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA test_tenant;


ALTER SCHEMA test_tenant OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.form (
    form_id uuid NOT NULL,
    task_id uuid,
    title text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE test_tenant.form OWNER TO postgres;

--
-- Name: form_field_values; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.form_field_values (
    id uuid NOT NULL,
    submission_id uuid,
    field_id uuid,
    value_text text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE test_tenant.form_field_values OWNER TO postgres;

--
-- Name: form_fields; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.form_fields (
    field_id uuid NOT NULL,
    form_id uuid,
    name text NOT NULL,
    field_type text NOT NULL,
    is_required boolean DEFAULT false,
    field_options jsonb
);


ALTER TABLE test_tenant.form_fields OWNER TO postgres;

--
-- Name: form_submissions; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.form_submissions (
    submission_id uuid NOT NULL,
    form_id uuid,
    submitted_by uuid,
    submitted_at timestamp without time zone DEFAULT now()
);


ALTER TABLE test_tenant.form_submissions OWNER TO postgres;

--
-- Name: task; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.task (
    task_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE test_tenant.task OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: template_schema; Owner: postgres
--

CREATE TABLE test_tenant.users (
    id uuid NOT NULL,
    global_user_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50),
    status character varying(50) DEFAULT 'active'::character varying,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE test_tenant.users OWNER TO postgres;

--
-- Name: form_field_values form_field_values_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_field_values
    ADD CONSTRAINT form_field_values_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (field_id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (form_id);


--
-- Name: form_submissions form_submissions_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_submissions
    ADD CONSTRAINT form_submissions_pkey PRIMARY KEY (submission_id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: form form_created_by_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form
    ADD CONSTRAINT form_created_by_fkey FOREIGN KEY (created_by) REFERENCES test_tenant.users(id);


--
-- Name: form_field_values form_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_field_values
    ADD CONSTRAINT form_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES test_tenant.form_fields(field_id);


--
-- Name: form_field_values form_field_values_submission_id_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_field_values
    ADD CONSTRAINT form_field_values_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES test_tenant.form_submissions(submission_id);


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES test_tenant.form(form_id);


--
-- Name: form_submissions form_submissions_form_id_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_submissions
    ADD CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES test_tenant.form(form_id);


--
-- Name: form_submissions form_submissions_submitted_by_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form_submissions
    ADD CONSTRAINT form_submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES test_tenant.users(id);


--
-- Name: form form_task_id_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.form
    ADD CONSTRAINT form_task_id_fkey FOREIGN KEY (task_id) REFERENCES test_tenant.task(task_id);


--
-- Name: task task_created_by_fkey; Type: FK CONSTRAINT; Schema: template_schema; Owner: postgres
--

ALTER TABLE ONLY test_tenant.task
    ADD CONSTRAINT task_created_by_fkey FOREIGN KEY (created_by) REFERENCES test_tenant.users(id);


--
-- PostgreSQL database dump complete
--

