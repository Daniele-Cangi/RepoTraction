"""Authored source ownership/provenance controls; no semantic gold classifier."""
import copy
import hashlib
import importlib
import json
import unittest
from unittest.mock import patch

from missing_link.provider import Provider
from scripts import missing_link_triage_prospective_sources as task


def source(text='def chosen(value):\n    """Return the supplied value."""\n    return value\n', path="src/example.py"):
    body = text.encode()
    return {"repository": "fixture/library", "revision": "a" * 40, "path": path, "text": text,
        "blob_sha": hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest(),
        "sha256": hashlib.sha256(body).hexdigest()}


class ProspectiveSourcesTests(unittest.TestCase):
    def test_complete_source_hashes_are_checked_without_mutation(self):
        record = source()
        saved = copy.deepcopy(record)
        self.assertEqual(task.validate_source(record), saved)
        self.assertEqual(record, saved)
        for field in ("text", "blob_sha", "sha256"):
            bad = {**record, field: record[field] + "changed"}
            with self.subTest(field=field), self.assertRaises(ValueError):
                task.validate_source(bad)

    def test_revision_repository_path_and_missing_fields_are_rejected(self):
        for field, value in (("revision", "main"), ("revision", "a" * 39),
                ("repository", "owner/repo/extra"), ("repository", "https://host/repo"),
                ("path", "/outside.py"), ("path", "../outside.py"),
                ("path", "src\\outside.py"), ("path", "src/./example.py"), ("text", 1)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                task.validate_source({**source(), field: value})
        bad = source()
        del bad["blob_sha"]
        with self.assertRaises(ValueError):
            task.validate_source(bad)

    def test_file_bound_rejects_without_truncation(self):
        with patch.object(task, "MAX_FILE_BYTES", 5), self.assertRaisesRegex(ValueError, "bound"):
            task.validate_source(source())

    def test_full_decorated_function_includes_nested_body_not_sibling(self):
        text = 'import unknown\n@unknown.decorator()\ndef chosen(value):\n    """Return a callable."""\n    def later(path):\n        return unknown.copy(path)\n    return later\n\ndef sibling():\n    return "not owned"\n'
        _, _, evidence = task.function_source(source(text), "chosen")
        self.assertEqual(evidence["line"], 2)
        self.assertEqual(evidence["end_line"], 7)
        self.assertEqual(evidence["quote"], "\n".join(text.splitlines()[1:7]))
        self.assertNotIn("sibling", evidence["quote"])

    def test_utf8_ast_columns_keep_complete_unicode_end_of_function(self):
        text = 'async def chosen():\n    """Résumé 😀."""\n    return "é😀"\n'
        _, _, evidence = task.function_source(source(text), "chosen")
        self.assertEqual(evidence["quote"], text.rstrip("\n"))

    def test_crlf_is_preserved_in_original_body_and_contract(self):
        text = 'def chosen(value):\r\n    """Original\r\n    contract."""\r\n    return value\r\n'
        record = source(text)
        case = task.documented_case(1, record, "chosen", demand_record=record, demand_function="chosen")
        self.assertEqual(case["operation_body"], text.rstrip("\r\n"))
        self.assertEqual(case["demand_sources"]["q0"], '"""Original\r\n    contract."""')

    def test_missing_duplicate_nested_or_class_function_is_not_selected(self):
        for text in ('def other():\n    pass\n', 'def chosen():\n    pass\ndef chosen():\n    pass\n',
                'def outer():\n    def chosen():\n        pass\n', 'class Parent:\n    def chosen(self):\n        pass\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                task.function_source(source(text), "chosen")

    def test_docstring_literal_is_exact_original_source_not_cleaned_or_decoded(self):
        text = 'def chosen():\n    r"""A \\n sequence.\n    Keep indentation."""\n    return None\n'
        record = source(text)
        case = task.documented_case(1, record, "chosen", demand_record=record, demand_function="chosen")
        self.assertEqual(case["demand_sources"]["q0"], 'r"""A \\n sequence.\n    Keep indentation."""')
        joined = "".join(span["quote"] for span in case["data"]["demand_spans"].values())
        self.assertEqual(joined, case["demand_sources"]["q0"])

    def test_missing_empty_or_non_docstring_contract_rejects(self):
        for text in ('def chosen():\n    return 1\n', 'def chosen():\n    "  "\n    return 1\n',
                'def chosen():\n    12\n    return 1\n'):
            record = source(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                task.documented_case(1, record, "chosen", demand_record=record, demand_function="chosen")

    def test_whole_document_is_preserved_without_external_reference_fetch(self):
        operation, demand = source(), source("Full documentation\n\nhttps://example.invalid/omitted\n", "README.rst")
        case = task.documented_case(4, operation, "chosen", demand_record=demand)
        self.assertEqual(case["demand_sources"]["q0"], demand["text"])
        self.assertFalse(case["data"]["acquisition_complete"])
        self.assertIn("not an external unresolved issue", " ".join(case["data"]["acquisition_limitations"]))
        self.assertIn("/" + "a" * 40 + "/README.rst", case["source_url"])

    def test_contract_and_operation_must_share_pinned_repository_revision(self):
        for field, value in (("repository", "different/project"), ("revision", "b" * 40)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                task.documented_case(1, source(), "chosen", demand_record={**source(), field: value})

    def test_review_predictions_and_extra_metadata_never_enter_model_context(self):
        record = {**source(), "reviewer_judgments": {"outcome": "sentinel-label"},
            "raw_prediction": "sentinel-prediction", "credential": "sentinel-credential"}
        saved = copy.deepcopy(record)
        case = task.documented_case(1, record, "chosen", demand_record=record, demand_function="chosen")
        encoded = json.dumps(case)
        for marker in ("sentinel-label", "sentinel-prediction", "sentinel-credential"):
            self.assertNotIn(marker, encoded)
        self.assertEqual(record, saved)

    def test_different_documented_operation_is_not_silently_substituted(self):
        text = 'def chosen(value):\n    """Choose one value."""\n    return value\n\ndef flatten(values):\n    """Flatten all nested values."""\n    return unknown(values)\n'
        record = source(text)
        case = task.documented_case(6, record, "chosen", demand_record=record, demand_function="flatten")
        self.assertIn("Flatten all nested", case["demand_sources"]["q0"])
        self.assertNotIn("def flatten", case["operation_body"])
        self.assertEqual(case["data"]["selected_entrypoint"], "src/example.py:chosen")

    def test_long_operation_spans_cover_every_character_without_truncation(self):
        text = 'def chosen(value):\n    """A contract."""\n' + '    # original é😀\n' * 140 + '    return value\n'
        record = source(text)
        case = task.documented_case(1, record, "chosen", demand_record=record, demand_function="chosen")
        offset = 0
        for key, span in case["operation_spans"].items():
            self.assertEqual(span["start"], offset)
            self.assertLessEqual(len(span["quote"]), task.OPERATION_SPAN_CHARACTERS)
            self.assertEqual(span["quote"], case["operation_body"][span["start"]:span["end"]])
            self.assertEqual(span["quote"], case["data"]["operation_evidence"][key]["quote"])
            offset = span["end"]
        self.assertEqual(offset, len(case["operation_body"]))
        self.assertEqual("".join(span["quote"] for span in case["operation_spans"].values()), case["operation_body"])
        self.assertGreater(len(case["operation_spans"]), 1)

    def test_operation_body_bound_rejects_not_truncates(self):
        with patch.object(task, "MAX_BODY_BYTES", 5), self.assertRaisesRegex(ValueError, "body bound"):
            task.documented_case(1, source(), "chosen", demand_record=source(), demand_function="chosen")

    def test_case_numbers_are_bounded_and_not_booleans(self):
        for number in (0, 7, True, 1.0, "1"):
            with self.subTest(number=number), self.assertRaises(ValueError):
                task.documented_case(number, source(), "chosen", demand_record=source())

    def test_acquired_python_is_parsed_never_executed(self):
        text = 'raise RuntimeError("do not execute")\ndef chosen():\n    """No execution."""\n    raise RuntimeError("do not call")\n'
        record = source(text)
        self.assertIn("do not call", task.documented_case(1, record, "chosen",
            demand_record=record, demand_function="chosen")["operation_body"])

    def test_import_performs_no_io_provider_or_credential_lookup(self):
        with patch("builtins.open", side_effect=AssertionError("file")), \
             patch("os.getenv", side_effect=AssertionError("environment")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("sqlite3.connect", side_effect=AssertionError("database")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch.object(Provider, "__init__", side_effect=AssertionError("provider")):
            importlib.reload(task)
