-- =====================================================================
-- SUIVIPRO - SCHÉMA DE BASE DE DONNÉES POSTGRESQL / SUPABASE
-- Conforme aux standards 'supabase-postgres-best-practices' & DDD
-- =====================================================================
-- Extensions recommandées
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- Support pgvector pour embeddings Face ID (128 dimensions)

-- 1. Table des Rôles d'Atelier
CREATE TABLE IF NOT EXISTS public.roles (
    id VARCHAR(50) PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL DEFAULT '#3B82F6',
    default_pct NUMERIC(5,2) NOT NULL DEFAULT 10.00 CHECK (default_pct >= 0 AND default_pct <= 100),
    icon VARCHAR(50) DEFAULT 'handyman',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Table des Employés d'Atelier (Pointage & Présence)
CREATE TYPE employee_presence_status AS ENUM ('PRESENT', 'BREAK', 'ABSENT', 'LEFT');

CREATE TABLE IF NOT EXISTS public.employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE, -- Ex: EMP-01
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(150) DEFAULT 'Opérateur atelier',
    phone VARCHAR(30),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    current_status employee_presence_status NOT NULL DEFAULT 'ABSENT',
    last_punch_at TIMESTAMPTZ,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour recherche rapide et filtrage des actifs
CREATE INDEX IF NOT EXISTS idx_employees_code ON public.employees(code);
CREATE INDEX IF NOT EXISTS idx_employees_status ON public.employees(current_status);
CREATE INDEX IF NOT EXISTS idx_employees_active ON public.employees(is_active) WHERE is_active = TRUE;

-- 3. Table des Identifiants Biométriques (Face ID)
CREATE TABLE IF NOT EXISTS public.face_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
    -- Vecteur facial 128-D standard (ex: face_recognition, dlib, facenet, MediaPipe)
    face_embedding vector(128),
    embedding_json JSONB, -- Fallback si pgvector non actif
    photo_url TEXT, -- URL de stockage de la photo de référence
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enrolled_by_admin VARCHAR(100) DEFAULT 'ADMIN_KIOSK',
    confidence_threshold NUMERIC(4,3) DEFAULT 0.550, -- Distance maximale pour validation
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_employee_face UNIQUE (employee_id)
);

CREATE INDEX IF NOT EXISTS idx_face_credentials_emp ON public.face_credentials(employee_id);

-- 4. Table des Événements de Pointage (Horodatage officiel)
CREATE TYPE punch_type AS ENUM ('IN', 'OUT', 'BREAK_START', 'BREAK_END');
CREATE TYPE punch_method AS ENUM ('FACE_ID', 'ADMIN_OVERRIDE', 'PIN_CODE', 'QR_SCAN');

CREATE TABLE IF NOT EXISTS public.attendance_punches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
    punch_type punch_type NOT NULL,
    punch_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method punch_method NOT NULL DEFAULT 'FACE_ID',
    confidence_score NUMERIC(5,4), -- Score de confiance de reconnaissance (ex: 0.942)
    device_id VARCHAR(100) DEFAULT 'BORNE_ATELIER_01',
    snapshot_url TEXT, -- Capture optionnelle au moment du pointage
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour requêtes fréquentes de pointage par date et employé
CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON public.attendance_punches(employee_id, punch_time DESC);
CREATE INDEX IF NOT EXISTS idx_attendance_time ON public.attendance_punches(punch_time DESC);

-- 5. Table des Tables de Travail d'Atelier
CREATE TABLE IF NOT EXISTS public.workshop_tables (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Table de Liaison Multi-Rôles / Employé par Table
CREATE TABLE IF NOT EXISTS public.table_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id VARCHAR(50) NOT NULL REFERENCES public.workshop_tables(id) ON DELETE CASCADE,
    role_id VARCHAR(50) NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES public.employees(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_table_role UNIQUE (table_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_table ON public.table_role_assignments(table_id);
CREATE INDEX IF NOT EXISTS idx_assignments_employee ON public.table_role_assignments(employee_id);

-- 7. Configuration Kiosk & Sécurité Admin
CREATE TABLE IF NOT EXISTS public.kiosk_settings (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'MAIN_KIOSK',
    kiosk_name VARCHAR(100) DEFAULT 'Borne Entrée Atelier',
    admin_pin_hash VARCHAR(255) NOT NULL, -- PIN sécurisé pour accès création employé (défaut '1234')
    auto_detect_timeout_sec INT DEFAULT 5,
    allow_break_punches BOOLEAN DEFAULT TRUE,
    qr_access_token VARCHAR(255) NOT NULL DEFAULT gen_random_uuid()::text,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Données initiales par défaut
INSERT INTO public.kiosk_settings (id, kiosk_name, admin_pin_hash)
VALUES ('MAIN_KIOSK', 'Borne Entrée Atelier', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4') -- SHA-256 de '1234'
ON CONFLICT (id) DO NOTHING;

-- Trigger automatique de mise à jour du statut employé lors d'un pointage
CREATE OR REPLACE FUNCTION update_employee_punch_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.punch_type = 'IN' THEN
        UPDATE public.employees 
        SET current_status = 'PRESENT', last_punch_at = NEW.punch_time, updated_at = NOW()
        WHERE id = NEW.employee_id;
    ELSIF NEW.punch_type = 'OUT' THEN
        UPDATE public.employees 
        SET current_status = 'LEFT', last_punch_at = NEW.punch_time, updated_at = NOW()
        WHERE id = NEW.employee_id;
    ELSIF NEW.punch_type = 'BREAK_START' THEN
        UPDATE public.employees 
        SET current_status = 'BREAK', last_punch_at = NEW.punch_time, updated_at = NOW()
        WHERE id = NEW.employee_id;
    ELSIF NEW.punch_type = 'BREAK_END' THEN
        UPDATE public.employees 
        SET current_status = 'PRESENT', last_punch_at = NEW.punch_time, updated_at = NOW()
        WHERE id = NEW.employee_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_after_punch ON public.attendance_punches;
CREATE TRIGGER trg_after_punch
AFTER INSERT ON public.attendance_punches
FOR EACH ROW
EXECUTE FUNCTION update_employee_punch_status();
