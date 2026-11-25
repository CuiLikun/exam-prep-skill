import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inventory = load("inventory", "skills/exam-prep/scripts/inventory.py")
builder = load("build_pdf", "skills/exam-prep/scripts/build_pdf.py")
installer = load("install_skill", "scripts/install.py")


class InventoryTests(unittest.TestCase):
    def test_mixed_formats_duplicates_and_stable_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "课程.md").write_text("矩阵", encoding="utf-8")
            (root / "副本.md").write_text("矩阵", encoding="utf-8")
            (root / "scan.PDF").write_bytes(b"%PDF-dummy")
            (root / "strange.xyz").write_bytes(b"unknown")
            result = inventory.collect(root)
            rows = {row["path"]: row for row in result["sources"]}
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows["scan.PDF"]["kind"], "pdf")
            self.assertEqual(rows["strange.xyz"]["kind"], "unknown")
            self.assertTrue(all(row["status"] == "pending" for row in rows.values()))
            copies = [row for row in rows.values() if row["duplicate_of"]]
            self.assertEqual(len(copies), 1)
            self.assertIn(copies[0]["duplicate_of"], {row["id"] for row in rows.values()})
            (root / "aaa.txt").write_text("new", encoding="utf-8")
            after = {row["path"]: row for row in inventory.collect(root)["sources"]}
            self.assertEqual(rows["课程.md"]["id"], after["课程.md"]["id"])

    def test_excludes_generated_output_and_selected_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("exam-prep-output", ".git", "skip", "keep"):
                (root / name).mkdir()
                (root / name / "file.md").write_text("content", encoding="utf-8")
            output = root / "sources.json"
            output.write_text("{}", encoding="utf-8")
            rows = inventory.collect(root, ["skip"], output)["sources"]
            self.assertEqual([row["path"] for row in rows], ["keep/file.md"])

    def test_bad_root_and_outside_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                inventory.collect(root, ["../outside"])
            with self.assertRaises(FileNotFoundError):
                inventory.collect(root / "missing")

    def test_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "real.txt").write_text("text", encoding="utf-8")
            try:
                (root / "link.txt").symlink_to(root / "real.txt")
            except OSError:
                self.skipTest("Symlinks are unavailable for this account.")
            result = inventory.collect(root)
            self.assertEqual(len(result["sources"]), 1)
            self.assertEqual(result["skipped"][0]["path"], "link.txt")

    def test_cli_preserves_existing_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "sources.json"
            output.write_text("keep", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "skills/exam-prep/scripts/inventory.py"),
                 str(root), "--output", str(output)], capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_resume_uses_only_unchanged_reading_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("notes", "exam", "slides", "removed"):
                (root / name).write_text(name, encoding="utf-8")
            prior = inventory.collect(root)
            for row in prior["sources"]:
                row.update(status="partial" if row["path"] == "slides" else "extracted",
                           coverage="section 1", locator="section", issues=["check figure"])
            previous = root / "previous.json"
            previous.write_text(json.dumps(prior), encoding="utf-8")
            (root / "notes").write_text("revised", encoding="utf-8")
            (root / "removed").unlink()
            (root / "extra").write_text("new", encoding="utf-8")
            shutil.copyfile(root / "exam", root / "a-copy")
            output = root / "next.json"
            command = [sys.executable, str(ROOT / "skills/exam-prep/scripts/inventory.py"),
                       str(root), "--reuse-from", str(previous), "--output"]
            subprocess.run(command + [str(output)], check=True, capture_output=True)
            rows = {row["path"]: row for row in json.loads(output.read_text(encoding="utf-8"))["sources"]}
            self.assertEqual(set(rows), {"exam", "notes", "slides", "extra", "a-copy"})
            self.assertEqual(rows["exam"]["status"], "extracted")
            self.assertEqual(rows["slides"]["status"], "partial")
            self.assertEqual(rows["slides"]["coverage"], "section 1")
            self.assertEqual(rows["slides"]["issues"], ["check figure"])
            self.assertEqual(rows["slides"]["locator"], "section")
            self.assertIsNone(rows["exam"]["duplicate_of"])
            self.assertEqual(rows["a-copy"]["duplicate_of"], rows["exam"]["id"])
            for name in ("notes", "extra", "a-copy"):
                self.assertEqual(rows[name]["status"], "pending")
                self.assertIsNone(rows[name]["coverage"])
            rejected = subprocess.run(command + [str(previous), "--overwrite"], capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(json.loads(previous.read_text(encoding="utf-8")), prior)

    def test_resume_rejects_unrelated_or_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = inventory.collect(root)
            previous = root / "previous.json"
            for change in ({"input_root": "../other"}, {"schema_version": 2}, {"sources": [None]}):
                previous.write_text(json.dumps({**current, **change}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    inventory.reuse_progress(current, previous)


class InstallerTests(unittest.TestCase):
    def test_both_installations_are_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            targets = installer.destinations("both", home=temp)
            installer.install(targets)
            for target in targets:
                self.assertEqual((target / "SKILL.md").read_bytes(), (installer.SOURCE / "SKILL.md").read_bytes())
                self.assertTrue((target / "scripts/build_pdf.py").is_file())
                self.assertTrue((target / "references/ingestion.md").is_file())

    def test_collision_preflight_preserves_existing_and_does_not_half_install(self):
        with tempfile.TemporaryDirectory() as temp:
            targets = installer.destinations("both", home=temp)
            targets[1].mkdir(parents=True)
            existing = targets[1] / "custom.txt"
            existing.write_text("user edits", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install(targets)
            self.assertFalse(targets[0].exists())
            self.assertEqual(existing.read_text(encoding="utf-8"), "user edits")

    def test_destination_inside_source_is_rejected(self):
        with self.assertRaises(ValueError):
            installer.install([installer.SOURCE / "nested" / "exam-prep"])

    def test_custom_destination_requires_one_tool(self):
        with self.assertRaises(ValueError):
            installer.destinations("both", dest="custom")


class PDFTests(unittest.TestCase):
    def test_missing_engine_reports_dependency_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.tex"
            source.write_text("document", encoding="utf-8")
            with patch.object(builder.shutil, "which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "XeLaTeX not found"):
                    builder.build(source, root / "out.pdf")
            self.assertFalse((root / "out.pdf").exists())

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source.tex", root / "out.pdf"
            source.write_text("document", encoding="utf-8")
            output.write_bytes(b"existing PDF")
            with self.assertRaises(ValueError):
                builder.build(source, output)
            self.assertEqual(output.read_bytes(), b"existing PDF")

    @unittest.skipUnless(shutil.which("xelatex"), "XeLaTeX is not installed.")
    def test_compiles_chinese_and_math(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "中文.pdf"
            builder.build(ROOT / "skills/exam-prep/assets/document-template.tex", output)
            self.assertTrue(output.read_bytes().startswith(b"%PDF-"))
            self.assertGreater(output.stat().st_size, 1000)
            log = output.with_suffix(".build.log").read_text(encoding="utf-8")
            self.assertNotIn("Missing character:", log)
            if importlib.util.find_spec("pymupdf"):
                import pymupdf
                with pymupdf.open(output) as document:
                    self.assertIn("期末复习材料", document[0].get_text())
            elif importlib.util.find_spec("pypdfium2"):
                import pypdfium2
                document = pypdfium2.PdfDocument(output)
                try:
                    self.assertIn("期末复习材料", document[0].get_textpage().get_text_bounded())
                finally:
                    document.close()
            elif shutil.which("pdftotext"):
                extracted = subprocess.run(
                    ["pdftotext", "-enc", "UTF-8", str(output), "-"],
                    capture_output=True, encoding="utf-8", check=True,
                )
                if "Missing language pack" in extracted.stderr:
                    self.skipTest("PDF compiled; text verification needs Poppler CJK data or PyMuPDF.")
                self.assertIn("期末复习材料", extracted.stdout)

    @unittest.skipUnless(shutil.which("xelatex"), "XeLaTeX is not installed.")
    def test_missing_glyph_preserves_existing_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "missing.tex", root / "out.pdf"
            source.write_text(
                r'\documentclass{article}\begin{document}Q\char"10FFFD\relax\end{document}',
                encoding="utf-8",
            )
            output.write_bytes(b"previous")
            with self.assertRaisesRegex(RuntimeError, "Missing character"):
                builder.build(source, output, overwrite=True)
            self.assertEqual(output.read_bytes(), b"previous")
            self.assertIn("Missing character:", output.with_suffix(".build.log").read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("xelatex"), "XeLaTeX is not installed.")
    def test_compile_error_keeps_old_pdf_and_saves_log(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "broken.tex", root / "out.pdf"
            source.write_text(
                "\\documentclass{article}\\begin{document}\\undefinedExamPrepCommand\\end{document}",
                encoding="utf-8",
            )
            output.write_bytes(b"keep existing PDF")
            with self.assertRaises(RuntimeError):
                builder.build(source, output, overwrite=True)
            self.assertEqual(output.read_bytes(), b"keep existing PDF")
            self.assertIn("Undefined control sequence", " ".join(output.with_suffix(".build.log").read_text(encoding="utf-8").split()))


if __name__ == "__main__":
    unittest.main()
