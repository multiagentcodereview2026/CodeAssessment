from dataclasses import dataclass


@dataclass
class LanguageConfig:

    name: str
    docker_image: str
    source_filename: str
    file_extension: str
    compile_cmd: list[str] | None
    run_cmd: list[str]


LANGUAGES = {
    "python": LanguageConfig(
        name="python",
        docker_image="codeassessment-python:latest",
        source_filename="solution.py",
        file_extension=".py",
        compile_cmd=None,
        run_cmd=[
            "python3",
            "solution.py"
        ]
    ),
    "c": LanguageConfig(
        name="c",
        docker_image="codeassessment-c:latest",
        source_filename="solution.c",
        file_extension=".c",
        compile_cmd=[
            "gcc",
            "-O2",
            "solution.c",
            "-o",
            "solution"
        ],
        run_cmd=[
            "./solution"
        ]
    ),
    "cpp": LanguageConfig(
        name="cpp",
        docker_image="codeassessment-cpp:latest",
        source_filename="solution.cpp",
        file_extension=".cpp",
        compile_cmd=[
            "g++",
            "-O2",
            "solution.cpp",
            "-o",
            "solution"
        ],
        run_cmd=[
            "./solution"
        ]
    ),
    "java": LanguageConfig(
        name="java",
        docker_image="codeassessment-java:latest",
        source_filename="Main.java",
        file_extension=".java",
        compile_cmd=[
            "javac",
            "Main.java"
        ],
        run_cmd=[
            "java",
            "Main"
        ]
    )
}


def get_language_config(language: str) -> LanguageConfig | None:
    lang_key = language.strip().lower()
    return LANGUAGES.get(lang_key)


def validate_language_for_problem(language: str, supported_languages_str: str) -> bool:
    lang_key = language.strip().lower()

    if lang_key not in LANGUAGES:
        return False

    allowed_list = [
        item.strip().lower()
        for item in supported_languages_str.split(",")
        if item.strip()
    ]

    return lang_key in allowed_list
