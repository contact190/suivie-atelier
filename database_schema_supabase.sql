-- =====================================================================
-- SUIVIPRO - SCHÉMA DE BASE DE DONNÉES CLOUD SUPABASE (POSTGRESQL)
-- 100% Compatible avec l'application SuiviPRO Atelier & Borne Face ID
-- =====================================================================

-- 1. Table des Rôles d'Atelier
CREATE TABLE IF NOT EXISTS public.roles (
    id VARCHAR(50) PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL DEFAULT '#3B82F6',
    default_pct NUMERIC(5,2) NOT NULL DEFAULT 10.00,
    icon VARCHAR(50) DEFAULT 'handyman',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Table des Employés d'Atelier
CREATE TABLE IF NOT EXISTS public.employees (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) NOT NULL,
    specialty VARCHAR(150) DEFAULT 'Opérateur atelier',
    phone VARCHAR(50),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    presence_status VARCHAR(50) NOT NULL DEFAULT 'PRESENT',
    last_punch_at VARCHAR(50),
    face_id_enrolled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employees_code ON public.employees(code);
CREATE INDEX IF NOT EXISTS idx_employees_active ON public.employees(active);

-- 3. Table des Identifiants Biométriques Face ID
CREATE TABLE IF NOT EXISTS public.face_credentials (
    employee_id VARCHAR(50) PRIMARY KEY REFERENCES public.employees(id) ON DELETE CASCADE,
    photo_data_url TEXT NOT NULL,
    enrolled_at VARCHAR(50),
    enrolled_by VARCHAR(100) DEFAULT 'ADMIN'
);

-- 4. Table des Événements d'Horodatage & Pointages
CREATE TABLE IF NOT EXISTS public.attendance_punches (
    id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
    employee_name VARCHAR(150),
    employee_code VARCHAR(50),
    punch_type VARCHAR(20) NOT NULL,
    punch_time VARCHAR(50) NOT NULL,
    time_short VARCHAR(20),
    method VARCHAR(50) DEFAULT 'FACE_ID',
    confidence NUMERIC(5,4) DEFAULT 0.980,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_punches_emp ON public.attendance_punches(employee_id);
CREATE INDEX IF NOT EXISTS idx_punches_created ON public.attendance_punches(created_at DESC);

-- 5. Table des Tables de Travail d'Atelier
CREATE TABLE IF NOT EXISTS public.workshop_tables (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Table des Affectations Multi-Rôles / Employé par Table
CREATE TABLE IF NOT EXISTS public.table_role_assignments (
    id BIGSERIAL PRIMARY KEY,
    table_id VARCHAR(50) NOT NULL REFERENCES public.workshop_tables(id) ON DELETE CASCADE,
    role_id VARCHAR(50) NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    employee_id VARCHAR(50) NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_table_role UNIQUE (table_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_table ON public.table_role_assignments(table_id);

-- 7. Table des Modèles de Menuiseries (Catalogue 32 modèles & temps cibles)
CREATE TABLE IF NOT EXISTS public.joinery_types (
    id VARCHAR(100) PRIMARY KEY,
    label VARCHAR(150) NOT NULL,
    gamme VARCHAR(100) NOT NULL,
    categorie VARCHAR(100) NOT NULL,
    has_joint_vitrage BOOLEAN DEFAULT FALSE,
    composants_count INT DEFAULT 16,
    description TEXT,
    temps_moyen_min NUMERIC(6,2) NOT NULL DEFAULT 60.00,
    ratios JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_joinery_categorie ON public.joinery_types(categorie);

-- 8. Table Configuration Kiosk
CREATE TABLE IF NOT EXISTS public.kiosk_settings (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'MAIN_KIOSK',
    kiosk_name VARCHAR(100) DEFAULT 'Borne Entrée Atelier',
    admin_pin VARCHAR(50) DEFAULT '1234',
    qr_token VARCHAR(100) DEFAULT 'kiosk_atelier_token',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- PERMISSIONS & ROW LEVEL SECURITY (RLS)
-- =====================================================================
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.face_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_punches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workshop_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.table_role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kiosk_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.joinery_types ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "suivipro_roles_policy" ON public.roles;
CREATE POLICY "suivipro_roles_policy" ON public.roles FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_employees_policy" ON public.employees;
CREATE POLICY "suivipro_employees_policy" ON public.employees FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_face_policy" ON public.face_credentials;
CREATE POLICY "suivipro_face_policy" ON public.face_credentials FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_punches_policy" ON public.attendance_punches;
CREATE POLICY "suivipro_punches_policy" ON public.attendance_punches FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_tables_policy" ON public.workshop_tables;
CREATE POLICY "suivipro_tables_policy" ON public.workshop_tables FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_assignments_policy" ON public.table_role_assignments;
CREATE POLICY "suivipro_assignments_policy" ON public.table_role_assignments FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_kiosk_policy" ON public.kiosk_settings;
CREATE POLICY "suivipro_kiosk_policy" ON public.kiosk_settings FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "suivipro_joinery_policy" ON public.joinery_types;
CREATE POLICY "suivipro_joinery_policy" ON public.joinery_types FOR ALL USING (true) WITH CHECK (true);
