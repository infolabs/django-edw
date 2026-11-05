#!/usr/bin/env python3
"""Static boundary of the supported source tree; no Django/application imports.

Use Git's file list, not .ignore-aware search: ignored-but-tracked source must
not disappear from this check. Historical evidence remains deliberately intact.
This is a narrow regression check, not a general dependency/security scanner.
"""
from pathlib import Path, PurePosixPath
import argparse
import json
import re
import subprocess
import sys

REMOVED = (
    'backend/requirements/django19',
    'backend/sandbox',
    'backend/docs/sample.txt',
)
HISTORICAL_FILES = {
    'edw-inventory.json', 'edw-runtime-report.json', 'edw-safety-report.json',
}
HISTORICAL_DIRS = ('docs/_build/', 'docs/neural-analysis/', 'docs/legacy-cleanup/')
SELF_TESTS = {'scripts/check_clean_source.py', 'scripts/test_clean_source.py'}
TEXT_SUFFIXES = {'.py', '.sh', '.toml', '.txt', '.md', '.rst', '.html', '.js',
                 '.mjs', '.cjs', '.jsx', '.less', '.po', '.bat',
                 '.json', '.yml', '.yaml', '.in', '.cfg', '.ini', '.css'}
TOKENS = ('backend/sandbox', 'requirements/django19', 'manage_todos.py',
          'backend/docs/sample.txt', 'Django==1.9', 'django==1.9')
IMPORT = re.compile(r'^\s*(?:from|import)\s+(?:(?:backend\.)?sandbox|sample|todos)(?:\.|\s|$)')
NAMESPACE = re.compile(r'\b(?:sample|todos)\.(?:settings|urls|models|apps|wsgi)\b')
OLD_RUN = re.compile(r'^\s*(?:(?:bash|sh)\s+)?(?:\./)?scripts/check(?:_runtime)?\.sh(?:\s|$)')
ENTRYPOINTS = ('README.md', 'INSTALL.md', 'backend/docs/install.txt',
               'docs/index.rst', 'frontend/docs/readme.txt')


def git_paths(root):
    result = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        capture_output=True, check=True,
    )
    return sorted(set(p.decode('utf-8') for p in result.stdout.split(b'\0') if p))


def check_tree(root, paths):
    root = Path(root)
    problems = []
    scanned = historical = 0
    for name in REMOVED:
        target = root / name
        if target.exists() or target.is_symlink():
            problems.append({'path': name, 'code': 'removed_path_present'})
    for name in ENTRYPOINTS:
        target = root / name
        if not target.is_file() or target.is_symlink():
            problems.append({'path': name, 'code': 'missing_regular_entrypoint'})
        elif 'INSTALL.md' not in target.read_text(encoding='utf-8') and name != 'INSTALL.md':
            problems.append({'path': name, 'code': 'missing_canonical_install_pointer'})
    for name in sorted(set(paths)):
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts:
            problems.append({'path': name, 'code': 'unsafe_git_path'})
            continue
        if name in HISTORICAL_FILES or name.startswith(HISTORICAL_DIRS):
            historical += 1
            continue
        if name in SELF_TESTS:
            continue  # The narrowly scoped detector and its synthetic fixtures contain the tokens.
        if path.suffix not in TEXT_SUFFIXES and path.name not in {'.ignore', '.gitignore', 'Makefile', 'Dockerfile'}:
            continue
        target = root / name
        if target.is_symlink():
            problems.append({'path': name, 'code': 'active_text_symlink'})
            continue
        if not target.exists():
            continue  # A tracked path may have been intentionally deleted in the worktree.
        if not target.is_file() or target.stat().st_size > 4 * 1024 * 1024:
            problems.append({'path': name, 'code': 'unreadable_or_oversized_active_text'})
            continue
        try:
            text = target.read_text(encoding='utf-8')
        except UnicodeError:
            problems.append({'path': name, 'code': 'invalid_utf8_active_text'})
            continue
        scanned += 1
        for number, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in TOKENS) or IMPORT.search(line) or NAMESPACE.search(line):
                problems.append({'path': name, 'line': number, 'code': 'active_legacy_reference'})
            if path.suffix in {'.md', '.rst', '.txt', '.html'} and OLD_RUN.search(line):
                problems.append({'path': name, 'line': number, 'code': 'obsolete_runner_command'})
    return {'schema': 'edw-clean-source/1', 'ok': not problems,
            'active_text_files_scanned': scanned,
            'historical_paths_skipped': historical,
            'problems': problems}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = check_tree(args.repo, git_paths(args.repo))
    except (OSError, UnicodeError, subprocess.CalledProcessError) as error:
        print(json.dumps({'schema': 'edw-clean-source/1', 'ok': False,
                          'error_type': type(error).__name__}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
