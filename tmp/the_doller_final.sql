--
-- PostgreSQL database dump
--

-- Dumped from database version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
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
-- Name: the_doller; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA the_doller;


ALTER SCHEMA the_doller OWNER TO postgres;

--
-- Name: access_type_enum; Type: TYPE; Schema: the_doller; Owner: postgres
--

CREATE TYPE the_doller.access_type_enum AS ENUM (
    'individual',
    'all'
);


ALTER TYPE the_doller.access_type_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.form (
    form_id uuid NOT NULL,
    task_id uuid,
    title text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text),
    is_active boolean
);


ALTER TABLE the_doller.form OWNER TO postgres;

--
-- Name: form_access; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.form_access (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_id uuid,
    user_id uuid,
    access_type the_doller.access_type_enum DEFAULT 'all'::the_doller.access_type_enum NOT NULL,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text),
    created_by uuid
);


ALTER TABLE the_doller.form_access OWNER TO postgres;

--
-- Name: form_field_values; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.form_field_values (
    id uuid NOT NULL,
    submission_id uuid,
    field_id uuid,
    value_text text,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text)
);


ALTER TABLE the_doller.form_field_values OWNER TO postgres;

--
-- Name: form_fields; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.form_fields (
    field_id uuid NOT NULL,
    form_id uuid,
    name text NOT NULL,
    field_type text NOT NULL,
    is_required boolean DEFAULT false,
    field_options jsonb
);


ALTER TABLE the_doller.form_fields OWNER TO postgres;

--
-- Name: form_submissions; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.form_submissions (
    submission_id uuid NOT NULL,
    form_id uuid,
    submitted_by uuid,
    submitted_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text),
    flagged public.flag_status DEFAULT 'none'::public.flag_status
);


ALTER TABLE the_doller.form_submissions OWNER TO postgres;

--
-- Name: notification_reads; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.notification_reads (
    id bigint NOT NULL,
    notification_id bigint NOT NULL,
    user_id uuid NOT NULL,
    read_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE the_doller.notification_reads OWNER TO postgres;

--
-- Name: notification_reads_id_seq; Type: SEQUENCE; Schema: the_doller; Owner: postgres
--

CREATE SEQUENCE the_doller.notification_reads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE the_doller.notification_reads_id_seq OWNER TO postgres;

--
-- Name: notification_reads_id_seq; Type: SEQUENCE OWNED BY; Schema: the_doller; Owner: postgres
--

ALTER SEQUENCE the_doller.notification_reads_id_seq OWNED BY the_doller.notification_reads.id;


--
-- Name: notifications; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.notifications (
    notification_id bigint NOT NULL,
    user_id uuid,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    created_by uuid,
    is_read boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text),
    form_id uuid
);


ALTER TABLE the_doller.notifications OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE; Schema: the_doller; Owner: postgres
--

CREATE SEQUENCE the_doller.notifications_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE the_doller.notifications_notification_id_seq OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE OWNED BY; Schema: the_doller; Owner: postgres
--

ALTER SEQUENCE the_doller.notifications_notification_id_seq OWNED BY the_doller.notifications.notification_id;


--
-- Name: task; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.task (
    task_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text)
);


ALTER TABLE the_doller.task OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: the_doller; Owner: postgres
--

CREATE TABLE the_doller.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50),
    phone character varying(14),
    status character varying(50) DEFAULT 'active'::character varying,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'Asia/Kolkata'::text)
);


ALTER TABLE the_doller.users OWNER TO postgres;

--
-- Name: notification_reads id; Type: DEFAULT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.notification_reads ALTER COLUMN id SET DEFAULT nextval('the_doller.notification_reads_id_seq'::regclass);


--
-- Name: notifications notification_id; Type: DEFAULT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.notifications ALTER COLUMN notification_id SET DEFAULT nextval('the_doller.notifications_notification_id_seq'::regclass);


--
-- Name: form_access form_access_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_access
    ADD CONSTRAINT form_access_pkey PRIMARY KEY (access_id);


--
-- Name: form_field_values form_field_values_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_field_values
    ADD CONSTRAINT form_field_values_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (field_id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (form_id);


--
-- Name: form_submissions form_submissions_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_submissions
    ADD CONSTRAINT form_submissions_pkey PRIMARY KEY (submission_id);


--
-- Name: notification_reads notification_reads_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.notification_reads
    ADD CONSTRAINT notification_reads_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_form_access_form_id; Type: INDEX; Schema: the_doller; Owner: postgres
--

CREATE INDEX idx_form_access_form_id ON the_doller.form_access USING btree (form_id);


--
-- Name: idx_form_access_form_user; Type: INDEX; Schema: the_doller; Owner: postgres
--

CREATE INDEX idx_form_access_form_user ON the_doller.form_access USING btree (form_id, user_id);


--
-- Name: idx_form_access_user_id; Type: INDEX; Schema: the_doller; Owner: postgres
--

CREATE INDEX idx_form_access_user_id ON the_doller.form_access USING btree (user_id);


--
-- Name: notification_reads fk_notification_reads_notification; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.notification_reads
    ADD CONSTRAINT fk_notification_reads_notification FOREIGN KEY (notification_id) REFERENCES the_doller.notifications(notification_id) ON DELETE CASCADE;


--
-- Name: form_access form_access_form_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_access
    ADD CONSTRAINT form_access_form_id_fkey FOREIGN KEY (form_id) REFERENCES the_doller.form(form_id) ON DELETE CASCADE;


--
-- Name: form_field_values form_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_field_values
    ADD CONSTRAINT form_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES the_doller.form_fields(field_id);


--
-- Name: form_field_values form_field_values_submission_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_field_values
    ADD CONSTRAINT form_field_values_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES the_doller.form_submissions(submission_id);


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES the_doller.form(form_id);


--
-- Name: form_submissions form_submissions_form_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form_submissions
    ADD CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES the_doller.form(form_id);


--
-- Name: form form_task_id_fkey; Type: FK CONSTRAINT; Schema: the_doller; Owner: postgres
--

ALTER TABLE ONLY the_doller.form
    ADD CONSTRAINT form_task_id_fkey FOREIGN KEY (task_id) REFERENCES the_doller.task(task_id);


--
-- PostgreSQL database dump complete
--

