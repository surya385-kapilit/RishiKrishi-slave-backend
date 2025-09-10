--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 17.2

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
-- Name: apple; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA apple;


ALTER SCHEMA apple OWNER TO postgres;

--
-- Name: access_type_enum; Type: TYPE; Schema: apple; Owner: postgres
--

CREATE TYPE apple.access_type_enum AS ENUM (
    'individual',
    'all'
);


ALTER TYPE apple.access_type_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: form; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.form (
    form_id uuid NOT NULL,
    task_id uuid,
    title text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE apple.form OWNER TO postgres;

--
-- Name: form_access; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.form_access (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    form_id uuid,
    user_id uuid,
    access_type apple.access_type_enum DEFAULT 'all'::apple.access_type_enum NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE apple.form_access OWNER TO postgres;

--
-- Name: form_field_values; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.form_field_values (
    id uuid NOT NULL,
    submission_id uuid,
    field_id uuid,
    value_text text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE apple.form_field_values OWNER TO postgres;

--
-- Name: form_fields; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.form_fields (
    field_id uuid NOT NULL,
    form_id uuid,
    name text NOT NULL,
    field_type text NOT NULL,
    is_required boolean DEFAULT false,
    field_options jsonb
);


ALTER TABLE apple.form_fields OWNER TO postgres;

--
-- Name: form_submissions; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.form_submissions (
    submission_id uuid NOT NULL,
    form_id uuid,
    submitted_by uuid,
    submitted_at timestamp without time zone DEFAULT now(),
    flagged boolean DEFAULT false
);


ALTER TABLE apple.form_submissions OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.notifications (
    notification_id bigint NOT NULL,
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    task_id uuid,
    is_read boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE apple.notifications OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE; Schema: apple; Owner: postgres
--

ALTER TABLE apple.notifications ALTER COLUMN notification_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME apple.notifications_notification_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: task; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.task (
    task_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE apple.task OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: apple; Owner: postgres
--

CREATE TABLE apple.users (
    id integer NOT NULL,
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    role character varying(50),
    phone character varying(14),
    status character varying(50) DEFAULT 'active'::character varying,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE apple.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: apple; Owner: postgres
--

CREATE SEQUENCE apple.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE apple.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: apple; Owner: postgres
--

ALTER SEQUENCE apple.users_id_seq OWNED BY apple.users.id;


--
-- Name: users id; Type: DEFAULT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.users ALTER COLUMN id SET DEFAULT nextval('apple.users_id_seq'::regclass);


--
-- Name: form_access form_access_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_access
    ADD CONSTRAINT form_access_pkey PRIMARY KEY (access_id);


--
-- Name: form_field_values form_field_values_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_field_values
    ADD CONSTRAINT form_field_values_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (field_id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (form_id);


--
-- Name: form_submissions form_submissions_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_submissions
    ADD CONSTRAINT form_submissions_pkey PRIMARY KEY (submission_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_form_access_form_id; Type: INDEX; Schema: apple; Owner: postgres
--

CREATE INDEX idx_form_access_form_id ON apple.form_access USING btree (form_id);


--
-- Name: idx_form_access_form_user; Type: INDEX; Schema: apple; Owner: postgres
--

CREATE INDEX idx_form_access_form_user ON apple.form_access USING btree (form_id, user_id);


--
-- Name: idx_form_access_user_id; Type: INDEX; Schema: apple; Owner: postgres
--

CREATE INDEX idx_form_access_user_id ON apple.form_access USING btree (user_id);


--
-- Name: form_access form_access_form_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_access
    ADD CONSTRAINT form_access_form_id_fkey FOREIGN KEY (form_id) REFERENCES apple.form(form_id) ON DELETE CASCADE;


--
-- Name: form_field_values form_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_field_values
    ADD CONSTRAINT form_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES apple.form_fields(field_id);


--
-- Name: form_field_values form_field_values_submission_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_field_values
    ADD CONSTRAINT form_field_values_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES apple.form_submissions(submission_id);


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES apple.form(form_id);


--
-- Name: form_submissions form_submissions_form_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form_submissions
    ADD CONSTRAINT form_submissions_form_id_fkey FOREIGN KEY (form_id) REFERENCES apple.form(form_id);


--
-- Name: form form_task_id_fkey; Type: FK CONSTRAINT; Schema: apple; Owner: postgres
--

ALTER TABLE ONLY apple.form
    ADD CONSTRAINT form_task_id_fkey FOREIGN KEY (task_id) REFERENCES apple.task(task_id);


--
-- PostgreSQL database dump complete
--

