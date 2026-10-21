#!/usr/bin/env bash
#
# E1: характеризационная проверка контрактов django-edw.
#
# Запускает синтетический контур (backend/edw/tests/contract) и штатный
# backend/edw/tests/test_term.py на предсобранном offline-окружении.
# pip/npm install не вызываются, внешние БД и сеть не используются:
# только sqlite в памяти и локальный locmem-кэш.
#
set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="/home/agent/workspace/venvs/edw-modernize/bin/python"
BACKEND="${REPO_ROOT}/backend"

if [[ ! -x "${PYTHON}" ]]; then
    echo "CHECK FAIL: не найден offline-python ${PYTHON}" >&2
    exit 2
fi

export PYTHONPATH="${BACKEND}${PYTHONPATH:+:${PYTHONPATH}}"
export DJANGO_SETTINGS_MODULE="edw_contract_settings"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::SyntaxWarning,ignore::RuntimeWarning,ignore::ImportWarning"

cd "${REPO_ROOT}"

echo "== EDW contracts check =="
"${PYTHON}" -c "import django, rest_framework, pytest; print('python: {}'.format(__import__('sys').version.split()[0])); print('django: {}'.format(django.get_version())); print('drf: {}'.format(rest_framework.VERSION)); print('pytest: {}'.format(pytest.__version__))"

set +o errexit
"${PYTHON}" -m pytest \
    --tb=short \
    -q \
    -p no:cacheprovider \
    backend/edw/tests/contract \
    backend/edw/tests/test_term.py
STATUS=$?
set -o errexit

if [[ ${STATUS} -eq 0 ]]; then
    echo "CHECK PASS"
else
    echo "CHECK FAIL (pytest exit ${STATUS})" >&2
fi

exit ${STATUS}
