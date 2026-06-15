from bravelab.rag import answer_question, _extractive_answer


def test_answer_has_citations_and_sources(fake_client):
    answer = answer_question("What is the Brave Search API?", fake_client, top_k=2)
    assert answer.sources, "expected sources"
    assert "[1]" in answer.text
    assert all(s.url.startswith("http") for s in answer.sources)
    rendered = answer.render()
    assert "Sources:" in rendered


def test_custom_answerer_is_used(fake_client):
    answer = answer_question(
        "anything", fake_client, answerer=lambda q, r: "CUSTOM"
    )
    assert answer.text == "CUSTOM"


def test_extractive_handles_empty():
    assert "couldn't find" in _extractive_answer("q", [])
