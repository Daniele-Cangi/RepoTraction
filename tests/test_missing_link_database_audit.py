"""Authored isolated SQLite content/concurrency/fallback controls; no provider."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from missing_link.store import Store
from scripts import missing_link_database_audit as audit
from scripts.missing_link_cadence_checks import HistoryAudit
from scripts.missing_link_repository_only_evaluator import EvaluationStopped, verify_prefix


SERIALIZE = callable(getattr(sqlite3.Connection, 'serialize', None))


class DatabaseAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path, self.allowance = self.root/'authored.sqlite3', 'authored-allowance'
        self.store = Store(self.path, 'authored-account')
        self.store.reserve_ai_allowance(self.allowance, 'prior', .1, 10)
        self.store.put('repositories', 1, {'text': 'before é'})
        self.store.put('jobs', 'done', {'id': 'done', 'status': 'completed'})
        self.cache = audit.ContentVerifiedSnapshot(self.path, self.allowance)
        self.before = audit.database_snapshot(self.path, self.allowance)

    def verify(self, value):
        verify_prefix(self.before, value, [], allowance=self.allowance, ceiling=.1)

    def factory(self, connection):
        connect = sqlite3.connect
        return patch.object(audit.sqlite3, 'connect',
                            side_effect=lambda *a, **kw: connect(*a, **kw, factory=connection))

    def test_logical_hashes_match_independent_frozen_fetchall_encoding(self):
        with closing(sqlite3.connect(self.path)) as db:
            for name, digest in self.before['tables'].items():
                rows = db.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
                self.assertEqual(digest, hashlib.sha256(json.dumps(rows, sort_keys=True,
                                                                 ensure_ascii=False).encode()).hexdigest())

    def test_unchanged_audits_return_private_copies_and_preserve_exact_prefix(self):
        with patch.object(audit, '_logical_snapshot', wraps=audit._logical_snapshot) as scan:
            changed = self.cache()
            changed['tables'].clear()
            changed['reservation_rows'][0][2] = 'changed-returned-copy'
            changed['reserved_usd'] = 0
            for _ in range(3):
                value = self.cache()
                self.assertEqual(value, self.before)
                self.verify(value)
            self.assertEqual(scan.call_count, 1 if SERIALIZE else 4)
        counts = self.cache.snapshot()
        self.assertEqual(counts['audits'], 4)
        self.assertEqual(counts['image_reads'], 4 if SERIALIZE else 0)
        self.assertEqual(counts['cache_hits'], 3 if SERIALIZE else 0)

    def test_same_size_and_restored_mtime_cannot_hide_non_accounting_changes(self):
        self.cache()
        stamp = self.path.stat()
        self.store.put('repositories', 1, {'text': 'after! é'})
        self.assertEqual(self.path.stat().st_size, stamp.st_size)
        os.utime(self.path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        with self.assertRaises(EvaluationStopped): self.verify(self.cache())
        self.assertEqual(self.cache.snapshot()['logical_scans'], 2)

    def test_foreign_reservation_and_allowance_changes_remain_rejected(self):
        self.cache()
        self.store.reserve_ai_allowance(self.allowance, 'foreign', .001, 10)
        value = self.cache()
        self.assertEqual(value['reservations'], 2)
        with self.assertRaises(EvaluationStopped): self.verify(value)
        self.assertEqual(value, audit.database_snapshot(self.path, self.allowance))

    def test_table_addition_and_active_job_are_not_hidden_by_previous_cache(self):
        self.cache()
        self.store.put('jobs', 'active', {'id': 'active', 'status': 'running'})
        self.assertEqual(self.cache()['active_jobs'], ['active'])
        with self.assertRaises(EvaluationStopped): self.verify(self.cache())
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE ml_authored_extra (value TEXT)')
        self.assertIn('ml_authored_extra', self.cache()['tables'])
        with self.assertRaises(EvaluationStopped): self.verify(self.cache())

    def test_physical_only_change_forces_logical_rescan_without_changing_contract(self):
        self.cache()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA user_version=42')
        self.verify(self.cache())
        self.assertEqual(self.cache.snapshot()['logical_scans'], 2)

    def test_runtime_without_serialize_always_scans_full_logical_snapshot(self):
        class NoSerialize(sqlite3.Connection): serialize = None
        with self.factory(NoSerialize):
            for _ in range(3): self.assertEqual(self.cache(), self.before)
        self.assertEqual(self.cache.snapshot()['fallback_scans'], 3)
        self.assertEqual(self.cache.snapshot()['cache_hits'], 0)

    def test_oversized_image_falls_back_without_skipping_any_table(self):
        cache = audit.ContentVerifiedSnapshot(self.path, self.allowance, max_image_bytes=1)
        self.assertEqual(cache(), self.before)
        self.store.put('repositories', 1, {'text': 'changed'})
        with self.assertRaises(EvaluationStopped): self.verify(cache())
        self.assertEqual(cache.snapshot()['fallback_scans'], 2)
        self.assertEqual(cache.snapshot()['image_reads'], 0)

    @unittest.skipUnless(SERIALIZE, 'SQLite serialize unavailable on this supported runtime')
    def test_serialization_error_after_warm_cache_latches_without_old_result(self):
        self.cache()
        primary = sqlite3.OperationalError('Authored serialization fault')
        class BrokenSerialize(sqlite3.Connection):
            def serialize(self): raise primary
        with self.factory(BrokenSerialize):
            with self.assertRaises(sqlite3.OperationalError) as caught: self.cache()
        self.assertIs(caught.exception, primary)
        counts = self.cache.snapshot()
        with patch.object(audit.sqlite3, 'connect', side_effect=AssertionError('No retry')):
            with self.assertRaises(sqlite3.OperationalError) as caught: self.cache()
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.cache.snapshot(), counts)

    @unittest.skipUnless(SERIALIZE, 'SQLite serialize unavailable on this supported runtime')
    def test_invalid_serialized_image_is_global_and_never_a_hit(self):
        self.cache()
        class BrokenSerialize(sqlite3.Connection):
            def serialize(self): return b''
        with self.factory(BrokenSerialize):
            with self.assertRaises(EvaluationStopped): self.cache()
        self.assertEqual(self.cache.snapshot()['cache_hits'], 0)

    def test_failed_logical_refresh_cannot_return_old_cache_even_after_repair(self):
        self.cache()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE ml_jobs SET payload='invalid-json'")
            db.commit()
        with self.assertRaises(ValueError) as caught: self.cache()
        primary = caught.exception
        self.store.put('jobs', 'done', {'id': 'done', 'status': 'completed'})
        with self.assertRaises(ValueError) as caught: self.cache()
        self.assertIs(caught.exception, primary)

    def test_readonly_connections_cannot_mutate_database(self):
        snapshot = audit._logical_snapshot
        def inspect(db, allowance):
            with self.assertRaises(sqlite3.OperationalError): db.execute('DELETE FROM ml_ai_reservations')
            return snapshot(db, allowance)
        with patch.object(audit, '_logical_snapshot', side_effect=inspect):
            self.assertEqual(self.cache(), self.before)
        self.assertEqual(audit.database_snapshot(self.path, self.allowance), self.before)

    def test_missing_aggregate_remains_null(self):
        cache = audit.ContentVerifiedSnapshot(self.path, 'unseen-allowance')
        value = cache()
        self.assertEqual(value['reservations'], 0)
        self.assertIsNone(value['reserved_usd'])
        self.assertEqual(cache(), value)

    def test_database_replacement_between_audits_requires_new_content_verification(self):
        self.cache()
        replacement = self.root/'replacement.sqlite3'
        shutil.copyfile(self.path, replacement)  # All SQLite connections are closed.
        Store(replacement, 'authored-account').put('repositories', 1, {'text': 'replaced'})
        os.replace(replacement, self.path)
        with self.assertRaises(EvaluationStopped): self.verify(self.cache())

    def test_deleted_database_is_global_and_cannot_create_a_replacement(self):
        self.cache()
        self.path.unlink()
        with self.assertRaises(EvaluationStopped): self.cache()
        self.assertFalse(self.path.exists())
        with self.assertRaises(EvaluationStopped): self.cache()

    @unittest.skipIf(os.name == 'nt' or not SERIALIZE, 'Windows blocks replacement of an open SQLite file')
    def test_path_replacement_during_a_cache_hit_cannot_return_the_old_inode(self):
        self.cache()
        replacement = self.root/'replacement.sqlite3'
        shutil.copyfile(self.path, replacement)  # No connections are open here.
        Store(replacement, 'authored-account').put('repositories', 1, {'text': 'different inode'})
        path = self.path
        class ReplaceDuringSerialize(sqlite3.Connection):
            def serialize(inner):
                image = super().serialize()
                os.replace(replacement, path)
                return image
        with self.factory(ReplaceDuringSerialize):
            with self.assertRaises(EvaluationStopped): self.cache()
        with self.assertRaises(EvaluationStopped): self.cache()

    def test_caught_reentrant_failure_still_prevents_outer_acceptance(self):
        snapshot = audit._logical_snapshot
        def nested(db, allowance):
            with self.assertRaises(EvaluationStopped): self.cache()
            return snapshot(db, allowance)
        with patch.object(audit, '_logical_snapshot', side_effect=nested):
            with self.assertRaises(EvaluationStopped) as caught: self.cache()
        with self.assertRaises(EvaluationStopped) as repeated: self.cache()
        self.assertIs(repeated.exception, caught.exception)

    def test_compiled_history_still_checks_files_inventories_and_exact_prefix_on_hits(self):
        pinned = self.root/'evidence.txt'
        pinned.write_text('authored')
        before = dict(self.before, artifacts={'evidence.txt': hashlib.sha256(pinned.read_bytes()).hexdigest()})
        history = HistoryAudit(root=self.root, database=self.path, baseline=before,
            allowance=self.allowance, ceiling=.1, rows=lambda: [], tree=lambda: None,
            inventories=[], database_audit=self.cache)
        history(); history()
        self.store.reserve_ai_allowance(self.allowance, 'foreign', .001, 10)
        with self.assertRaises(EvaluationStopped): history()

    @unittest.skipUnless(SERIALIZE, 'SQLite serialize unavailable on this supported runtime')
    def test_wal_commit_changes_image_when_main_file_bytes_are_unchanged(self):
        # Keep this authored raw handle open until every SQLite connection has
        # closed; POSIX close() must not drop another connection's SQLite locks.
        with self.path.open('rb') as raw, closing(sqlite3.connect(self.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('PRAGMA wal_autocheckpoint=0')
            original_file = hashlib.sha256(raw.read()).digest()
            self.cache()
            writer.execute("UPDATE ml_repositories SET payload=?", (json.dumps({'text':'after! é'}),))
            writer.commit()
            raw.seek(0)
            self.assertEqual(hashlib.sha256(raw.read()).digest(), original_file)
            value = self.cache()
            with self.assertRaises(EvaluationStopped): self.verify(value)
            self.assertEqual(value, audit.database_snapshot(self.path, self.allowance))

    @unittest.skipUnless(SERIALIZE, 'SQLite serialize unavailable on this supported runtime')
    def test_wal_commit_during_serialization_preserves_reader_then_next_audit_detects_it(self):
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            self.cache()
            class CommitDuringSerialize(sqlite3.Connection):
                def serialize(inner):
                    writer.execute("UPDATE ml_repositories SET payload=?", (json.dumps({'text':'changed'}),))
                    writer.commit()
                    return super().serialize()
            with self.factory(CommitDuringSerialize):
                self.assertEqual(self.cache(), self.before)
            with self.assertRaises(EvaluationStopped): self.verify(self.cache())


if __name__ == '__main__': unittest.main()
