#!/usr/bin/env python3
"""Synthetic stdlib tests for check_clean_source.py; no application imports."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'clean_source', Path(__file__).with_name('check_clean_source.py'))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class CleanSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='edw-clean-source-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in CHECK.ENTRYPOINTS:
            self.put(name, 'Current instructions: INSTALL.md\n')

    def put(self, name, text):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return target

    def run_check(self):
        paths = [str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file()]
        return CHECK.check_tree(self.root, paths)

    def assert_problem(self, report, path, code):
        self.assertFalse(report['ok'])
        self.assertTrue(any(item['path'] == path and item['code'] == code
                            for item in report['problems']), report)

    def test_clean_supported_tree(self):
        self.put('backend/edw/__init__.py', '# supported source\n')
        self.assertTrue(self.run_check()['ok'])

    def test_removed_directories_and_file_are_refused(self):
        for name in CHECK.REMOVED:
            with self.subTest(path=name):
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if name.endswith('.txt'):
                    target.write_text('old guide')
                else:
                    target.mkdir()
                report = self.run_check()
                self.assertFalse(report['ok'])
                self.assertIn({'path': name, 'code': 'removed_path_present'}, report['problems'])
                if target.is_file():
                    target.unlink()
                else:
                    target.rmdir()

    def test_missing_entrypoint_refused(self):
        (self.root / 'INSTALL.md').unlink()
        self.assertFalse(self.run_check()['ok'])

    def test_missing_redirect_refused(self):
        self.put('backend/docs/install.txt', 'stale instructions\n')
        self.assertFalse(self.run_check()['ok'])

    def test_active_document_reference_refused(self):
        self.put('docs/howto.md', 'pip install -r backend/requirements/django19/common.txt\n')
        self.assert_problem(self.run_check(), 'docs/howto.md', 'active_legacy_reference')

    def test_active_code_import_refused(self):
        self.put('backend/edw/example.py', 'from sandbox.sample import apps\n')
        self.assert_problem(self.run_check(), 'backend/edw/example.py', 'active_legacy_reference')

    def test_bare_demo_imports_refused(self):
        for statement in ('from sample.models.book import Book', 'from todos import Todo'):
            with self.subTest(statement=statement):
                self.put('backend/edw/example.py', statement + '\n')
                self.assert_problem(self.run_check(), 'backend/edw/example.py', 'active_legacy_reference')

    def test_demo_settings_namespace_refused(self):
        self.put('docs/howto.md', 'DJANGO_SETTINGS_MODULE=todos.settings\n')
        self.assert_problem(self.run_check(), 'docs/howto.md', 'active_legacy_reference')

    def test_ignored_text_suffixes_scanned(self):
        for suffix in ('.mjs', '.less', '.po', '.bat'):
            with self.subTest(suffix=suffix):
                name = 'frontend/hidden' + suffix
                path = self.put(name, 'backend/sandbox\n')
                self.assert_problem(self.run_check(), name, 'active_legacy_reference')
                path.unlink()

    def test_obsolete_full_runner_command_refused(self):
        for command in ('./scripts/check.sh', 'bash scripts/check_runtime.sh'):
            with self.subTest(command=command):
                self.put('docs/howto.md', command + '\n')
                self.assertFalse(self.run_check()['ok'])

    def test_warning_about_runner_is_allowed(self):
        self.put('docs/howto.md', 'Old scripts/check.sh is not the supported installation path.\n')
        self.assertTrue(self.run_check()['ok'])

    def test_historical_evidence_preserved(self):
        self.put('edw-inventory.json', '{"old": "backend/sandbox"}\n')
        self.put('docs/neural-analysis/provenance.json', '{"old": "requirements/django19"}\n')
        self.put('docs/legacy-cleanup/README.md', 'Removed backend/sandbox\n')
        self.assertTrue(self.run_check()['ok'])

    def test_tracked_hidden_files_are_included(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.put('.gitignore', 'hidden/\n')
        self.put('hidden/code.py', 'import sandbox.sample\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '-f', 'hidden/code.py'], check=True)
        paths = CHECK.git_paths(self.root)
        self.assertIn('hidden/code.py', paths)
        self.assertFalse(CHECK.check_tree(self.root, paths)['ok'])

    def test_symlink_to_removed_path_is_refused(self):
        target = self.root / CHECK.REMOVED[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(self.root / 'missing-target', target_is_directory=True)
        self.assertFalse(self.run_check()['ok'])

    def test_invalid_utf8_active_source_is_refused(self):
        target = self.put('docs/howto.md', 'placeholder')
        target.write_bytes(b'\xff')
        self.assertFalse(self.run_check()['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
