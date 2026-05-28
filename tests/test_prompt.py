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
