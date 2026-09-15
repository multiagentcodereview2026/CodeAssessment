import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import main
from database import Base, get_db


@pytest.fixture
def client(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(main, 'engine', engine)
    monkeypatch.setattr(main, 'SessionLocal', factory)
    def session():
        with factory() as db:
            yield db
    main.app.dependency_overrides[get_db] = session
    with TestClient(main.app) as client:
        yield client
    main.app.dependency_overrides.clear()
    engine.dispose()


def account(client, name, role):
    r = client.post('/api/auth/register', json={'username': name, 'email': f'{name}@test.local', 'password': 'test-password', 'role': role})
    assert r.status_code == 201, r.text
    r = client.post('/api/auth/login', data={'username': name, 'password': 'test-password'})
    assert r.status_code == 200, r.text
    return {'Authorization': 'Bearer ' + r.json()['access_token']}


def question():
    return {'title': 'Echo an integer', 'description': 'Read an integer and print it.', 'course_code': 'CS101',
            'constraints': ['O(1) time required', 'O(1) space required'],
            'test_cases': [{'input': '7', 'expected_output': '7', 'is_hidden': False},
                           {'input': '83117', 'expected_output': '83117', 'is_hidden': True}]}


def test_publish_notify_submit_and_restore(client, monkeypatch):
    teacher = account(client, 'teacher', 'instructor')
    student = account(client, 'student', 'student')
    other = account(client, 'other', 'student')
    r = client.post('/api/problems', json=question(), headers=teacher)
    assert r.status_code == 201, r.text
    pid = r.json()['id']
    assert len(client.get(f'/api/problems/{pid}', headers=student).json()['test_cases']) == 1
    notices = client.get('/api/announcements', headers=student).json()
    assert notices[0]['problemId'] == pid and not notices[0]['read']
    assert client.patch(f'/api/announcements/{pid}/read', headers=student).status_code == 200
    assert client.get('/api/announcements', headers=student).json()[0]['read']
    assert not client.get('/api/announcements', headers=other).json()[0]['read']

    async def execution(code, language, cases):
        assert len(cases) == 2
        return {'compile_status': 'success', 'execution_status': 'completed', 'passed_cases': 2, 'failed_cases': 0,
                'total_cases': 2, 'runtime_ms': 1, 'memory_kb': 0, 'results': [
                    {'status': 'accepted', **case, 'actual_output': case['expected_output']} for case in cases]}
    monkeypatch.setattr(main, 'run_checked', execution)
    r = client.post('/api/submissions/submit', headers=student, json={'student_id': 'other', 'problem_id': pid, 'language': 'python', 'code': 'print(input())'})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['student_id'] == 'student'
    assert result['correctness_score'] == 100
    assert result['style_score'] is None
    assert '83117' not in r.text
    sid = result['submission_id']
    saved = client.get(f'/api/submissions/{sid}', headers=student).json()
    assert saved['feedback'] == result['feedback']
    assert saved['complexity_details'] == result['complexity_details']
    assert saved['score_breakdown'] == result['score_breakdown']
    assert client.get(f'/api/submissions/{sid}', headers=other).status_code == 403
    assert client.get(f'/api/submissions/{sid}', headers=teacher).status_code == 200
    assert client.get('/api/submissions', headers=other).json() == []
    stats = client.get('/api/instructor/overview', headers=teacher).json()
    assert stats['total_students'] == 2 and stats['total_submissions'] == 1
    assert client.delete(f'/api/problems/{pid}', headers=teacher).status_code == 409


def test_roles_and_invalid_login(client):
    student = account(client, 'student', 'student')
    assert client.post('/api/auth/login', data={'username': 'student', 'password': 'wrong'}).status_code == 401
    assert client.post('/api/problems', json=question(), headers=student).status_code == 403
    assert client.get('/api/submissions').status_code == 401
    assert client.get('/api/instructor/overview', headers=student).status_code == 403


def test_question_edits_preserve_empty_values(client):
    teacher = account(client, 'teacher', 'instructor')
    data = question()
    data['test_cases'][0] = {'input': '', 'expected_output': '', 'is_hidden': False}
    r = client.post('/api/problems', headers=teacher, json=data)
    assert r.status_code == 201, r.text
    pid = r.json()['id']
    data['title'] = 'Updated question'
    r = client.put(f'/api/problems/{pid}', headers=teacher, json=data)
    assert r.status_code == 200 and r.json()['test_cases'][0]['expected_output'] == ''
    assert client.delete(f'/api/problems/{pid}', headers=teacher).status_code == 200


def test_execution_unavailable_is_explicit(client, monkeypatch):
    student = account(client, 'student', 'student')
    async def unavailable(*args, **kwargs):
        raise RuntimeError('offline')
    monkeypatch.setattr(main, 'execute_code_sandboxed', unavailable)
    r = client.post('/api/submissions/run', headers=student, json={'language': 'python', 'code': 'print(1)', 'test_cases': [{'input': '', 'expected_output': '1'}]})
    assert r.status_code == 503
