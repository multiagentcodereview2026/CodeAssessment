import asyncio

import pytest
from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from auth import get_current_user, hash_password, require_instructor
from database import Base
from main import (
    get_authenticated_user,
    get_owned_assignment,
    get_owned_course,
    get_problem,
    get_instructor_overview,
    get_instructor_roster,
    get_submission,
    list_submissions,
    get_course_analytics,
    list_instructor_similarity_cases,
    update_instructor_similarity_case,
    get_available_student_courses,
    request_course_enrollment,
    get_instructor_course_requests,
    decide_course_request,
    leave_student_course,
    get_notifications,
    mark_all_notifications_read,
    build_assignment_stats,
    build_course_stats,
    average_score,
    latest_assessed_attempts,
    get_student_analytics,
    get_student_assignment_for_problem,
    get_student_course_assignments,
    get_student_courses,
    create_assignment,
    create_instructor_problem,
    list_instructor_problems,
    enroll_student,
    login,
    logout,
    register,
    submit_and_evaluate_code,
    update_assignment,
)
from schemas import AssignmentCreate, AssignmentUpdate, CourseCreate, CourseUpdate, EnrollmentCreate, InstructorProblemCreate, CourseRequestCreate, LoginRequest, RegisterRequest, SubmissionRequest
import main as main_module


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def add_account(db_session, *, username, role, password, email=None, active=True):
    user = models.User(
        username=username,
        email=email or f"{username}@example.test",
        full_name=username,
        hashed_password=hash_password(password),
        role=role,
        is_active=active,
    )
    db_session.add(user)
    db_session.flush()
    if role == "student":
        db_session.add(models.Student(
            student_id=username,
            name=username,
            email=user.email,
            user_id=user.id,
        ))
    else:
        db_session.add(models.Instructor(user_id=user.id))
    db_session.commit()
    return user


def test_student_login_returns_real_token_and_does_not_create_identity(db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-key-that-is-long-enough-123456")
    password = "valid-student-password"
    user = add_account(db_session, username="student-1", role="student", password=password)

    response = login(LoginRequest(user_id="student-1", role="student", password=password), db_session)

    assert response.id == "student-1"
    assert response.access_token
    assert response.token_type == "bearer"
    assert db_session.query(models.User).count() == 1
    assert db_session.query(models.Student).count() == 1
    authenticated = get_current_user(response.access_token, db_session)
    assert authenticated.id == user.id


def test_invalid_password_unknown_and_disabled_accounts_are_rejected(db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-key-that-is-long-enough-123456")
    add_account(db_session, username="student-1", role="student", password="valid-student-password")

    with pytest.raises(HTTPException) as bad_password:
        login(LoginRequest(user_id="student-1", role="student", password="wrong-password"), db_session)
    assert bad_password.value.status_code == 401

    with pytest.raises(HTTPException) as unknown_user:
        login(LoginRequest(user_id="unknown", role="student", password="wrong-password"), db_session)
    assert unknown_user.value.status_code == 401

    disabled = add_account(
        db_session,
        username="disabled",
        role="student",
        password="valid-student-password",
        active=False,
    )
    with pytest.raises(HTTPException) as disabled_user:
        login(LoginRequest(user_id=disabled.username, role="student", password="valid-student-password"), db_session)
    assert disabled_user.value.status_code == 401


def test_registration_links_existing_student_and_rejects_duplicate(db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-key-that-is-long-enough-123456")
    existing = models.Student(student_id="legacy-student", name="Legacy Student", email="legacy@example.test")
    db_session.add(existing)
    db_session.commit()

    response = register(RegisterRequest(
        username="legacy-student",
        email="legacy@example.test",
        password="a-new-valid-password",
    ), db_session)

    assert response.id == "legacy-student"
    assert response.access_token
    assert db_session.query(models.Student).filter_by(student_id="legacy-student").count() == 1
    assert db_session.query(models.User).filter_by(username="legacy-student").count() == 1

    with pytest.raises(HTTPException) as duplicate:
        register(RegisterRequest(
            username="legacy-student",
            email="legacy@example.test",
            password="another-valid-password",
        ), db_session)
    assert duplicate.value.status_code == 409


def test_instructor_role_check_and_logout_revoke_token(db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-key-that-is-long-enough-123456")
    instructor = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )

    with pytest.raises(HTTPException) as forbidden:
        require_instructor(student)
    assert forbidden.value.status_code == 403

    response = login(LoginRequest(
        user_id="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    ), db_session)
    assert get_authenticated_user(instructor).id == "instructor-1"
    logout(instructor, db_session)

    with pytest.raises(HTTPException) as revoked:
        get_current_user(response.access_token, db_session)
    assert revoked.value.status_code == 401


def test_invalid_legacy_hash_is_rejected_without_exception(db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "phase-two-test-key-that-is-long-enough-123456")
    user = models.User(
        username="legacy",
        email="legacy@example.test",
        full_name="Legacy",
        hashed_password="hashed_password",
        role="instructor",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(models.Instructor(user_id=user.id))
    db_session.commit()

    with pytest.raises(HTTPException) as rejected:
        login(LoginRequest(user_id="legacy", role="instructor", password="wrong"), db_session)
    assert rejected.value.status_code == 401


def test_instructor_resource_helpers_isolate_course_and_assignment_ownership(db_session):
    instructor_a_user = add_account(
        db_session,
        username="instructor-a",
        role="instructor",
        password="instructor-a-password",
    )
    instructor_b_user = add_account(
        db_session,
        username="instructor-b",
        role="instructor",
        password="instructor-b-password",
    )
    instructor_a = instructor_a_user.instructor_profile
    instructor_b = instructor_b_user.instructor_profile
    course_a = models.Course(course_code="A-101", title="Course A", instructor_id=instructor_a.id)
    course_b = models.Course(course_code="B-101", title="Course B", instructor_id=instructor_b.id)
    db_session.add_all([course_a, course_b])
    db_session.flush()
    assignment_a = models.Assignment(title="Assignment A", course_id=course_a.id)
    assignment_b = models.Assignment(title="Assignment B", course_id=course_b.id)
    db_session.add_all([assignment_a, assignment_b])
    db_session.commit()

    assert get_owned_course(db_session, instructor_a.id, course_a.id).id == course_a.id
    assert get_owned_assignment(db_session, instructor_a.id, assignment_a.id).id == assignment_a.id
    with pytest.raises(HTTPException) as other_course:
        get_owned_course(db_session, instructor_a.id, course_b.id)
    assert other_course.value.status_code == 404
    with pytest.raises(HTTPException) as other_assignment:
        get_owned_assignment(db_session, instructor_a.id, assignment_b.id)
    assert other_assignment.value.status_code == 404


def test_course_enrollment_scopes_student_course_and_assignment_views(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student_user = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )
    student = student_user.student_profile
    course = models.Course(
        course_code="CSE-101",
        title="Intro to Code",
        instructor_id=instructor_user.instructor_profile.id,
    )
    problem = models.Problem(
        id="sum-problem",
        title="Sum",
        description="Add two numbers.",
        examples=[],
        constraints=[],
        starter_codes={},
        test_cases=[],
    )
    db_session.add_all([course, problem])
    db_session.flush()
    assignment = models.Assignment(
        title="Week 1",
        course_id=course.id,
        status="ACTIVE",
    )
    db_session.add(assignment)
    db_session.flush()
    db_session.add_all([
        models.AssignmentProblem(assignment_id=assignment.id, problem_id=problem.id, position=1),
        models.Enrollment(student_id=student.student_id, course_id=course.id),
    ])
    db_session.commit()

    courses = get_student_courses(db_session, student)
    assignments = get_student_course_assignments(course.id, db_session, student)
    assert [item.id for item in courses] == [course.id]
    assert courses[0].assignments_count == 1
    assert [item.id for item in assignments] == [assignment.id]
    assert assignments[0].problems == [problem.id]
    assert assignments[0].problem_titles == [problem.title]

    enrollment = db_session.query(models.Enrollment).filter_by(course_id=course.id).one()
    enrollment.is_active = False
    db_session.commit()
    assert get_student_courses(db_session, student) == []
    with pytest.raises(HTTPException) as no_access:
        get_student_course_assignments(course.id, db_session, student)
    assert no_access.value.status_code == 404


def test_enrolling_a_registered_student_makes_the_course_visible_in_my_courses(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student_user = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )
    course = models.Course(
        course_code="CSE-201",
        title="Algorithms",
        instructor_id=instructor_user.instructor_profile.id,
    )
    db_session.add(course)
    db_session.commit()

    enrollment = enroll_student(
        EnrollmentCreate(course_id=course.id, student_id="student-1"),
        db_session,
        instructor_user.instructor_profile,
    )
    visible_courses = get_student_courses(db_session, student_user.student_profile)

    assert enrollment.student_id == "student-1"
    assert [item.id for item in visible_courses] == [course.id]


def test_unlinked_student_profile_cannot_be_enrolled(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    db_session.add(models.Student(student_id="profile-only", name="Profile Only"))
    course = models.Course(
        course_code="CSE-202",
        title="Data Structures",
        instructor_id=instructor_user.instructor_profile.id,
    )
    db_session.add(course)
    db_session.commit()

    with pytest.raises(HTTPException) as rejected:
        enroll_student(
            EnrollmentCreate(course_id=course.id, student_id="profile-only"),
            db_session,
            instructor_user.instructor_profile,
        )

    assert rejected.value.status_code == 422


def test_assignment_schema_rejects_empty_titles_empty_problems_and_duplicate_ids():
    assert AssignmentCreate(title="Task", course_id=1, problem_ids=["problem-1"]).title == "Task"
    invalid_payloads = [
        {"title": " ", "course_id": 1, "problem_ids": ["problem-1"]},
        {"title": "Task", "course_id": 1, "problem_ids": []},
        {"title": "Task", "course_id": 1, "problem_ids": ["problem-1", "problem-1"]},
    ]
    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            AssignmentCreate(**payload)


def test_course_schema_rejects_blank_code_or_title():
    assert CourseCreate(course_code="CSE-101", title="Intro").course_code == "CSE-101"
    for payload in (
        {"course_code": "", "title": "Intro"},
        {"course_code": "CSE-101", "title": " "},
    ):
        with pytest.raises(ValidationError):
            CourseCreate(**payload)


def test_course_update_normalizes_text_and_rejects_blank_required_fields():
    assert CourseUpdate(course_code=" CSE-101 ", title=" Intro ").model_dump(exclude_unset=True) == {
        "course_code": "CSE-101",
        "title": "Intro",
    }
    assert CourseUpdate(term="  ", description="  ").model_dump(exclude_unset=True) == {
        "term": None,
        "description": None,
    }
    for field in ("course_code", "title"):
        with pytest.raises(ValidationError):
            CourseUpdate(**{field: "   "})


def test_instructor_question_is_saved_to_selected_course_with_private_cases(db_session):
    instructor_user = add_account(db_session, username="instructor-1", role="instructor", password="valid-instructor-password")
    other_instructor = add_account(db_session, username="instructor-2", role="instructor", password="other-instructor-password")
    course = models.Course(course_code="CSE-401", title="Algorithms", instructor_id=instructor_user.instructor_profile.id)
    other_course = models.Course(course_code="CSE-402", title="Other course", instructor_id=other_instructor.instructor_profile.id)
    db_session.add_all([course, other_course])
    db_session.commit()

    payload = InstructorProblemCreate(
        title="Rotate an array",
        description="Rotate the input array by k positions.",
        difficulty="Medium",
        category="Arrays",
        target_time_complexity="O(n)",
        target_space_complexity="O(1)",
        course_id=course.id,
        test_cases=[
            {"input": "[1,2,3], 1", "expected_output": "[3,1,2]", "is_hidden": False},
            {"input": "[] , 0", "expected_output": "[]", "is_hidden": True},
        ],
    )
    created = create_instructor_problem(payload, db_session, instructor_user.instructor_profile)
    linked_assignment = db_session.query(models.Assignment).filter_by(id=created["assignment_id"]).one()
    saved_problem = db_session.get(models.Problem, created["id"])
    saved_cases = db_session.query(models.ProblemTestCase).filter_by(problem_id=created["id"]).order_by(models.ProblemTestCase.position).all()

    assert linked_assignment.course_id == course.id
    assert db_session.query(models.AssignmentProblem).filter_by(assignment_id=linked_assignment.id, problem_id=created["id"]).count() == 1
    assert [case.visibility for case in saved_cases] == ["PUBLIC", "HIDDEN"]
    assert len(created["test_cases"]) == 2
    assert saved_problem.description == payload.description
    assert any(problem["id"] == created["id"] and problem["course_code"] == "CSE-401"
               for problem in list_instructor_problems(db_session, instructor_user))
    assert get_problem(created["id"], db_session, instructor_user)["assignment_id"] == linked_assignment.id

    student_user = add_account(db_session, username="student-1", role="student", password="valid-student-password")
    db_session.add(models.Enrollment(student_id=student_user.student_profile.student_id, course_id=course.id, is_active=True))
    db_session.commit()
    student_questions = list_instructor_problems(db_session, student_user)
    student_question = next(problem for problem in student_questions if problem["id"] == created["id"])
    assert len(student_question["test_cases"]) == 1
    assert student_question["test_cases"][0]["is_hidden"] is False
    assert len(get_problem(created["id"], db_session, student_user)["test_cases"]) == 1
    stranger = add_account(db_session, username="student-2", role="student", password="valid-student-password")
    with pytest.raises(HTTPException) as outside_course:
        get_problem(created["id"], db_session, stranger)
    assert outside_course.value.status_code == 404

    payload.course_id = other_course.id
    with pytest.raises(HTTPException) as wrong_owner:
        create_instructor_problem(payload, db_session, instructor_user.instructor_profile)
    assert wrong_owner.value.status_code == 404


def test_assignment_create_persists_ordered_links_and_rejects_partial_invalid_create(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    instructor = instructor_user.instructor_profile
    course = models.Course(course_code="CSE-101", title="Intro", instructor_id=instructor.id)
    problems = [
        models.Problem(id=problem_id, title=problem_id, description="Problem", examples=[], constraints=[], starter_codes={}, test_cases=[])
        for problem_id in ("p-1", "p-2")
    ]
    db_session.add_all([course, *problems])
    db_session.commit()

    with pytest.raises(HTTPException) as invalid_problem:
        create_assignment(
            AssignmentCreate(title="Invalid", course_id=course.id, problem_ids=["p-1", "missing"]),
            db_session,
            instructor,
        )
    assert invalid_problem.value.status_code == 422
    assert db_session.query(models.Assignment).count() == 0

    created = create_assignment(
        AssignmentCreate(title="Ordered", course_id=course.id, problem_ids=["p-2", "p-1"]),
        db_session,
        instructor,
    )
    assert created.problems == ["p-2", "p-1"]
    links = db_session.query(models.AssignmentProblem).filter_by(assignment_id=created.id).order_by(
        models.AssignmentProblem.position
    ).all()
    assert [(link.position, link.problem_id) for link in links] == [(1, "p-2"), (2, "p-1")]


def test_assigned_submission_requires_active_enrollment_and_linked_problem(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student = models.Student(student_id="student-1", name="Student")
    other_student = models.Student(student_id="student-2", name="Other Student")
    course = models.Course(course_code="CSE-101", title="Intro", instructor_id=instructor_user.instructor_profile.id)
    problem = models.Problem(id="p-1", title="Problem", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    other_problem = models.Problem(id="p-2", title="Other", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([student, other_student, course, problem, other_problem])
    db_session.flush()
    assignment = models.Assignment(title="Assignment", course_id=course.id, status="ACTIVE")
    db_session.add(assignment)
    db_session.flush()
    db_session.add_all([
        models.Enrollment(student_id=student.student_id, course_id=course.id, is_active=True),
        models.AssignmentProblem(assignment_id=assignment.id, problem_id=problem.id, position=1),
    ])
    db_session.commit()

    assert get_student_assignment_for_problem(db_session, student.student_id, assignment.id, problem.id).id == assignment.id
    with pytest.raises(HTTPException) as not_enrolled:
        get_student_assignment_for_problem(db_session, other_student.student_id, assignment.id, problem.id)
    assert not_enrolled.value.status_code == 403
    with pytest.raises(HTTPException) as unassigned_problem:
        get_student_assignment_for_problem(db_session, student.student_id, assignment.id, other_problem.id)
    assert unassigned_problem.value.status_code == 403

    assignment.status = "CLOSED"
    db_session.commit()
    with pytest.raises(HTTPException) as closed_assignment:
        get_student_assignment_for_problem(db_session, student.student_id, assignment.id, problem.id)
    assert closed_assignment.value.status_code == 404


def test_assignment_content_is_frozen_after_submission_but_status_can_change(db_session):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student = models.Student(student_id="student-1", name="Student")
    course = models.Course(course_code="CSE-101", title="Intro", instructor_id=instructor_user.instructor_profile.id)
    problem = models.Problem(id="p-1", title="Problem", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([student, course, problem])
    db_session.flush()
    assignment = models.Assignment(title="Assignment", description="Original instructions", course_id=course.id, status="ACTIVE")
    db_session.add(assignment)
    db_session.flush()
    db_session.add_all([
        models.AssignmentProblem(assignment_id=assignment.id, problem_id=problem.id, position=1),
        models.Submission(submission_id="existing-submission", student_id=student.student_id, problem_id=problem.id, assignment_id=assignment.id, language="python", code="", status="EVALUATED", overall_score=50),
    ])
    db_session.commit()

    with pytest.raises(HTTPException) as frozen_content:
        update_assignment(assignment.id, AssignmentUpdate(title="Changed"), db_session, instructor_user.instructor_profile)
    assert frozen_content.value.status_code == 409

    closed = update_assignment(assignment.id, AssignmentUpdate(status="CLOSED"), db_session, instructor_user.instructor_profile)
    assert closed.status == "CLOSED"
    assert db_session.query(models.Submission).filter_by(submission_id="existing-submission").count() == 1


def test_submit_persists_authenticated_student_and_assignment_context(db_session, monkeypatch):
    instructor_user = add_account(
        db_session,
        username="instructor-1",
        role="instructor",
        password="valid-instructor-password",
    )
    student_user = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )
    student = student_user.student_profile
    course = models.Course(course_code="CSE-101", title="Intro", instructor_id=instructor_user.instructor_profile.id)
    problem = models.Problem(id="p-1", title="Problem", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([course, problem])
    db_session.flush()
    assignment = models.Assignment(title="Assignment", course_id=course.id, status="ACTIVE")
    db_session.add(assignment)
    db_session.flush()
    db_session.add_all([
        models.Enrollment(student_id=student.student_id, course_id=course.id, is_active=True),
        models.AssignmentProblem(assignment_id=assignment.id, problem_id=problem.id, position=1),
    ])
    db_session.commit()

    async def fake_execute(**_kwargs):
        return {"compile_status": "success", "passed_cases": 1, "failed_cases": 0, "total_cases": 1, "results": []}

    async def fake_complexity(*_args, **_kwargs):
        return {"time_complexity": "O(1)", "space_complexity": "O(1)"}

    async def fake_graph(_state):
        return {
            "execution_result": {"compile_status": "success", "passed_cases": 1, "failed_cases": 0, "total_cases": 1, "results": []},
            "overall_score": 90.0,
            "correctness_score": 100.0,
            "complexity_score": 90.0,
            "style_score": 90.0,
            "similarity_score": 10.0,
            "complexity_details": {"time_complexity": "O(1)", "space_complexity": "O(1)"},
            "assessment_flags": {},
            "feedback": {},
            "recommendations": {},
            "improved_code": {},
            "projected_score": {},
        }

    monkeypatch.setattr(main_module, "execute_code_sandboxed", fake_execute)
    monkeypatch.setattr(main_module, "analyze_student_complexity", fake_complexity)
    monkeypatch.setattr(main_module.evaluation_graph, "ainvoke", fake_graph)

    assigned_response = asyncio.run(submit_and_evaluate_code(
        SubmissionRequest(
            student_id="spoofed-student",
            problem_id=problem.id,
            language="python",
            code="print(1)",
            assignment_id=assignment.id,
        ),
        db_session,
        student,
    ))
    practice_response = asyncio.run(submit_and_evaluate_code(
        SubmissionRequest(
            student_id="another-spoof",
            problem_id=problem.id,
            language="python",
            code="print(1)",
        ),
        db_session,
        student,
    ))

    assigned_record = db_session.query(models.Submission).filter_by(submission_id=assigned_response.submission_id).one()
    practice_record = db_session.query(models.Submission).filter_by(submission_id=practice_response.submission_id).one()
    assert assigned_record.student_id == student.student_id
    assert assigned_record.assignment_id == assignment.id
    assert practice_record.student_id == student.student_id
    assert practice_record.assignment_id is None


def test_instructor_overview_uses_latest_owned_assignment_attempts_only(db_session):
    instructor_a_user = add_account(
        db_session,
        username="instructor-a",
        role="instructor",
        password="instructor-a-password",
    )
    instructor_b_user = add_account(
        db_session,
        username="instructor-b",
        role="instructor",
        password="instructor-b-password",
    )
    student = models.Student(student_id="student-1", name="Student")
    course_a = models.Course(course_code="A-101", title="Course A", instructor_id=instructor_a_user.instructor_profile.id)
    course_b = models.Course(course_code="B-101", title="Course B", instructor_id=instructor_b_user.instructor_profile.id)
    problem = models.Problem(id="p-1", title="Problem", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([student, course_a, course_b, problem])
    db_session.flush()
    assignment_a = models.Assignment(title="A Assignment", course_id=course_a.id, status="ACTIVE")
    assignment_b = models.Assignment(title="B Assignment", course_id=course_b.id, status="ACTIVE")
    db_session.add_all([assignment_a, assignment_b])
    db_session.flush()
    db_session.add_all([
        models.Enrollment(student_id=student.student_id, course_id=course_a.id, is_active=True),
        models.Enrollment(student_id=student.student_id, course_id=course_b.id, is_active=True),
    ])
    db_session.add_all([
        models.Submission(submission_id="a-old", student_id=student.student_id, problem_id=problem.id, assignment_id=assignment_a.id, language="python", code="", status="EVALUATED", overall_score=50, correctness_score=50),
        models.Submission(submission_id="a-new", student_id=student.student_id, problem_id=problem.id, assignment_id=assignment_a.id, language="python", code="", status="EVALUATED", overall_score=90, correctness_score=90),
        models.Submission(submission_id="practice", student_id=student.student_id, problem_id=problem.id, language="python", code="", status="EVALUATED", overall_score=100),
        models.Submission(submission_id="b-owned-elsewhere", student_id=student.student_id, problem_id=problem.id, assignment_id=assignment_b.id, language="python", code="", status="EVALUATED", overall_score=10),
    ])
    db_session.commit()

    overview = get_instructor_overview(db_session, instructor_a_user.instructor_profile)
    assert overview["total_students"] == 1
    assert overview["total_courses"] == 1
    assert overview["total_submissions"] == 2
    assert overview["class_avg_score"] == "90.0%"
    assert overview["highest_score"] == 90
    assert overview["lowest_score"] == 90
    assert overview["score_distribution"] == [
        {"range": "0-20", "count": 0, "heightPercent": 0},
        {"range": "21-40", "count": 0, "heightPercent": 0},
        {"range": "41-60", "count": 0, "heightPercent": 0},
        {"range": "61-80", "count": 0, "heightPercent": 0},
        {"range": "81-100", "count": 1, "heightPercent": 100.0},
    ]
    assignment_stats = build_assignment_stats(db_session, assignment_a)
    assert assignment_stats.total_attempts == 2
    assert assignment_stats.submitted_count == 1
    assert assignment_stats.avg_score == 90
    course_stats = build_course_stats(db_session, course_a)
    assert course_stats.submission_count == 2
    assert course_stats.unique_submitters == 1
    assert course_stats.avg_score == 90
    analytics = get_course_analytics(course_a.id, db_session, instructor_a_user.instructor_profile)
    assert analytics["total_submissions"] == 2
    assert analytics["completion_rate"] == 100.0
    assert analytics["avg_score"] == 90


def test_live_roster_uses_active_owned_enrollments_and_assessment_data(db_session):
    instructor_user = add_account(db_session, username="instructor-1", role="instructor", password="instructor-password")
    other_instructor = add_account(db_session, username="instructor-2", role="instructor", password="other-instructor-password")
    student_user = add_account(db_session, username="student-1", role="student", password="student-password")
    student = student_user.student_profile
    own_course = models.Course(course_code="CSE-101", title="Owned", instructor_id=instructor_user.instructor_profile.id)
    other_course = models.Course(course_code="CSE-102", title="Other", instructor_id=other_instructor.instructor_profile.id)
    problem = models.Problem(id="arrays-1", title="Arrays", category="Arrays", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([own_course, other_course, problem])
    db_session.flush()
    own_assignment = models.Assignment(title="Owned work", course_id=own_course.id, status="ACTIVE")
    other_assignment = models.Assignment(title="Other work", course_id=other_course.id, status="ACTIVE")
    db_session.add_all([own_assignment, other_assignment])
    db_session.flush()
    db_session.add_all([
        models.Enrollment(student_id=student.student_id, course_id=own_course.id, is_active=True),
        models.Enrollment(student_id=student.student_id, course_id=other_course.id, is_active=True),
        models.Submission(submission_id="own-score", student_id=student.student_id, problem_id=problem.id, assignment_id=own_assignment.id, language="python", code="", status="EVALUATED", overall_score=45),
        models.Submission(submission_id="other-score", student_id=student.student_id, problem_id=problem.id, assignment_id=other_assignment.id, language="python", code="", status="EVALUATED", overall_score=100),
    ])
    db_session.commit()

    roster = get_instructor_roster(db_session, instructor_user.instructor_profile)

    assert len(roster) == 1
    assert roster[0].id == student.student_id
    assert roster[0].submissions_count == 1
    assert roster[0].avg_score == 45
    assert roster[0].weak_topics == ["Arrays"]
    assert roster[0].status == "At Risk"


def test_similarity_review_uses_owned_course_pairs_and_persists_actions(db_session):
    instructor_user = add_account(db_session, username="similarity-instructor", role="instructor", password="instructor-password")
    student_a_user = add_account(db_session, username="similarity-student-a", role="student", password="student-password-a")
    student_b_user = add_account(db_session, username="similarity-student-b", role="student", password="student-password-b")
    course = models.Course(course_code="SIM-101", title="Similarity course", instructor_id=instructor_user.instructor_profile.id)
    problem = models.Problem(id="similarity-problem", title="Pair Comparison", description="Task", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add_all([course, problem])
    db_session.flush()
    assignment = models.Assignment(title="Similarity task", course_id=course.id, status="ACTIVE")
    db_session.add(assignment)
    db_session.flush()
    code = """def compute(values):
    total = 0
    for value in values:
        if value > 3:
            total += value * 2
        else:
            total += value - 1
    return total
"""
    db_session.add_all([
        models.Submission(submission_id="SIM-A", student_id=student_a_user.student_profile.student_id, problem_id=problem.id, assignment_id=assignment.id, language="python", code=code, status="EVALUATED", overall_score=90),
        models.Submission(submission_id="SIM-B", student_id=student_b_user.student_profile.student_id, problem_id=problem.id, assignment_id=assignment.id, language="python", code=code, status="EVALUATED", overall_score=88),
    ])
    db_session.commit()

    response = list_instructor_similarity_cases(db_session, instructor_user.instructor_profile)
    assert response["total_cases"] == 1
    case = response["cases"][0]
    assert case["similarityPercentage"] == 100
    assert case["studentA"]["name"] != case["studentB"]["name"]

    updated = update_instructor_similarity_case(case["id"], "request-review", db_session, instructor_user.instructor_profile)
    assert updated["status"] == "review_requested"
    refreshed = list_instructor_similarity_cases(db_session, instructor_user.instructor_profile)
    assert refreshed["cases"][0]["reviewStatus"] == "review_requested"

    update_instructor_similarity_case(case["id"], "dismiss", db_session, instructor_user.instructor_profile)
    assert list_instructor_similarity_cases(db_session, instructor_user.instructor_profile)["total_cases"] == 0


def test_student_course_request_approval_leave_and_notifications(db_session):
    instructor_user = add_account(db_session, username="course-owner", role="instructor", password="instructor-password")
    student_user = add_account(db_session, username="course-joiner", role="student", password="student-password")
    course = models.Course(course_code="JOIN-101", title="Joining Flow", instructor_id=instructor_user.instructor_profile.id)
    db_session.add(course)
    db_session.commit()

    available = get_available_student_courses(db_session, student_user.student_profile)
    assert available[0].enrollment_status == "AVAILABLE"
    request_response = Response()
    requested = request_course_enrollment(
        CourseRequestCreate(course_id=course.id), request_response, db_session, student_user.student_profile
    )
    assert requested.status == "PENDING"
    assert request_response.status_code == 200
    assert get_available_student_courses(db_session, student_user.student_profile)[0].enrollment_status == "PENDING"
    assert len(get_instructor_course_requests(db_session, instructor_user.instructor_profile, course.id)) == 1

    instructor_notices = get_notifications(db_session, instructor_user)
    assert len(instructor_notices) == 1
    assert instructor_notices[0].event_type == "course_join_request"
    approved = decide_course_request(requested.id, "approve", db_session, instructor_user.instructor_profile)
    assert approved.status == "APPROVED"
    assert get_available_student_courses(db_session, student_user.student_profile)[0].enrollment_status == "ENROLLED"
    assert get_notifications(db_session, student_user)[0].event_type == "course_request_decision"

    leave_student_course(course.id, db_session, student_user.student_profile)
    assert get_available_student_courses(db_session, student_user.student_profile)[0].enrollment_status == "AVAILABLE"
    assert any(notice.event_type == "student_left_course" for notice in get_notifications(db_session, instructor_user))

    mark_all_notifications_read(db_session, instructor_user)
    assert not any(notice.is_read is False for notice in get_notifications(db_session, instructor_user))


def test_course_request_rejection_can_be_resubmitted_and_is_owner_scoped(db_session):
    instructor_user = add_account(db_session, username="course-owner-2", role="instructor", password="instructor-password")
    other_instructor_user = add_account(db_session, username="course-owner-3", role="instructor", password="instructor-password")
    student_user = add_account(db_session, username="course-joiner-2", role="student", password="student-password")
    course = models.Course(course_code="JOIN-102", title="Request Review", instructor_id=instructor_user.instructor_profile.id)
    other_course = models.Course(course_code="JOIN-103", title="Other Course", instructor_id=other_instructor_user.instructor_profile.id)
    db_session.add_all([course, other_course])
    db_session.commit()

    response = Response()
    first_request = request_course_enrollment(CourseRequestCreate(course_id=course.id), response, db_session, student_user.student_profile)
    assert first_request.status == "PENDING"
    with pytest.raises(HTTPException) as wrong_owner:
        decide_course_request(first_request.id, "approve", db_session, other_instructor_user.instructor_profile)
    assert wrong_owner.value.status_code == 404

    rejected = decide_course_request(first_request.id, "reject", db_session, instructor_user.instructor_profile)
    assert rejected.status == "REJECTED"
    assert get_available_student_courses(db_session, student_user.student_profile)[0].enrollment_status == "AVAILABLE"

    second_request = request_course_enrollment(CourseRequestCreate(course_id=course.id), Response(), db_session, student_user.student_profile)
    assert second_request.id != first_request.id
    assert second_request.status == "PENDING"


def test_notification_read_state_is_private_to_recipient(db_session):
    instructor_user = add_account(db_session, username="notice-owner", role="instructor", password="instructor-password")
    student_user = add_account(db_session, username="notice-student", role="student", password="student-password")
    notice = models.Notification(
        recipient_user_id=instructor_user.id,
        event_type="course_join_request",
        title="Request",
        message="A student requested access.",
    )
    db_session.add(notice)
    db_session.commit()

    with pytest.raises(HTTPException) as private_notice:
        main_module.mark_notification_read(notice.id, db_session, student_user)
    assert private_notice.value.status_code == 404
    assert get_notifications(db_session, instructor_user)[0].is_read is False


def test_submission_history_is_private_and_zero_score_is_not_treated_as_missing(db_session):
    student_user = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )
    other_user = add_account(
        db_session,
        username="student-2",
        role="student",
        password="other-student-password",
    )
    problem = models.Problem(id="p-1", title="Problem", description="Statement", examples=[], constraints=[], starter_codes={}, test_cases=[])
    db_session.add(problem)
    db_session.flush()
    submission = models.Submission(
        submission_id="zero-score",
        student_id=student_user.student_profile.student_id,
        problem_id=problem.id,
        language="python",
        code="",
        status="EVALUATED",
        overall_score=0,
    )
    db_session.add(submission)
    db_session.commit()

    assert average_score([submission]) == 0
    assert [record.submission_id for record in list_submissions(None, db_session, student_user.student_profile)] == ["zero-score"]
    with pytest.raises(HTTPException) as spoofed_history:
        list_submissions(other_user.student_profile.student_id, db_session, student_user.student_profile)
    assert spoofed_history.value.status_code == 403
    with pytest.raises(HTTPException) as private_detail:
        get_submission("zero-score", db_session, other_user.student_profile)
    assert private_detail.value.status_code == 404


def test_empty_student_analytics_has_no_fabricated_scores_or_trend(db_session):
    user = add_account(
        db_session,
        username="student-1",
        role="student",
        password="valid-student-password",
    )
    db_session.add(models.Problem(
        id="p-1",
        title="Problem",
        description="Statement",
        examples=[],
        constraints=[],
        starter_codes={},
        test_cases=[],
    ))
    db_session.commit()

    analytics = get_student_analytics(user.student_profile.student_id, db_session, user.student_profile)
    assert analytics.overall_score is None
    assert analytics.problems_solved == 0
    assert analytics.total_problems == 1
    assert analytics.score_trend == []
    assert analytics.category_breakdown == []
    assert analytics.weak_topics == []


def test_student_latest_problem_attempts_collapse_across_assignments():
    old_attempt = models.Submission(
        id=1,
        submission_id="old",
        student_id="student-1",
        problem_id="p-1",
        assignment_id=1,
        language="python",
        code="",
        status="EVALUATED",
        overall_score=50,
    )
    new_attempt = models.Submission(
        id=2,
        submission_id="new",
        student_id="student-1",
        problem_id="p-1",
        assignment_id=2,
        language="python",
        code="",
        status="EVALUATED",
        overall_score=80,
    )
    assert len(latest_assessed_attempts([old_attempt, new_attempt])) == 2
    assert latest_assessed_attempts([old_attempt, new_attempt], preserve_assignment=False) == [new_attempt]
