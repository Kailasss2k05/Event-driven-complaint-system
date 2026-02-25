-- ==============================
-- Event Driven Complaint System
-- Database Schema for NeonDB
-- ==============================

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id   SERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(255),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    department_id   INT REFERENCES departments(department_id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 3. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id    UUID PRIMARY KEY,
    description     TEXT NOT NULL,
    category        VARCHAR(100),
    priority        VARCHAR(20),
    severity        VARCHAR(20),
    department      VARCHAR(100),
    status          VARCHAR(30) DEFAULT 'SUBMITTED',
    assigned_to     VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 4. Complaint Events (Audit Trail)
CREATE TABLE IF NOT EXISTS complaint_events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id    UUID REFERENCES complaints(complaint_id),
    topic           VARCHAR(50) NOT NULL,
    event_data      JSONB NOT NULL,
    status          VARCHAR(30) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ==============================
-- Seed Departments
-- ==============================
INSERT INTO departments (name, email) VALUES
    ('Engineering Department', 'engineering@municipality.gov'),
    ('Health Department', 'health@municipality.gov'),
    ('Revenue Department', 'revenue@municipality.gov'),
    ('General Department', 'general@municipality.gov')
ON CONFLICT (name) DO NOTHING;

-- ==============================
-- Seed Categories
-- ==============================
INSERT INTO categories (name, department_id) VALUES
    -- Engineering Department
    ('Road Issues', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),
    ('Drainage & Buildings', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),
    ('Street Lighting & Electrical Works', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),
    ('Public Infrastructure Maintenance', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),
    ('Building Permits & Violations', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),
    ('Water Supply Infrastructure', (SELECT department_id FROM departments WHERE name = 'Engineering Department')),

    -- Health Department
    ('Solid Waste Management', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Public Health & Sanitation', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Vector Control & Disease Prevention', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Biomedical & Hazardous Waste', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Food Safety & Hygiene', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Public Toilet & Washroom Maintenance', (SELECT department_id FROM departments WHERE name = 'Health Department')),
    ('Animal & Stray Control', (SELECT department_id FROM departments WHERE name = 'Health Department')),

    -- Revenue Department
    ('Property Tax', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Other Taxes', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Trade License & Renewal', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Advertisement & Hoarding Permissions', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Birth & Death Certificates', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Land & Ownership Records', (SELECT department_id FROM departments WHERE name = 'Revenue Department')),
    ('Online Payment & Portal Issues', (SELECT department_id FROM departments WHERE name = 'Revenue Department'))
ON CONFLICT (name) DO NOTHING;

-- ==============================
-- Indexes for Performance
-- ==============================
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_department ON complaints(department);
CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority);
CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);
CREATE INDEX IF NOT EXISTS idx_complaint_events_complaint_id ON complaint_events(complaint_id);
CREATE INDEX IF NOT EXISTS idx_complaint_events_topic ON complaint_events(topic);
