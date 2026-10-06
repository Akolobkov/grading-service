from typing import Iterator

import tree_sitter_cpp
from tree_sitter import Language, Node, Parser

_CXX = Language(tree_sitter_cpp.language())
_PARSER = Parser(_CXX)

_NORMALIZE = {
    "identifier": "ident",
    "field_identifier": "ident",
    "type_identifier": "type",         # vector, string → type
    "namespace_identifier": "type",    # std → type
    "number_literal": "literal",
    "string_literal": "literal",
    "raw_string_literal": "literal",
    "char_literal": "literal",
    "true": "literal",
    "false": "literal",
    "nullptr": "literal",
}


_SKIP_TYPES = frozenset({
    "comment",
    "line_comment",
    "block_comment",
})
def _iter_leaves(node: Node) -> Iterator[Node]:
    """Обходит дерево, отдаёт только листья (узлы без детей)."""
    if node.child_count == 0:
        yield node
    else:
        for child in node.children:
            yield from _iter_leaves(child)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")



def tokenize(code: str) -> list[str]:
    """
    Токенизирует C++ код: возвращает нормализованную последовательность токенов.

    Идентификаторы → "ident", литералы → "literal", типы → "type".
    Комментарии выкидываются. Операторы и ключевые слова — как есть.
    """
    source = code.encode("utf-8")
    tree = _PARSER.parse(source)

    tokens: list[str] = []
    for leaf in _iter_leaves(tree.root_node):
        if leaf.type in _SKIP_TYPES:
            continue

        if leaf.is_named:
            token = _NORMALIZE.get(leaf.type, _node_text(leaf, source))
        else:
            token = _node_text(leaf, source)

        if token:
            tokens.append(token)

    return tokens