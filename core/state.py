"""
State Manager da Laura — camada SQLite (Fase 2).

Substitui os JSONs operacionais por um banco local com garantias ACID.
Tabelas: jobs (rotinas compostas), steps (resultados por etapa), artifacts.
Tudo que a Laura produz fica auditável aqui.
"""

import os
import sqlite3
import json
import datetime
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "laura.db")

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    params TEXT DEFAULT '{}',
    status TEXT DEFAULT 'running',
    created_at TEXT,
    finished_at TEXT,
    summary TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    step_num INTEGER NOT NULL,
    skill TEXT NOT NULL,
    status TEXT DEFAULT 'ok',
    data TEXT DEFAULT '{}',
    output TEXT DEFAULT '',
    created_at TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    kind TEXT DEFAULT 'file',
    created_at TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_steps_job ON steps(job_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_job ON artifacts(job_id);
"""

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class StateManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_schema()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with _lock:
            conn = self._conn()
            try:
                conn.executescript(_SCHEMA)
                conn.commit()
            finally:
                conn.close()

    def create_job(self, job_type, params=None):
        with _lock:
            conn = self._conn()
            try:
                cur = conn.execute(
                    "INSERT INTO jobs (type, params, status, created_at) VALUES (?, ?, 'running', ?)",
                    (job_type, json.dumps(params or {}, ensure_ascii=False), _now())
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

    def finish_job(self, job_id, status="done", summary=""):
        with _lock:
            conn = self._conn()
            try:
                conn.execute(
                    "UPDATE jobs SET status=?, finished_at=?, summary=? WHERE id=?",
                    (status, _now(), summary, job_id)
                )
                conn.commit()
            finally:
                conn.close()

    def get_job(self, job_id):
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return None
            job = dict(row)
            job["params"] = json.loads(job.get("params") or "{}")
            steps = [dict(r) for r in conn.execute(
                "SELECT * FROM steps WHERE job_id=? ORDER BY step_num", (job_id,)).fetchall()]
            for s in steps:
                try: s["data"] = json.loads(s.get("data") or "{}")
                except Exception: s["data"] = {}
            job["steps"] = steps
            job["artifacts"] = [dict(r) for r in conn.execute(
                "SELECT * FROM artifacts WHERE job_id=?", (job_id,)).fetchall()]
            return job
        finally:
            conn.close()

    def list_jobs(self, limit=20, status=None):
        conn = self._conn()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status=? ORDER BY id DESC LIMIT ?",
                    (status, limit)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_step(self, job_id, step_num, skill, status="ok", data=None, output=""):
        """Registra o resultado REAL (estruturado) de uma etapa."""
        with _lock:
            conn = self._conn()
            try:
                conn.execute(
                    "INSERT INTO steps (job_id, step_num, skill, status, data, output, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (job_id, step_num, skill, status,
                     json.dumps(data or {}, ensure_ascii=False), str(output)[:2000], _now())
                )
                conn.commit()
            finally:
                conn.close()

    def add_artifact(self, job_id, path, kind="file"):
        with _lock:
            conn = self._conn()
            try:
                conn.execute(
                    "INSERT INTO artifacts (job_id, path, kind, created_at) VALUES (?, ?, ?, ?)",
                    (job_id, path, kind, _now())
                )
                conn.commit()
            finally:
                conn.close()

# Instância global (thread-safe: locks + conexões por chamada)
state = StateManager()
