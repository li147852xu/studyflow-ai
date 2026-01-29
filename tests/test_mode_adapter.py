from service.api_mode_adapter import ApiModeAdapter, SlidesGenerationResult, TextGenerationResult


def test_mode_adapter_api_response_shape(monkeypatch):
    adapter = ApiModeAdapter("api", "http://example.com")

    def fake_post(path, payload):
        if path == "/generate" and payload["action_type"] == "slides":
            return {
                "deck": "deck",
                "qa": ["q1"],
                "citations": ["c1"],
                "run_id": "run",
                "asset_id": "asset",
                "asset_version_id": "ver",
                "asset_version_index": 1,
            }
        return {
            "content": "text",
            "citations": ["c1"],
            "run_id": "run",
            "asset_id": "asset",
            "asset_version_id": "ver",
            "asset_version_index": 1,
        }

    monkeypatch.setattr(adapter, "_post", fake_post)

    result = adapter.generate(action_type="paper_card", payload={"workspace_id": "ws"})
    assert isinstance(result, TextGenerationResult)
    assert result.content == "text"

    slides = adapter.generate(action_type="slides", payload={"workspace_id": "ws"})
    assert isinstance(slides, SlidesGenerationResult)
    assert slides.deck == "deck"
