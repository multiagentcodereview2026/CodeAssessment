#!/usr/bin/env python3
"""Test script for instructor APIs."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_overview():
    print("=== Testing /api/instructor/overview ===")
    resp = requests.get(f"{BASE_URL}/api/instructor/overview")
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

def test_create_course():
    print("\n=== Testing POST /api/instructor/courses ===")
    data = {"course_code": "CSE-301", "title": "Data Structures", "term": "Fall 2024"}
    resp = requests.post(f"{BASE_URL}/api/instructor/courses", json=data)
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

def test_get_courses():
    print("\n=== Testing GET /api/instructor/courses ===")
    resp = requests.get(f"{BASE_URL}/api/instructor/courses")
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

def test_enroll_student():
    print("\n=== Testing POST /api/instructor/enrollments ===")
    data = {"student_id": "24BD1A058Z", "course_id": 1}
    resp = requests.post(f"{BASE_URL}/api/instructor/enrollments", json=data)
    print(json.dumps(resp.json(), indent=2))
    return resp.json()

if __name__ == "__main__":
    overview = test_overview()
    course = test_create_course()
    courses = test_get_courses()
    try:
        enrollment = test_enroll_student()
    except Exception as e:
        print(f"Enrollment error: {e}")
    overview2 = test_overview()
    print("\n=== Final Overview ===")
    print(json.dumps(overview2, indent=2))