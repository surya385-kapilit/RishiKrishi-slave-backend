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
-- Name: salaar_ros; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA salaar_ros;


ALTER SCHEMA salaar_ros OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.form (
    form_id uuid DEFAULT gen_random_uuid() NOT NULL,
    task_id uuid,
    title text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE salaar_ros.form OWNER TO postgres;

--
-- Name: form_field_values; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.form_field_values (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    submission_id uuid,
    field_id uuid,
    value_text text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE salaar_ros.form_field_values OWNER TO postgres;

--
-- Name: form_fields; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.form_fields (
    field_id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_id uuid,
    name text NOT NULL,
    field_type text NOT NULL,
    is_required boolean DEFAULT false,
    field_options jsonb
);


ALTER TABLE salaar_ros.form_fields OWNER TO postgres;

--
-- Name: form_submissions; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.form_submissions (
    submission_id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_id uuid,
    submitted_by uuid,
    submitted_at timestamp without time zone DEFAULT now()
);


ALTER TABLE salaar_ros.form_submissions OWNER TO postgres;

--
-- Name: task; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.task (
    task_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE salaar_ros.task OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: salaar_ros; Owner: postgres
--

CREATE TABLE salaar_ros.users (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    phone character varying(20),
    email character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50),
    status character varying(50) DEFAULT 'active'::character varying,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE salaar_ros.users OWNER TO postgres;

--
-- Name: form_field_values form_field_values_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_field_values
    ADD CONSTRAINT form_field_values_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (field_id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (form_id);


--
-- Name: form_submissions form_submissions_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_submissions
    ADD CONSTRAINT form_submissions_pkey PRIMARY KEY (submission_id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_id);


--
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: idx_form_created_by; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_created_by ON salaar_ros.form USING btree (created_by);


--
-- Name: idx_form_field_values_field_id; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_field_values_field_id ON salaar_ros.form_field_values USING btree (field_id);


--
-- Name: idx_form_field_values_submission_id; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_field_values_submission_id ON salaar_ros.form_field_values USING btree (submission_id);


--
-- Name: idx_form_fields_form_id; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_fields_form_id ON salaar_ros.form_fields USING btree (form_id);


--
-- Name: idx_form_submissions_form_id; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_submissions_form_id ON salaar_ros.form_submissions USING btree (form_id);


--
-- Name: idx_form_submissions_submitted_by; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_submissions_submitted_by ON salaar_ros.form_submissions USING btree (submitted_by);


--
-- Name: idx_form_task_id; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_form_task_id ON salaar_ros.form USING btree (task_id);


--
-- Name: idx_task_created_by; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_task_created_by ON salaar_ros.task USING btree (created_by);


--
-- Name: idx_users_email; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE UNIQUE INDEX idx_users_email ON salaar_ros.users USING btree (email);


--
-- Name: idx_users_phone; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE UNIQUE INDEX idx_users_phone ON salaar_ros.users USING btree (phone);


--
-- Name: idx_users_status; Type: INDEX; Schema: salaar_ros; Owner: postgres
--

CREATE INDEX idx_users_status ON salaar_ros.users USING btree (status);


--
-- Name: form form_created_by_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form
    ADD CONSTRAINT form_created_by_fkey FOREIGN KEY (created_by) REFERENCES salaar_ros.users(user_id);


--
-- Name: form_field_values form_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_field_values
    ADD CONSTRAINT form_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES salaar_ros.form_fields(field_id);


--
-- Name: form_field_values form_field_values_submission_id_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_field_values
    ADD CONSTRAINT form_field_values_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES salaar_ros.form_submissions(submission_id);


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES salaar_ros.form(form_id);


--
-- Name: form_submissions form_submissions_form_id_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_submissions
    ADD CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES salaar_ros.form(form_id);


--
-- Name: form_submissions form_submissions_submitted_by_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form_submissions
    ADD CONSTRAINT form_submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES salaar_ros.users(user_id);


--
-- Name: form form_task_id_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.form
    ADD CONSTRAINT form_task_id_fkey FOREIGN KEY (task_id) REFERENCES salaar_ros.task(task_id);


--
-- Name: task task_created_by_fkey; Type: FK CONSTRAINT; Schema: salaar_ros; Owner: postgres
--

ALTER TABLE ONLY salaar_ros.task
    ADD CONSTRAINT task_created_by_fkey FOREIGN KEY (created_by) REFERENCES salaar_ros.users(user_id);


--
-- PostgreSQL database dump complete
--

