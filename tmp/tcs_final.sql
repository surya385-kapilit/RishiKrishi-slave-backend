--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tcs; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tcs;


ALTER SCHEMA tcs OWNER TO postgres;

--
-- Name: access_type_enum; Type: TYPE; Schema: tcs; Owner: postgres
--

CREATE TYPE tcs.access_type_enum AS ENUM (
    'individual',
    'all'
);


ALTER TYPE tcs.access_type_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.form (
    form_id uuid NOT NULL,
    task_id uuid,
    title text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now(),
    is_active boolean
);


ALTER TABLE tcs.form OWNER TO postgres;

--
-- Name: form_access; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.form_access (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_id uuid,
    user_id uuid,
    access_type tcs.access_type_enum DEFAULT 'all'::tcs.access_type_enum NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    created_by uuid
);


ALTER TABLE tcs.form_access OWNER TO postgres;

--
-- Name: form_field_values; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.form_field_values (
    id uuid NOT NULL,
    submission_id uuid,
    field_id uuid,
    value_text text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE tcs.form_field_values OWNER TO postgres;

--
-- Name: form_fields; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.form_fields (
    field_id uuid NOT NULL,
    form_id uuid,
    name text NOT NULL,
    field_type text NOT NULL,
    is_required boolean DEFAULT false,
    field_options jsonb
);


ALTER TABLE tcs.form_fields OWNER TO postgres;

--
-- Name: form_submissions; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.form_submissions (
    submission_id uuid NOT NULL,
    form_id uuid,
    submitted_by uuid,
    submitted_at timestamp without time zone DEFAULT now(),
    flagged public.flag_status DEFAULT 'none'::public.flag_status
);


ALTER TABLE tcs.form_submissions OWNER TO postgres;

--
-- Name: notification_reads; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.notification_reads (
    id bigint NOT NULL,
    notification_id bigint NOT NULL,
    user_id uuid NOT NULL,
    read_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE tcs.notification_reads OWNER TO postgres;

--
-- Name: notification_reads_id_seq; Type: SEQUENCE; Schema: tcs; Owner: postgres
--

CREATE SEQUENCE tcs.notification_reads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tcs.notification_reads_id_seq OWNER TO postgres;

--
-- Name: notification_reads_id_seq; Type: SEQUENCE OWNED BY; Schema: tcs; Owner: postgres
--

ALTER SEQUENCE tcs.notification_reads_id_seq OWNED BY tcs.notification_reads.id;


--
-- Name: notifications; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.notifications (
    notification_id bigint NOT NULL,
    user_id uuid,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    created_by uuid,
    is_read boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    form_id uuid
);


ALTER TABLE tcs.notifications OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE; Schema: tcs; Owner: postgres
--

CREATE SEQUENCE tcs.notifications_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tcs.notifications_notification_id_seq OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE OWNED BY; Schema: tcs; Owner: postgres
--

ALTER SEQUENCE tcs.notifications_notification_id_seq OWNED BY tcs.notifications.notification_id;


--
-- Name: task; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.task (
    task_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE tcs.task OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: tcs; Owner: postgres
--

CREATE TABLE tcs.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50),
    phone character varying(14),
    status character varying(50) DEFAULT 'active'::character varying,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE tcs.users OWNER TO postgres;

--
-- Name: notification_reads id; Type: DEFAULT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.notification_reads ALTER COLUMN id SET DEFAULT nextval('tcs.notification_reads_id_seq'::regclass);


--
-- Name: notifications notification_id; Type: DEFAULT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.notifications ALTER COLUMN notification_id SET DEFAULT nextval('tcs.notifications_notification_id_seq'::regclass);


--
-- Name: form_access form_access_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_access
    ADD CONSTRAINT form_access_pkey PRIMARY KEY (access_id);


--
-- Name: form_field_values form_field_values_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_field_values
    ADD CONSTRAINT form_field_values_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (field_id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (form_id);


--
-- Name: form_submissions form_submissions_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_submissions
    ADD CONSTRAINT form_submissions_pkey PRIMARY KEY (submission_id);


--
-- Name: notification_reads notification_reads_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.notification_reads
    ADD CONSTRAINT notification_reads_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_form_access_form_id; Type: INDEX; Schema: tcs; Owner: postgres
--

CREATE INDEX idx_form_access_form_id ON tcs.form_access USING btree (form_id);


--
-- Name: idx_form_access_form_user; Type: INDEX; Schema: tcs; Owner: postgres
--

CREATE INDEX idx_form_access_form_user ON tcs.form_access USING btree (form_id, user_id);


--
-- Name: idx_form_access_user_id; Type: INDEX; Schema: tcs; Owner: postgres
--

CREATE INDEX idx_form_access_user_id ON tcs.form_access USING btree (user_id);


--
-- Name: notification_reads fk_notification_reads_notification; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.notification_reads
    ADD CONSTRAINT fk_notification_reads_notification FOREIGN KEY (notification_id) REFERENCES tcs.notifications(notification_id) ON DELETE CASCADE;


--
-- Name: form_access form_access_form_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_access
    ADD CONSTRAINT form_access_form_id_fkey FOREIGN KEY (form_id) REFERENCES tcs.form(form_id) ON DELETE CASCADE;


--
-- Name: form_field_values form_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_field_values
    ADD CONSTRAINT form_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES tcs.form_fields(field_id);


--
-- Name: form_field_values form_field_values_submission_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_field_values
    ADD CONSTRAINT form_field_values_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES tcs.form_submissions(submission_id);


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES tcs.form(form_id);


--
-- Name: form_submissions form_submissions_form_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form_submissions
    ADD CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES tcs.form(form_id);


--
-- Name: form form_task_id_fkey; Type: FK CONSTRAINT; Schema: tcs; Owner: postgres
--

ALTER TABLE ONLY tcs.form
    ADD CONSTRAINT form_task_id_fkey FOREIGN KEY (task_id) REFERENCES tcs.task(task_id);


--
-- PostgreSQL database dump complete
--

