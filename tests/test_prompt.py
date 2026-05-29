import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from prompt import build_prompt

CHUNKS = [
    {"text": "Use jf mvn deploy to publish artifacts.", "source": "rdme-artifactory/maven.md", "section": "Maven"},
    {"text": "Configure with jf mvn-config first.", "source": "rdme-artifactory/maven.md", "section": "Config"},
]

def test_prompt_contains_query():
    p = build_prompt("how to deploy?", CHUNKS)
    assert "how to deploy?" in p

def test_prompt_contains_chunk_text():
    p = build_prompt("how to deploy?", CHUNKS)
    assert "jf mvn deploy" in p
    assert "jf mvn-config" in p

def test_prompt_contains_source():
    p = build_prompt("how to deploy?", CHUNKS)
    assert "rdme-artifactory/maven.md" in p

def test_prompt_with_no_chunks():
    p = build_prompt("anything?", [])
    assert "anything?" in p
    assert len(p) > 0


def test_prompt_includes_history():
    history = [
        {"role": "user", "content": "what is Artifactory?"},
        {"role": "assistant", "content": "Artifactory is a repository manager."},
    ]
    p = build_prompt("how do I configure it?", CHUNKS, history=history)
    assert "what is Artifactory?" in p
    assert "Artifactory is a repository manager." in p


def test_prompt_without_history_unchanged():
    p1 = build_prompt("how to deploy?", CHUNKS)
    p2 = build_prompt("how to deploy?", CHUNKS, history=None)
    assert p1 == p2


def test_prompt_history_capped_at_10_messages():
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"} for i in range(20)]
    p = build_prompt("question?", CHUNKS, history=history)
    assert "msg0" not in p
    assert "msg10" in p
