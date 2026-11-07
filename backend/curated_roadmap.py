"""Deterministic progress through the user-curated 446-problem DSA path."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

CURRICULUM = json.loads(Path(__file__).with_name('roadmap_curriculum.json').read_text(encoding='utf-8'))
CORE_AVERAGE = 90.0
MASTERY_AVERAGE = 97.0
ROADMAP_STEPS = tuple(
    (s['id'], s['title'], tuple(s['aliases']), tuple(s['prerequisites']), s['level'],
     len(s['problems']), len(s['problems']), len(s['problems']))
    for s in CURRICULUM['steps']
)


def build_roadmap(problems: Iterable[Any], submissions: Iterable[Any]) -> dict[str, Any]:
    catalogue = {
        p.id: p for p in problems
        if str(p.id).startswith('leetcode-') and getattr(p, 'is_public_practice', True)
    }
    planned_ids = {p['id'] for s in CURRICULUM['steps'] for p in s['problems']}
    best: dict[str, float] = {}
    for submission in submissions:
        pid = getattr(submission, 'problem_id', None)
        score = getattr(submission, 'overall_score', None)
        if pid not in planned_ids or pid not in catalogue or score is None:
            continue
        value = float(score)
        if math.isfinite(value) and 0 <= value <= 100:
            best[pid] = max(best.get(pid, -1), value)

    steps = []
    for configured in CURRICULUM['steps']:
        entries = []
        for position, planned in enumerate(configured['problems'], 1):
            problem = catalogue.get(planned['id'])
            entries.append({
                'id': planned['id'], 'title': problem.title if problem else f"Problem #{planned['id'].split('-')[-1]}",
                'difficulty': planned['difficulty'], 'position': position,
                'catalogue_difficulty': problem.difficulty if problem else None,
                'category': getattr(problem, 'category', configured['title']),
                'available': problem is not None, 'best_score': best.get(planned['id']),
                'completed': planned['id'] in best,
            })
        scores = [p['best_score'] for p in entries if p['completed']]
        exact_average = sum(scores) / len(scores) if scores else None
        requirements = {d: sum(p['difficulty'] == d for p in entries) for d in ('Easy', 'Medium', 'Hard')}
        completed = {d: sum(p['difficulty'] == d and p['completed'] for p in entries) for d in requirements}
        missing = [p['id'] for p in entries if not p['available']]
        mismatches = [p['id'] for p in entries if p['available'] and p['difficulty'] != p['catalogue_difficulty']]
        all_done = len(scores) == len(entries) and not missing and not mismatches
        steps.append({
            'id': configured['id'], 'title': configured['title'], 'level': configured['level'],
            'prerequisites': list(configured['prerequisites']),
            'foundation_prerequisites': configured['foundation_prerequisites'],
            'problems': entries, 'catalogue_problems': len(entries) - len(missing),
            'completed_problems': len(scores), 'average_score': round(exact_average, 1) if scores else None,
            'core_required_problems': len(entries), 'core_required_average': CORE_AVERAGE,
            'completed_by_difficulty': completed, 'core_difficulty_requirements': requirements,
            'core_complete': bool(all_done and exact_average >= CORE_AVERAGE),
            'mastered': bool(all_done and exact_average >= MASTERY_AVERAGE),
            'mastery_min_problems': len(entries), 'mastery_max_problems': len(entries),
            'mastery_required_average': MASTERY_AVERAGE, 'mastery_difficulty_requirements': requirements,
            'missing_problem_ids': missing, 'difficulty_mismatches': mismatches,
        })

    by_id = {s['id']: s for s in steps}
    current = None
    for step in steps:
        step['unlocked'] = all(by_id[pid]['core_complete'] for pid in step['prerequisites'])
        if current is None and step['unlocked'] and not step['core_complete']:
            current = step
    core_path_complete = all(s['core_complete'] for s in steps)
    mastery_review = core_path_complete and not all(s['mastered'] for s in steps)
    if current is None and mastery_review:
        current = next(s for s in steps if not s['mastered'])

    next_problem = None
    next_requirement = None
    if current:
        pending = [p for p in current['problems'] if not p['completed']]
        if pending:
            selected = pending[0]  # Exact curated order; never substitute another ID.
        else:
            selected = min(current['problems'], key=lambda p: (p['best_score'], p['position']))
        if selected['available']:
            next_problem = {
                'id': selected['id'], 'title': selected['title'], 'difficulty': selected['difficulty'],
                'category': selected['category'], 'topic': current['title'],
                'reason': (
                    f"Revisit your lowest best score in {current['title']} to reach the "
                    f"{MASTERY_AVERAGE if mastery_review else CORE_AVERAGE:g}% average."
                    if not pending else
                    f"Problem {selected['position']} of {current['core_required_problems']} in the curated {current['title']} path."
                ),
            }
        else:
            next_requirement = {'topic': current['title'], 'difficulty': selected['difficulty'],
                                'problem_id': selected['id'], 'reason': 'This exact curated problem is missing from the public bank.'}
    for step in steps:
        step['prerequisite_titles'] = [by_id[pid]['title'] for pid in step['prerequisites']]
        step['status'] = ('LOCKED' if not step['unlocked'] else 'MASTERED' if step['mastered'] else
                          'CORE_COMPLETE' if step['core_complete'] else
                          'CURRENT' if current and step['id'] == current['id'] else 'AVAILABLE')

    levels = []
    milestones = [{'name': 'Starter', 'target': 30, 'completed': len(best) >= 30}]
    cumulative = 0
    for level in ('Beginner', 'Intermediate', 'Advanced'):
        selected_steps = [s for s in steps if s['level'] == level]
        required = sum(s['core_required_problems'] for s in selected_steps)
        cumulative += required
        preceding_levels = ('Beginner', 'Intermediate', 'Advanced')[:('Beginner', 'Intermediate', 'Advanced').index(level) + 1]
        complete = all(s['core_complete'] for s in steps if s['level'] in preceding_levels)
        levels.append({'level': level, 'topics': len(selected_steps), 'required_problems': required,
                       'completed_problems': sum(s['completed_problems'] for s in selected_steps),
                       'complete': complete})
        milestones.append({'name': level + ' complete', 'target': cumulative, 'completed': complete})
    milestones.append({'name': 'Mastery', 'target': len(planned_ids), 'completed': all(s['mastered'] for s in steps)})
    return {
        'curriculum_version': CURRICULUM['version'], 'steps': steps,
        'foundations': CURRICULUM['foundations'], 'level_summaries': levels,
        'current_step_id': current['id'] if current else None,
        'next_problem': next_problem, 'next_requirement': next_requirement,
        'total_completed_problems': len(best), 'total_curated_problems': len(planned_ids),
        'total_curated_topics': len(steps), 'core_path_complete': core_path_complete,
        'mastery_complete': all(s['mastered'] for s in steps), 'overall_milestones': milestones,
    }
