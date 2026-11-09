"""The integrity check and two helpers of the pre-checks, using temporary Git repositories."""

import json
import shutil
import subprocess

import integrity
import prechecks
import pytest

GIT = shutil.which("git")
TASKS = "specs/001-lcgkit-assistant/tasks.md"
TWO_TESTS = "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n"


def git(root, *args):
    subprocess.run(
        [
            GIT,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "-c",
            "tag.gpgSign=false",
            "-c",
            "commit.gpgSign=false",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture(name="repo")
def repo_fixture(tmp_path):
    git(tmp_path, "init", "-q")
    write(tmp_path, "tests/test_a.py", TWO_TESTS)
    write(tmp_path, "evals/dataset.json", json.dumps({"cases": [{}, {}, {}]}))
    write(tmp_path, ".harness/run.py", "x = 1\n")
    write(tmp_path, "pyproject.toml", "[project]\n")
    write(tmp_path, "src/pkg.py", "y = 1\n")
    write(tmp_path, TASKS, "- [ ] T001 one\n- [ ] T002 two\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "tag", "-a", integrity.TAG, "-m", "test_functions=2 dataset_cases=3")
    return tmp_path


def rules(root):
    return {p["rule"] for p in integrity.check(root)}


@pytest.mark.fr("FR-030")
def test_a_clean_repository_passes(repo):
    assert integrity.check(repo) == []


@pytest.mark.fr("FR-030")
@pytest.mark.parametrize(
    "name", ["tests/test_a.py", "evals/dataset.json", ".harness/run.py", "pyproject.toml"]
)
def test_a_changed_protected_file_fails(repo, name):
    path = repo / name
    path.write_text(path.read_text() + "\n")
    assert "protected-path-changed" in rules(repo)


@pytest.mark.fr("FR-030")
@pytest.mark.parametrize("name", ["tests/test_new.py", "evals/new.json", ".harness/new.py"])
def test_a_new_protected_file_fails(repo, name):
    write(repo, name, "z = 1\n")
    assert "protected-path-changed" in rules(repo)


@pytest.mark.fr("FR-030")
def test_ticking_a_task_passes_and_any_other_change_fails(repo):
    write(repo, TASKS, "- [x] T001 one\n- [ ] T002 two\n")
    assert integrity.check(repo) == []
    write(repo, TASKS, "- [x] T001 one\n- [ ] T002 changed\n")
    assert "protected-path-changed" in rules(repo)


@pytest.mark.fr("FR-030")
def test_fewer_tests_or_cases_than_the_tag_fails(repo):
    (repo / "tests" / "test_a.py").write_text("def test_a():\n    pass\n")
    assert "test-count" in rules(repo)
    git(repo, "checkout", "--", "tests")
    write(repo, "evals/dataset.json", json.dumps({"cases": [{}]}))
    assert "case-count" in rules(repo)


@pytest.mark.fr("FR-030")
@pytest.mark.parametrize(
    "line",
    [
        "x = 1  # noqa: E501",
        "@pytest.mark.skip",
        "@pytest.mark.xfail",
        "z = 1  # nosec",
        "z = 1  # type: ignore",
    ],
)
def test_a_new_forbidden_marker_fails(repo, line):
    (repo / "src" / "pkg.py").write_text(f"y = 1\n{line}\n")
    assert "forbidden-marker" in rules(repo)


@pytest.mark.fr("FR-030")
def test_a_missing_tag_or_annotation_fails(repo):
    git(repo, "tag", "-d", integrity.TAG)
    assert rules(repo) == {"baseline-tag"}
    git(repo, "tag", "-a", integrity.TAG, "-m", "no counts here")
    assert "baseline-annotation" in rules(repo)


@pytest.mark.fr("FR-030")
def test_tracked_copy_holds_tracked_and_untracked_files_but_not_an_ignored_env(tmp_path):
    git(tmp_path, "init", "-q")
    write(tmp_path, ".gitignore", ".env\n")
    write(tmp_path, "tracked.txt", "a")
    git(tmp_path, "add", ".")
    write(tmp_path, "untracked.txt", "b")
    write(tmp_path, ".env", "GEMINI_API_KEY=x")
    copy = prechecks.tracked_copy(tmp_path)
    try:
        assert {p.name for p in copy.iterdir()} == {".gitignore", "tracked.txt", "untracked.txt"}
    finally:
        shutil.rmtree(copy)


@pytest.mark.fr("FR-030")
def test_env_is_ignored_follows_the_gitignore(tmp_path):
    git(tmp_path, "init", "-q")
    assert not prechecks.env_is_ignored(tmp_path)
    write(tmp_path, ".gitignore", ".env\n")
    assert prechecks.env_is_ignored(tmp_path)
