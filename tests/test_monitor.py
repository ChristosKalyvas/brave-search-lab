from bravelab.monitor import TrendMonitor, age_to_hours, freshness_weight


def test_age_parsing():
    assert age_to_hours("2 hours ago") == 2
    assert age_to_hours("3 days ago") == 72
    assert age_to_hours(None) == 24 * 7          # unknown -> a week


def test_freshness_decay():
    assert freshness_weight(0) == 1.0
    assert round(freshness_weight(24), 3) == 0.5  # 24h half-life


def test_pulse_and_leaderboard(fake_client):
    monitor = TrendMonitor(fake_client)
    pulse = monitor.pulse("openai")
    assert pulse.article_count == 2
    assert pulse.breaking is True
    assert pulse.buzz_score > 0
    board = monitor.leaderboard(["openai", "anthropic"])
    assert len(board) == 2
    assert board[0].buzz_score >= board[1].buzz_score
