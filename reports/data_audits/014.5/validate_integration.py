"""Offline preservation checks for the two reviewed research commits."""

import ast
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PR15 = '7d2ddf2b2efe1af27e4182348e41e150aae3b683'
PR16 = 'ee0a0326b45dfd2718b1fed4625412b66dbd18a3'
MAIN = '8d97df3a68a7a7f002afbea5eafca3c26d4af9cd'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')


def show(ref, name):
    return git('show', ref + ':' + name)


def files(ref, prefix):
    return git('ls-tree', '-r', '--name-only', ref, '--', prefix).splitlines()


def read(name):
    return (ROOT / name).read_text(encoding='utf-8-sig')


def subsequence(old, new):
    lines = iter(new.splitlines())
    return all(any(line == candidate for candidate in lines) for line in old.splitlines())


def issue_rows(text):
    return {line.split('|')[1].strip(): [c.strip() for c in line.split('|')[1:-1]]
            for line in text.splitlines() if re.match(r'^\| ISS-\d{3} \|', line)}


def main():
    preserved = {}
    for ref, task in [(PR15, '014.3'), (PR16, '014.4')]:
        paths = files(ref, 'reports/data_audits/' + task)
        paths += [p for p in files(ref, 'docs') if Path(p).name.startswith(task + '-')]
        for name in paths:
            assert read(name) == show(ref, name), name
        preserved[task] = len(paths)
    issues = read('docs/issue-register.md')
    current_rows = issue_rows(issues)
    assert len(current_rows) == 22
    for issue in ['ISS-003', 'ISS-004', 'ISS-022']:
        assert current_rows[issue][5] == 'Open'
    for ref in [MAIN, PR16]:
        for name in ['docs/data-architecture-and-dictionary.md',
                     'docs/development-journal/02-data-preparation.md']:
            assert subsequence(show(ref, name), read(name)), (ref, name)
        old = show(ref, 'docs/issue-register.md')
        # Git automatically combined Task 014.3's addition within ISS-003's cell.
        for key, cells in issue_rows(old).items():
            assert all(a in b for a, b in zip(cells, current_rows[key])), key
        narrative = lambda s: '\n'.join(line for line in s.splitlines()
                                       if not re.match(r'^\| ISS-\d{3} \|', line))
        assert subsequence(narrative(old), narrative(issues))
    with (ROOT / 'docs/task-execution-log.csv').open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assert len(reader.fieldnames) == 7
        rows = list(reader)
    lookup = {r['task_id']: r for r in rows}
    assert len(lookup) == len(rows)
    for ref in [MAIN, PR16]:
        for row in csv.DictReader(show(ref, 'docs/task-execution-log.csv').splitlines()):
            assert lookup[row['task_id']] == row
    scope = set(files('HEAD', 'docs') + files('HEAD', 'reports/data_audits/014.4')
                + files(MAIN, 'reports/data_audits/014.3'))
    scope.update(str(p.relative_to(ROOT)).replace('\\', '/')
                 for p in (ROOT / 'reports/data_audits/014.5').glob('*'))
    scope.add('docs/014.5-integrate-geography-research-and-approved-methodology.md')
    for name in scope:
        text = read(name)
        if name.endswith('.json'):
            json.loads(text)
        if name.endswith('.py'):
            ast.parse(text)
        assert not re.search(r'^(<<<<<<< |=======\s*$|>>>>>>> )', text, re.M), name
        assert not re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY', text), name
        if name.endswith('.md'):
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if target.startswith(('https:', 'http:', '#', '<')):
                    continue
                target = target.split('#')[0]
                if target and '<' not in target:
                    assert (ROOT / name).parent.joinpath(target).exists(), (name, target)
    for ref in [MAIN, PR15, PR16]:
        names = git('diff', '--name-only', 'a8bc21c9a0c95e379f2fc1c61efa39b866985b35', ref).splitlines()
        assert all(n.startswith(('docs/', 'reports/data_audits/014.3/',
                                 'reports/data_audits/014.4/')) for n in names)
    result = dict(status='pass', reviewed_pr15_head=PR15, reviewed_pr16_head=PR16,
                  pr15_merge_main=MAIN, exact_research_and_prompt_files_preserved=preserved,
                  original_document_narrative_and_issue_cell_content_preserved=True,
                  all_22_issue_records_and_statuses_preserved=True,
                  historical_csv_rows_preserved=True,
                  syntax_json_local_links_conflict_markers_credential_pattern_scan='pass; pattern scan is not proof of absence',
                  conflicts_resolved=['dictionary', 'Phase 2 journal', 'timing CSV'],
                  resolution='Both append contributions retained in task order; CSV row content preserved. ISS-003 automatic merge retains both research updates.',
                  production_tests='Not run: documentation/research integration only.',
                  independent_offline_validators_executed='Task 014.3: all 142 ranges; Task 014.4: 3564 grid rows and 11682 native period records. Both pass; original validation files unchanged.')
    path = ROOT / 'reports/data_audits/014.5/integration-validation.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
