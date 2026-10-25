# -*- coding: utf-8 -*-
"""
E11/R6 (ported E10.safetycheck + residual controls): the evidence runner is
fail-closed.

These are fast negative tests of the durable gate helpers.  They do not build or
install anything; the gate itself runs the heavy path.  Each control is a real
subprocess invocation, so ``-O``/missing-precondition/write-failure paths are
exercised exactly as an operator would hit them.
"""
from __future__ import unicode_literals

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
JUNIT_SCRIPT = REPO / 'scripts' / 'check_safety_env.py'
GATE_SCRIPT = REPO / 'scripts' / 'check_safety.sh'
INPUTS = REPO / 'scripts' / 'safety-inputs.json'

PASSING_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="ok" errors="0" failures="0" skipped="0" tests="2" time="0.2">
    <testcase classname="runtime_tests.test_a" name="test_one" time="0.1"/>
    <testcase classname="runtime_tests.test_a" name="test_two" time="0.1"/>
  </testsuite>
</testsuites>
'''

ZERO_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="0" time="0.001"></testsuite></testsuites>
'''

MULTI_SUITE_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="clean" errors="0" failures="0" skipped="0" tests="1" time="0.1"><testcase classname="a" name="ok" time="0.1"/></testsuite>
  <testsuite name="broken" errors="0" failures="1" skipped="0" tests="1" time="0.1"><testcase classname="b" name="bad" time="0.1"><failure message="boom">boom</failure></testcase></testsuite>
</testsuites>
'''

MISMATCHED_COUNTER_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="3" time="0.1"><testcase classname="a" name="one" time="0.1"/></testsuite></testsuites>
'''

NEGATIVE_COUNTER_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="-1" failures="0" skipped="0" tests="1" time="0.1"><testcase classname="a" name="one" time="0.1"/></testsuite></testsuites>
'''

DUPLICATE_XML = '''<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="2" time="0.1">
  <testcase classname="a" name="one" time="0.1"/>
  <testcase classname="a" name="one" time="0.1"/>
</testsuite></testsuites>
'''


def _run_junit(workdir, name, payload, extra=()):
    xml = pathlib.Path(workdir) / '{}.xml'.format(name)
    xml.write_text(payload, encoding='utf-8')
    json_path = pathlib.Path(workdir) / '{}.json'.format(name)
    command = [sys.executable, str(JUNIT_SCRIPT), 'junit', '--file', str(xml),
               '--json', str(json_path)]
    command += list(extra)
    result = subprocess.run(command, capture_output=True, text=True)
    counts = json_path.read_text(encoding='utf-8') if json_path.exists() else ''
    return result, counts


def test_zero_test_junit_is_not_a_pass(tmp_path):
    result, counts = _run_junit(tmp_path, 'zero', ZERO_XML)
    assert result.returncode != 0, (
        'a zero-test JUnit report passed the gate (rc=0, counts={})'.format(counts))


def test_multi_suite_junit_with_failing_suite_is_not_a_pass(tmp_path):
    result, counts = _run_junit(tmp_path, 'multi_suite', MULTI_SUITE_XML)
    assert result.returncode != 0, (
        'a multi-suite JUnit with a failing later suite passed the gate '
        '(rc=0, counts={})'.format(counts))


def test_multi_suite_junit_without_failures_is_read_completely(tmp_path):
    xml = PASSING_XML.replace(
        '</testsuites>',
        '  <testsuite name="second" errors="0" failures="0" skipped="0" tests="1" '
        'time="0.1"><testcase classname="runtime_tests.test_b" name="test_three" '
        'time="0.1"/></testsuite>\n</testsuites>',
    )
    result, counts = _run_junit(tmp_path, 'passing', xml)
    assert result.returncode == 0, counts
    report = json.loads(counts)
    assert report['tests'] == 3 and report['suites'] == 2, report


def test_declared_counter_mismatch_is_refused(tmp_path):
    result, counts = _run_junit(tmp_path, 'mismatched', MISMATCHED_COUNTER_XML)
    assert result.returncode != 0, counts
    assert 'declares 3 tests' in str(json.loads(counts)['problems'])


def test_negative_counter_is_refused(tmp_path):
    result, counts = _run_junit(tmp_path, 'negative', NEGATIVE_COUNTER_XML)
    assert result.returncode != 0, counts


def test_malformed_junit_is_refused(tmp_path):
    result, counts = _run_junit(tmp_path, 'broken', '<testsuites><testsuite')
    assert result.returncode != 0, counts


def test_stale_or_missing_junit_is_refused(tmp_path):
    missing = pathlib.Path(tmp_path) / 'missing.xml'
    result = subprocess.run(
        [sys.executable, str(JUNIT_SCRIPT), 'junit', '--file', str(missing),
         '--json', str(pathlib.Path(tmp_path) / 'missing.json')],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'a missing (stale) JUnit report was accepted'


def test_duplicate_testcase_ids_are_refused(tmp_path):
    result, counts = _run_junit(tmp_path, 'duplicate', DUPLICATE_XML)
    assert result.returncode != 0, counts
    assert 'duplicate' in str(json.loads(counts)['problems'])


def test_inventory_requires_every_reviewed_case(tmp_path):
    inventory = pathlib.Path(tmp_path) / 'inventory.json'
    inventory.write_text(json.dumps({
        'schema': 'edw-modernize/safety-test-inventory/1',
        'suites': {
            'sample': {
                'settings': 'sample_settings',
                'cases': [
                    'runtime_tests.test_a::test_one',
                    'runtime_tests.test_a::test_two',
                    'runtime_tests.test_a::test_missing',
                ],
            },
        },
    }), encoding='utf-8')
    result, counts = _run_junit(
        tmp_path, 'inventory', PASSING_XML,
        extra=('--suite', 'sample', '--inventory', str(inventory)),
    )
    assert result.returncode != 0, counts
    report = json.loads(counts)
    assert report['inventory']['missing'] == ['runtime_tests.test_a::test_missing']


def test_inventory_rejects_unreviewed_cases(tmp_path):
    inventory = pathlib.Path(tmp_path) / 'inventory.json'
    inventory.write_text(json.dumps({
        'schema': 'edw-modernize/safety-test-inventory/1',
        'suites': {'sample': {'settings': 's', 'cases': ['runtime_tests.test_a::test_one']}},
    }), encoding='utf-8')
    result, counts = _run_junit(
        tmp_path, 'inventory2', PASSING_XML,
        extra=('--suite', 'sample', '--inventory', str(inventory)),
    )
    assert result.returncode != 0, counts
    assert json.loads(counts)['inventory']['unknown'] == ['runtime_tests.test_a::test_two']


def test_gate_does_not_delete_an_arbitrary_workdir(tmp_path):
    victim = pathlib.Path(tmp_path) / 'cleanup-victim'
    victim.mkdir(parents=True)
    sentinel = victim / 'sentinel.txt'
    sentinel.write_text('evidence\n', encoding='utf-8')
    env = dict(os.environ)
    env['EDW_SAFETY_PYTHON'] = '/nonexistent/e10-python'
    env['EDW_SAFETY_WORK'] = str(victim)
    result = subprocess.run(
        ['bash', str(GATE_SCRIPT)], cwd=str(REPO), env=env,
        capture_output=True, text=True,
    )
    tail = (result.stderr or result.stdout or '')[-400:]
    assert result.returncode != 0, 'the gate accepted a missing interpreter'
    assert sentinel.exists(), (
        'the gate destroyed the arbitrary caller-supplied work directory '
        '(exit {}, log tail: {})'.format(result.returncode, tail))
    assert sorted(path.name for path in victim.iterdir()) == ['sentinel.txt'], (
        'the gate wrote into a caller-supplied directory before its preconditions')


def test_gate_refuses_a_foreign_head_without_deleting_evidence(tmp_path):
    victim = pathlib.Path(tmp_path) / 'evidence-keeper'
    victim.mkdir(parents=True)
    sentinel = victim / 'sentinel.txt'
    sentinel.write_text('evidence\n', encoding='utf-8')
    wheelhouse = pathlib.Path(tmp_path) / 'wheelhouse'
    wheelhouse.mkdir()
    env = dict(os.environ)
    env['EDW_SAFETY_PYTHON'] = sys.executable
    env['EDW_SAFETY_WORK'] = str(victim)
    env['EDW_SAFETY_EXPECTED_HEAD'] = '0' * 40
    env['EDW_SAFETY_WHEELHOUSE'] = str(wheelhouse)
    result = subprocess.run(
        ['bash', str(GATE_SCRIPT)], cwd=str(REPO), env=env,
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'the gate accepted a foreign HEAD'
    assert sentinel.exists(), 'the gate removed the caller-supplied evidence directory'


def test_optimized_interpreter_is_refused_before_output(tmp_path):
    target = pathlib.Path(tmp_path) / 'optimized.json'
    result = subprocess.run(
        [sys.executable, '-O', str(JUNIT_SCRIPT), 'probe', '--dest',
         str(tmp_path / 'probe.txt'), '--json', str(target)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'an optimized interpreter was accepted'
    assert not target.exists(), 'an optimized interpreter wrote trust evidence'
    assert not (pathlib.Path(tmp_path) / 'probe.txt').exists()


def test_evidence_write_failure_is_not_a_pass(tmp_path):
    xml = pathlib.Path(tmp_path) / 'passing.xml'
    xml.write_text(PASSING_XML, encoding='utf-8')
    result = subprocess.run(
        [sys.executable, str(JUNIT_SCRIPT), 'junit', '--file', str(xml),
         '--json', '/dev/full'],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, (
        'a failed evidence write was reported as a pass (exit {})'.format(
            result.returncode))


def test_snapshot_requires_the_exact_commit(tmp_path):
    result = subprocess.run(
        [sys.executable, str(JUNIT_SCRIPT), 'snapshot',
         '--repo', str(REPO), '--expected-head', '0' * 40,
         '--inputs', str(INPUTS), '--dest', str(tmp_path / 'src'),
         '--json', str(tmp_path / 'snapshot.json')],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'a foreign commit snapshot was accepted'


def test_preconditions_require_a_prepared_wheelhouse(tmp_path):
    inventory = REPO / 'scripts' / 'safety-test-inventory.json'
    if not inventory.is_file():
        pytest.skip('the reviewed inventory is not present yet')
    result = subprocess.run(
        [sys.executable, str(JUNIT_SCRIPT), 'preconditions',
         '--repo', str(REPO), '--expected-head', _head(),
         '--wheelhouse', str(tmp_path / 'no-wheelhouse'),
         '--inputs', str(INPUTS), '--inventory', str(inventory),
         '--json', str(tmp_path / 'pre.json')],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'a missing prepared wheelhouse was accepted'


def test_preconditions_refuse_a_foreign_head(tmp_path):
    inventory = REPO / 'scripts' / 'safety-test-inventory.json'
    result = subprocess.run(
        [sys.executable, str(JUNIT_SCRIPT), 'preconditions',
         '--repo', str(REPO), '--expected-head', '0' * 40,
         '--wheelhouse', str(tmp_path),
         '--inputs', str(INPUTS), '--inventory', str(inventory),
         '--json', str(tmp_path / 'pre.json')],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, 'a foreign HEAD was accepted'


def test_production_gate_script_has_no_destructive_caller_cleanup():
    source = GATE_SCRIPT.read_text(encoding='utf-8')
    assert 'rm -rf "${WORK}"' not in source
    assert 'rm -rf "${RUN_BASE}"' not in source
    assert 'rm -rf "${RUN}/tmp"' in source


def _head():
    return subprocess.run(
        ['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
