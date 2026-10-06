from collections import Counter


def build_ngrams(tokens: list[str], n: int = 3) -> Counter:
    """Считает частоты n-грамм токенов."""
    if len(tokens) < n:
        return Counter()
    return Counter(
        tuple(tokens[i:i + n])
        for i in range(len(tokens) - n + 1)
    )