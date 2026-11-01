import hashlib

import pytest

from agents.revision_patches import apply_source_patches, source_context
from revision_jobs import remember_supported_guide, retained_revision_guide


def apply(source, edits, steps=None, digest=None):
    return apply_source_patches(source, edits, steps or [{"id": "one", "target": {"symbol": "value"}}],
        digest or hashlib.sha256(source.encode()).hexdigest())


def test_patches_preserve_untouched_source_and_use_original_offsets():
    source = '#include <iostream>\nint main() { int value = 0; std::cout << value; }\n'
    code, errors = apply(source, [{"step_id": "one", "old": "int value = 0;", "new": "int value = 1;"}])
    assert errors == []
    assert code == source.replace('int value = 0;', 'int value = 1;')


@pytest.mark.parametrize("source,edits,reason", [
    ('int value = 0;', [{"step_id": "one", "old": "missing", "new": "value"}], 'patch_anchor_not_unique'),
    ('value + value', [{"step_id": "one", "old": "value", "new": "x"}], 'patch_anchor_not_unique'),
    ('value = 0;', [{"step_id": "other", "old": "value", "new": "x"}], 'patch_step_not_in_guide'),
    ('value = 0;', [{"step_id": "one", "old": "value", "new": "value"}], 'patch_has_no_change'),
    ('value = 0;', [{"step_id": "one", "old": "value = 0;", "new": "value = 1;"}], 'whole_program_patch_rejected'),
    ('int value = 0; print(value);', [{"step_id": "one", "old": "int value = 0;", "new": "```cpp"}], 'fenced_patch_rejected'),
    ('value = 0; print(value);', [{"step_id": "one", "old": "0", "new": "1"}], 'patch_does_not_touch_target'),
    ('#include <iostream>\nint value = 0;', [{"step_id": "one", "old": "#include <iostream>", "new": "#include <bits/stdc++.h>"}], 'unrequested_header_replacement'),
])
def test_unsafe_or_ambiguous_edits_fail_closed(source, edits, reason):
    code, errors = apply(source, edits)
    assert not code and errors == [reason]


def test_overlapping_and_stale_patches_are_rejected():
    source = 'int value = 0; print(value);'
    edits = [{"step_id": "one", "old": "int value = 0;", "new": "int value = 1;"},
             {"step_id": "one", "old": "value = 0", "new": "value = 2"}]
    assert apply(source, edits)[1] == ['overlapping_source_patches']
    assert apply(source, edits[:1], digest='x' * 64)[1] == ['stale_patch_source']


def test_required_header_addition_is_supported_without_replacing_other_headers():
    source = '#include <vector>\nint main() { int value = 0; }'
    code, errors = apply(source, [{"step_id": "one", "old": "#include <vector>", "new": "#include <vector>\n#include <algorithm>"}])
    assert not errors and code.startswith('#include <vector>\n#include <algorithm>\n')


@pytest.mark.parametrize('original,addition', [
    ('import java.util.Scanner;', 'import java.util.Arrays;'),
    ('import sys', 'from collections import deque'),
])
def test_standard_import_additions_are_separate_from_algorithm_edits(original, addition):
    source = original + '\n// existing value operation\n'
    code, errors = apply(source, [{"step_id": "one", "old": original, "new": original + '\n' + addition}])
    assert not errors and original in code and addition in code


def test_crlf_source_keeps_untouched_bytes():
    source = 'int value = 0;\r\nprint(value);\r\n// untouched\r\n'
    code, errors = apply(source, [{"step_id": "one", "old": "int value = 0;\nprint(value);", "new": "int value = 1;\nprint(value);"}])
    assert not errors and code == source.replace('value = 0', 'value = 1')


@pytest.mark.parametrize('language,source,names', [
    ('cpp', 'int main() { int count = 0; return count; }', {'main', 'count'}),
    ('python', 'def run(items):\n    return items\n', {'run', 'items'}),
    ('java', 'class Main { public static void main(String[] args) { int count = 0; } }', {'Main', 'main', 'args', 'count'}),
])
def test_inventory_contains_existing_ast_names_and_locations(language, source, names):
    context = source_context(source, language)
    assert names <= {item['name'] for item in context['symbols']}
    assert all(item['lines'] for item in context['symbols'])
    assert context['source_hash'] == hashlib.sha256(source.encode()).hexdigest()


def test_later_bad_guide_does_not_erase_supported_previous_guide():
    first = {'guide_validated': True, 'guidance_supported': True, 'steps': [{'id': 'one'}],
             'guided_steps': ['Keep this supported action.'], 'score_projection': {'projected_score': 100}}
    saved = remember_supported_guide(first)
    assert 'score_projection' not in saved
    second = {'guide_validated': False, 'steps': [], 'last_candidate_result': {'errors': ['target_not_in_original_ast']}}
    assert remember_supported_guide(second, saved) == saved
    display = retained_revision_guide(second, saved)
    assert display['guided_steps'] == first['guided_steps']
    assert display['last_candidate_result'] == second['last_candidate_result']
