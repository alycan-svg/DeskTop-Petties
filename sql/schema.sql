-- Shared Persona Core database schema for Supabase PostgreSQL.
-- Run this file in the Supabase SQL Editor for Step 2.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS worlds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS world_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    mood TEXT NOT NULL DEFAULT 'curious',
    color TEXT NOT NULL DEFAULT 'blue',
    animation TEXT NOT NULL DEFAULT 'idle',
    energy INTEGER NOT NULL DEFAULT 70 CHECK (energy BETWEEN 0 AND 100),
    friendliness INTEGER NOT NULL DEFAULT 60 CHECK (friendliness BETWEEN 0 AND 100),
    curiosity INTEGER NOT NULL DEFAULT 80 CHECK (curiosity BETWEEN 0 AND 100),
    chaos INTEGER NOT NULL DEFAULT 20 CHECK (chaos BETWEEN 0 AND 100),
    stress INTEGER NOT NULL DEFAULT 30 CHECK (stress BETWEEN 0 AND 100),
    loneliness INTEGER NOT NULL DEFAULT 10 CHECK (loneliness BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (world_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL CHECK (char_length(content) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (char_length(content) > 0),
    memory_type TEXT NOT NULL DEFAULT 'general',
    importance INTEGER NOT NULL DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    emotion TEXT,
    source_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    description TEXT,
    due_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS set_worlds_updated_at ON worlds;
CREATE TRIGGER set_worlds_updated_at
BEFORE UPDATE ON worlds
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_world_state_updated_at ON world_state;
CREATE TRIGGER set_world_state_updated_at
BEFORE UPDATE ON world_state
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_memories_updated_at ON memories;
CREATE TRIGGER set_memories_updated_at
BEFORE UPDATE ON memories
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_tasks_updated_at ON tasks;
CREATE TRIGGER set_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_messages_world_created_at
    ON messages (world_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memories_world_importance_created_at
    ON memories (world_id, importance DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memories_world_type
    ON memories (world_id, memory_type);

CREATE INDEX IF NOT EXISTS idx_tasks_world_status_due_at
    ON tasks (world_id, status, due_at);

CREATE INDEX IF NOT EXISTS idx_system_events_world_created_at
    ON system_events (world_id, created_at DESC);

INSERT INTO worlds (id, name, description)
VALUES (
    'shared_world',
    'Shared Persona Core',
    'A shared cloud soul collectively fed by all users and connected to the desktop pet.'
)
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description;

INSERT INTO world_state (
    world_id,
    mood,
    color,
    animation,
    energy,
    friendliness,
    curiosity,
    chaos,
    stress,
    loneliness
)
VALUES (
    'shared_world',
    'curious',
    'blue',
    'idle',
    70,
    60,
    80,
    20,
    30,
    10
)
ON CONFLICT (world_id) DO NOTHING;
