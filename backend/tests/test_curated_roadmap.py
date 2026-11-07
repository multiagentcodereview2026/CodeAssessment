from collections import Counter
from types import SimpleNamespace

from curated_roadmap import CURRICULUM, build_roadmap


def catalogue():
    return [SimpleNamespace(id=p['id'], title=p['id'], difficulty=p['difficulty'],
                            category='Unrelated tag', topic_tags=[], is_public_practice=True)
            for step in CURRICULUM['steps'] for p in step['problems']]


def attempts(ids, score=95):
    return [SimpleNamespace(problem_id=pid, overall_score=score) for pid in ids]


def step(result, pid='arrays'):
    return next(s for s in result['steps'] if s['id'] == pid)


def test_curriculum_matches_all_attached_totals_and_is_topological():
    assert len(CURRICULUM['steps']) == 32
    assert len(catalogue()) == len({p.id for p in catalogue()}) == 446
    assert Counter(p.difficulty for p in catalogue()) == {'Easy': 116, 'Medium': 242, 'Hard': 88}
    assert Counter(s['level'] for s in CURRICULUM['steps']) == {'Beginner': 11, 'Intermediate': 9, 'Advanced': 12}
    visited = set()
    for item in CURRICULUM['steps']:
        assert set(item['prerequisites']) <= visited
        visited.add(item['id'])


def test_next_problem_follows_attachment_order_not_lexical_id_or_tags():
    result = build_roadmap(catalogue(), [])
    assert result['next_problem']['id'] == 'leetcode-66'
    result = build_roadmap(catalogue(), attempts(['leetcode-66'], 100))
    assert result['next_problem']['id'] == 'leetcode-121'
    assert result['next_problem']['difficulty'] == 'Easy'


def test_unlisted_same_tag_and_instructor_problems_do_not_count():
    problems = catalogue() + [SimpleNamespace(id='leetcode-999999', title='extra', difficulty='Easy',
                                             category='Array', topic_tags=['Array'])]
    result = build_roadmap(problems, attempts(['leetcode-999999', 'instructor-leetcode-66'], 100))
    assert result['total_completed_problems'] == 0
    assert step(result)['completed_problems'] == 0


def test_best_score_only_counts_once_and_never_regresses():
    result = build_roadmap(catalogue(), attempts(['leetcode-66'], 20) + attempts(['leetcode-66'], 99) + attempts(['leetcode-66'], 30))
    assert step(result)['completed_problems'] == 1
    assert step(result)['average_score'] == 99


def test_catalogue_gap_retains_exact_problem_and_does_not_substitute():
    result = build_roadmap([p for p in catalogue() if p.id != 'leetcode-66'], [])
    assert result['next_problem'] is None
    assert result['next_requirement']['problem_id'] == 'leetcode-66'
    assert step(result)['missing_problem_ids'] == ['leetcode-66']
    assert step(result)['core_required_problems'] == 22


def test_sorting_is_required_before_two_pointers_can_unlock():
    arrays = next(s for s in CURRICULUM['steps'] if s['id'] == 'arrays')['problems']
    sorting = next(s for s in CURRICULUM['steps'] if s['id'] == 'sorting')['problems']
    completed = attempts([p['id'] for p in arrays])
    result = build_roadmap(catalogue(), completed)
    assert step(result, 'sorting')['unlocked']
    assert not step(result, 'two-pointers')['unlocked']
    result = build_roadmap(catalogue(), completed + attempts([p['id'] for p in sorting]))
    assert step(result, 'two-pointers')['unlocked']


def test_low_average_revisits_weakest_core_problem_without_adding_new_ids():
    arrays = next(s for s in CURRICULUM['steps'] if s['id'] == 'arrays')['problems']
    result = build_roadmap(catalogue(), attempts([p['id'] for p in arrays], 80))
    assert not step(result)['core_complete']
    assert result['next_problem']['id'] == 'leetcode-66'
    assert '90%' in result['next_problem']['reason']


def test_all_core_complete_keeps_mastery_review_then_finishes_at_97():
    result = build_roadmap(catalogue(), attempts([p.id for p in catalogue()], 95))
    assert result['core_path_complete']
    assert not result['mastery_complete']
    assert '97%' in result['next_problem']['reason']
    assert [s['required_problems'] for s in result['level_summaries']] == [181, 143, 122]
    result = build_roadmap(catalogue(), attempts([p.id for p in catalogue()], 97))
    assert result['mastery_complete']
    assert result['next_problem'] is None
    assert result['next_requirement'] is None
    assert all(s['status'] == 'MASTERED' for s in result['steps'])


def test_nonfinite_scores_and_private_problems_cannot_complete_a_topic():
    problems = catalogue()
    next(p for p in problems if p.id == 'leetcode-66').is_public_practice = False
    result = build_roadmap(problems, attempts(['leetcode-66']) + attempts(['leetcode-121'], float('nan')))
    assert result['total_completed_problems'] == 0
    assert not step(result)['core_complete']
