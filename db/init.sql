-- ============================================================
-- Budget-Planer Datenbankschema
-- ============================================================

-- Nutzerverwaltung (owned by auth service)
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Monats-Tabs (ein Tab pro Nutzer und Monat)
CREATE TABLE IF NOT EXISTS budget_tabs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    locked      BOOLEAN DEFAULT FALSE,
    fixed_title VARCHAR(200) DEFAULT 'Fixkosten',
    pots_title  VARCHAR(200) DEFAULT 'Spartöpfe',
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, year, month)
);

-- Einnahmen
CREATE TABLE IF NOT EXISTS income_items (
    id          SERIAL PRIMARY KEY,
    tab_id      INTEGER REFERENCES budget_tabs(id) ON DELETE CASCADE,
    sort_order  INTEGER DEFAULT 0,
    name        VARCHAR(300) NOT NULL,
    amount      NUMERIC(15,2) DEFAULT 0,
    level       INTEGER DEFAULT 0
);

-- Fixkosten
CREATE TABLE IF NOT EXISTS fixed_expense_items (
    id          SERIAL PRIMARY KEY,
    tab_id      INTEGER REFERENCES budget_tabs(id) ON DELETE CASCADE,
    sort_order  INTEGER DEFAULT 0,
    name        VARCHAR(300) NOT NULL,
    amount      NUMERIC(15,2) DEFAULT 0,
    level       INTEGER DEFAULT 0
);

-- Spartöpfe
CREATE TABLE IF NOT EXISTS pot_items (
    id          SERIAL PRIMARY KEY,
    tab_id      INTEGER REFERENCES budget_tabs(id) ON DELETE CASCADE,
    sort_order  INTEGER DEFAULT 0,
    name        VARCHAR(300) NOT NULL,
    amount      NUMERIC(15,2) DEFAULT 0,
    level       INTEGER DEFAULT 0
);

-- Überschussverteilung
CREATE TABLE IF NOT EXISTS surplus_items (
    id             SERIAL PRIMARY KEY,
    tab_id         INTEGER REFERENCES budget_tabs(id) ON DELETE CASCADE,
    sort_order     INTEGER DEFAULT 0,
    name           VARCHAR(300) NOT NULL,
    monthly_amount NUMERIC(15,2) DEFAULT 0,
    strategy       VARCHAR(200) DEFAULT '',
    current_value  NUMERIC(15,2),
    level          INTEGER DEFAULT 0,
    paid_override  NUMERIC(15,2),
    paid_out       NUMERIC(15,2)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_budget_tabs_user  ON budget_tabs(user_id);
CREATE INDEX IF NOT EXISTS idx_income_tab        ON income_items(tab_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_fixed_tab         ON fixed_expense_items(tab_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_pot_tab           ON pot_items(tab_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_surplus_tab       ON surplus_items(tab_id, sort_order);
