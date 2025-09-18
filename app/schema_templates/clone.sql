
-- set this for the new schema
-- ALTER TABLE public.--table_nmae--
-- ALTER COLUMN created_at SET DEFAULT (NOW() AT TIME ZONE 'Asia/Kolkata');

-- ALTER TABLE salaar2.notifications add column submission_id UUID    this should add in the notifications table


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50),
    phone VARCHAR(14),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);


CREATE TABLE task (
    task_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE form (
    form_id UUID PRIMARY KEY,
    task_id UUID REFERENCES task(task_id),
    title TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE
);
CREATE TABLE form_fields (
    field_id UUID PRIMARY KEY,
    form_id UUID REFERENCES form(form_id),
    name TEXT NOT NULL,
    field_type TEXT NOT NULL, -- text/number/date/radio/checkbox/mcq
    is_required BOOLEAN DEFAULT FALSE,
    field_options JSONB -- options for radio, checkbox, mcq
);

create type flag_status as enum('none','raised','approved','rejected')
CREATE TABLE form_submissions (
    submission_id UUID PRIMARY KEY,
    form_id UUID REFERENCES form(form_id),
    submitted_by UUID REFERENCES users(id),
    submitted_at TIMESTAMP DEFAULT now(),
    flagged flag_status DEFAULT 'none',
);



CREATE TABLE form_field_values (
    id UUID PRIMARY KEY,
    submission_id UUID REFERENCES form_submissions(submission_id),
    field_id UUID REFERENCES form_fields(field_id),
    value_text TEXT,
    -- value_json JSONB,
    created_at TIMESTAMP DEFAULT now()
);



-- Enum type inside template_schema
CREATE TYPE template_schema.access_type_enum AS ENUM ('individual', 'all','none');

-- Table using enum
CREATE TABLE form_access (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID REFERENCES template_schema.form(form_id) ON DELETE CASCADE,
    user_id UUID REFERENCES template_schema.users(id) ON DELETE CASCADE,
    access_type template_schema.access_type_enum NOT NULL DEFAULT 'none',
    assign_by UUID REFERENCES template_schema.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_form_access_form_id ON template_schema.form_access(form_id);
CREATE INDEX idx_form_access_user_id ON template_schema.form_access(user_id);
CREATE INDEX idx_form_access_form_user ON template_schema.form_access(form_id, user_id);



-- Notifications table
CREATE TABLE notifications (
    notification_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id             INT NOT NULL,
    title               VARCHAR(255) NOT NULL,
    message             TEXT NOT NULL,
    form_id             UUID,
    created_by          UUID
    is_read             BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notify_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    CONSTRAINT fk_notify_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_notify_task FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
);