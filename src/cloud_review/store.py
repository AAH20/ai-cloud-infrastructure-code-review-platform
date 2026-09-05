from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class TenantBoundaryError(PermissionError):
    pass


class ReviewStore:
    """SQLite reference store. PostgreSQL is the production adapter boundary."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    tenant_id TEXT NOT NULL,
                    delivery_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    head_sha TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, delivery_id)
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    tenant_id TEXT NOT NULL,
                    delivery_id TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, delivery_id)
                );
            """)

    def accept_delivery(self, tenant_id: str, delivery_id: str, repository: str, head_sha: str, payload: dict[str, Any]) -> bool:
        with self.connection() as connection:
            try:
                connection.execute(
                    "INSERT INTO deliveries(tenant_id, delivery_id, repository, head_sha, status, payload_json) VALUES(?,?,?,?,?,?)",
                    (tenant_id, delivery_id, repository, head_sha, "queued", json.dumps(payload, sort_keys=True)),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def supersede_older(self, tenant_id: str, repository: str, head_sha: str) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE deliveries SET status='superseded' WHERE tenant_id=? AND repository=? AND head_sha<>? AND status IN ('queued','running')",
                (tenant_id, repository, head_sha),
            )
            return cursor.rowcount

    def set_status(self, tenant_id: str, delivery_id: str, status: str) -> None:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE deliveries SET status=? WHERE tenant_id=? AND delivery_id=?",
                (status, tenant_id, delivery_id),
            )
            if cursor.rowcount != 1:
                raise TenantBoundaryError("delivery is absent or belongs to another tenant")

    def status(self, tenant_id: str, delivery_id: str) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT status FROM deliveries WHERE tenant_id=? AND delivery_id=?",
                (tenant_id, delivery_id),
            ).fetchone()
        if not row:
            raise TenantBoundaryError("delivery is absent or belongs to another tenant")
        return str(row["status"])

    def save_evidence(self, tenant_id: str, delivery_id: str, manifest: dict[str, Any]) -> None:
        with self.connection() as connection:
            delivery = connection.execute(
                "SELECT 1 FROM deliveries WHERE tenant_id=? AND delivery_id=?",
                (tenant_id, delivery_id),
            ).fetchone()
            if not delivery:
                raise TenantBoundaryError("cannot attach evidence across tenant boundary")
            connection.execute(
                "INSERT OR REPLACE INTO evidence(tenant_id, delivery_id, manifest_json) VALUES(?,?,?)",
                (tenant_id, delivery_id, json.dumps(manifest, sort_keys=True)),
            )

