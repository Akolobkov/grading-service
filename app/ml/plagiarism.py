import math
from collections import Counter


_EPSILON = 1e-10


def _to_probabilities(counter: Counter) -> dict:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {ngram: count / total for ngram, count in counter.items()}


def symmetric_cross_entropy(counter_a: Counter, counter_b: Counter) -> float:
    """Симметричная кросс-энтропия. Меньше → похожее."""
    p = _to_probabilities(counter_a)
    q = _to_probabilities(counter_b)
    if not p or not q:
        return float("inf")

    def _ce(p: dict, q: dict) -> float:
        total = 0.0
        for ngram, prob in p.items():
            q_prob = q.get(ngram, _EPSILON)
            total += prob * math.log(q_prob)
        return -total

    return (_ce(p, q) + _ce(q, p)) / 2


def normalized_cross_entropy(counter_a: Counter, counter_b: Counter) -> float:
    """Кросс-энтропия, нормированная на число уникальных n-грамм."""
    p = _to_probabilities(counter_a)
    q = _to_probabilities(counter_b)
    if not p or not q:
        return float("inf")

    def _ce(p: dict, q: dict) -> float:
        total = 0.0
        for ngram, prob in p.items():
            q_prob = q.get(ngram, _EPSILON)
            total += prob * math.log(q_prob)
        return -total

    raw = (_ce(p, q) + _ce(q, p)) / 2
    return raw / max(len(p), len(q))


def js_divergence(counter_a: Counter, counter_b: Counter) -> float:
    """
    Jensen-Shannon divergence. 0 → идентичны, log(2) ≈ 0.693 → максимально разные.
    Принимает Counter и сам нормирует.
    """
    p = _to_probabilities(counter_a)
    q = _to_probabilities(counter_b)
    if not p or not q:
        return float("inf")

    # Объединение ключей
    keys = set(p) | set(q)

    # Смешанное распределение m = (p + q) / 2
    m = {
        k: (p.get(k, _EPSILON) + q.get(k, _EPSILON)) / 2
        for k in keys
    }

    def _kl(a: dict, b: dict) -> float:
        total = 0.0
        for k, prob in a.items():
            if prob > 0:
                total += prob * math.log(prob / b[k])
        return total

    return (_kl(p, m) + _kl(q, m)) / 2