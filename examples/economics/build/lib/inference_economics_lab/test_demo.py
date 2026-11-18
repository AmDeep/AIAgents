import pytest

from inference_economics_lab.demo import ResponseCache, parallel_tools, percentile, route


def test_router_selects_by_threshold_and_rejects_negative():
    assert route(2) == "small" and route(6) == "large"
    with pytest.raises(ValueError):
        route(-1)
    with pytest.raises(ValueError):
        route(2, threshold=-1)


def test_cache_is_keyed_by_model_and_prompt():
    cache = ResponseCache()
    calls = []
    compute = lambda: calls.append(1) or "answer"
    assert cache.get_or_compute("small", "p", compute) == ("answer", False)
    assert cache.get_or_compute("small", "p", compute) == ("answer", True)
    assert cache.get_or_compute("large", "p", compute)[1] is False
    assert len(calls) == 2


def test_cache_key_encoding_avoids_separator_collisions():
    assert ResponseCache.key("a\0b", "c") != ResponseCache.key("a", "b\0c")


def test_parallel_tools_return_named_results():
    assert parallel_tools({"a": lambda: 1, "b": lambda: 2}) == {"a": 1, "b": 2}
    with pytest.raises(ValueError):
        parallel_tools({}, max_workers=0)
    with pytest.raises(RuntimeError, match="tool failure"):
        parallel_tools({"bad": lambda: (_ for _ in ()).throw(RuntimeError("tool failure"))})


def test_nearest_rank_percentile_and_invalid_inputs():
    assert percentile([10, 20, 30, 40, 50], 95) == 50
    assert percentile([10, 20, 30, 40, 50], 50) == 30
    with pytest.raises(ValueError):
        percentile([], 95)
    assert percentile([10, 20, 30, 40, 50], 0) == 10
    assert percentile([10, 20, 30, 40, 50], 100) == 50
    with pytest.raises(ValueError):
        percentile([1, float("nan")], 95)
    with pytest.raises(ValueError):
        percentile([1], float("inf"))
