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
        docker_image="python:3.11-slim",
        source_filename="solution.py",
        file_extension=".py",
        compile_cmd=None,
        run_cmd=["python3", "solution.py"]
    ),
    "c": LanguageConfig(
        name="c",
        docker_image="gcc:13",
        source_filename="solution.c",
        file_extension=".c",
        compile_cmd=["gcc", "-O2", "solution.c", "-o", "solution"],
        run_cmd=["./solution"]
    ),
    "cpp": LanguageConfig(
        name="cpp",
        docker_image="gcc:13",
        source_filename="solution.cpp",
        file_extension=".cpp",
        compile_cmd=["g++", "-O2", "solution.cpp", "-o", "solution"],
        run_cmd=["./solution"]
    ),
    "java": LanguageConfig(
        name="java",
        # The old openjdk:17-slim tag is no longer published.  Temurin is a
        # maintained Java 17 JDK image and works with the existing javac/java
        # commands below.
        docker_image="eclipse-temurin:17-jdk",
        source_filename="Main.java",
        file_extension=".java",
        compile_cmd=["javac", "Main.java"],
        run_cmd=["java", "Main"]
    ),
    "javascript": LanguageConfig(
        name="javascript",
        docker_image="node:20-slim",
        source_filename="solution.js",
        file_extension=".js",
        compile_cmd=None,
        run_cmd=["node", "solution.js"]
    )
}

LANGUAGE_ALIASES = {
    "py": "python",
    "python3": "python",
    "c++": "cpp",
    "g++": "cpp",
    "js": "javascript",
    "node": "javascript",
    "ts": "javascript",
    "typescript": "javascript"
}


def get_language_config(language: str) -> LanguageConfig | None:
    lang_key = language.strip().lower()
    normalized = LANGUAGE_ALIASES.get(lang_key, lang_key)
    return LANGUAGES.get(normalized)
