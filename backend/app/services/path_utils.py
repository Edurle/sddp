import copy
import re
from typing import Any


class PathSyntaxError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class MultipleMatchError(Exception):
    pass


def _tokenize(path: str) -> list[tuple[str, Any]]:
    if not path or not path.strip():
        raise PathSyntaxError(f"路径语法非法：'{path}' 为空。路径不能为空。")
    tokens: list[tuple[str, Any]] = []
    pos = 0
    n = len(path)
    expect_key = True
    while pos < n:
        ch = path[pos]
        if ch == ".":
            if pos == 0 or path[pos - 1] == "." or path[pos - 1] == "[":
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 在位置 {pos} 处出现多余点号。"
                )
            pos += 1
            expect_key = True
            continue
        if ch == "[":
            end = path.find("]", pos)
            if end == -1:
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 中 '[' 缺少右括号 ']'。"
                )
            inner = path[pos + 1:end].strip()
            if inner == "":
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 中 '[]' 缺少下标或键值。"
                    f"用法：a[0] / a[-1] / a[name=xxx]"
                )
            if "=" in inner:
                key, _, val = inner.partition("=")
                key = key.strip()
                val = val.strip()
                if not key:
                    raise PathSyntaxError(
                        f"路径语法非法：'{path}' 中 '[{inner}]' 键名缺失。用法：[name=xxx]"
                    )
                tokens.append(("match", (key, val)))
            else:
                try:
                    idx = int(inner)
                except ValueError:
                    raise PathSyntaxError(
                        f"路径语法非法：'{path}' 中 '[{inner}]' 既非整数下标也非键值匹配。"
                        f"用法：a[0] / a[-1] / a[name=xxx]"
                    )
                tokens.append(("index", idx))
            pos = end + 1
            expect_key = False
            continue
        m = re.match(r"[^.\[\]]+", path[pos:])
        if not m:
            raise PathSyntaxError(
                f"路径语法非法：'{path}' 在位置 {pos} 处无法解析。"
            )
        key = m.group(0)
        if not expect_key and tokens:
            last_kind = tokens[-1][0]
            if last_kind == "key":
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 中相邻键 '{tokens[-1][1]}{key}' 缺少点号分隔。"
                )
        tokens.append(("key", key))
        pos += len(key)
        expect_key = False
    if not tokens:
        raise PathSyntaxError(f"路径语法非法：'{path}' 没有有效段。")
    return tokens


def _tokens_to_str(tokens: list[tuple[str, Any]]) -> str:
    out = ""
    for kind, key in tokens:
        if kind == "key":
            part = str(key)
        elif kind == "index":
            part = f"[{key}]"
        else:
            mk, mv = key
            part = f"[{mk}={mv}]"
        if part.startswith("[") or out == "":
            out += part
        else:
            out += part if part.startswith("[") else "." + part
    return out


def _descend(cur: Any, kind: str, key: Any, prefix: str) -> Any:
    if kind == "key":
        if not isinstance(cur, dict):
            raise PathNotFoundError(
                f"路径不存在：'{prefix}' 中 '{key}' 要求对象，但当前节点不是对象。"
            )
        if key not in cur:
            existing = list(cur.keys())
            raise PathNotFoundError(
                f"路径不存在：'{prefix}' 中 '{key}' 键不存在。现有键：{existing}"
            )
        return cur[key]
    if kind == "index":
        if not isinstance(cur, list):
            raise PathNotFoundError(
                f"路径不存在：'{prefix}' 要求数组，但当前节点不是数组。"
            )
        length = len(cur)
        actual = key if key >= 0 else length + key
        if actual < 0 or actual >= length:
            raise PathNotFoundError(
                f"路径不存在：'{prefix}' 越界，该数组当前长度 {length}"
                f"（有效下标 0..{length - 1} 或用 [-1] 取末元素）。"
            )
        return cur[actual]
    if not isinstance(cur, list):
        raise PathNotFoundError(
            f"路径不存在：'{prefix}' 要求数组，但当前节点不是数组。"
        )
    mk, mv = key
    matches = [item for item in cur if isinstance(item, dict) and item.get(mk) == mv]
    if len(matches) == 0:
        existing_vals = [item.get(mk) for item in cur if isinstance(item, dict)]
        raise PathNotFoundError(
            f"路径不存在：{prefix} 无匹配。现有 {mk} 值：{existing_vals}"
        )
    if len(matches) > 1:
        parent_path = prefix.rsplit("[", 1)[0]
        if not parent_path:
            parent_path = prefix
        raise MultipleMatchError(
            f"路径匹配到多个节点：{prefix} 命中 {len(matches)} 条，"
            f"请改用下标精确定位（如 {parent_path}[0]/{parent_path}[1]）。"
        )
    return matches[0]


def _resolve_node(doc: Any, tokens: list[tuple[str, Any]]) -> tuple[Any, str, str, Any]:
    cur = doc
    prefix = ""
    for i, (kind, key) in enumerate(tokens):
        if prefix == "":
            if kind == "key":
                prefix = str(key)
            elif kind == "index":
                prefix = f"[{key}]"
            else:
                mk, mv = key
                prefix = f"[{mk}={mv}]"
        else:
            if kind == "key":
                prefix = prefix + "." + str(key)
            elif kind == "index":
                prefix = prefix + f"[{key}]"
            else:
                mk, mv = key
                prefix = prefix + f"[{mk}={mv}]"
        is_last = i == len(tokens) - 1
        if not is_last:
            cur = _descend(cur, kind, key, prefix)
    last_kind, last_key = tokens[-1]
    return cur, prefix, last_kind, last_key


def set_by_path(doc: Any, path: str, value: Any) -> Any:
    new_doc = copy.deepcopy(doc)
    tokens = _tokenize(path)
    parent, full_prefix, last_kind, last_key = _resolve_node(new_doc, tokens)

    if last_kind == "key":
        if not isinstance(parent, dict):
            raise PathNotFoundError(
                f"路径不存在：'{path}' 的目标节点不是对象，无法设置键 '{last_key}'。"
            )
        if last_key not in parent:
            existing = list(parent.keys())
            raise PathNotFoundError(
                f"路径不存在：'{path}' 中 '{last_key}' 键不存在。现有键：{existing}"
            )
        parent[last_key] = value
    elif last_kind == "index":
        if not isinstance(parent, list):
            raise PathNotFoundError(
                f"路径不存在：'{path}' 的目标节点不是数组。"
            )
        length = len(parent)
        actual = last_key if last_key >= 0 else length + last_key
        if actual < 0 or actual >= length:
            raise PathNotFoundError(
                f"路径不存在：'{path}' 越界，该数组当前长度 {length}"
                f"（有效下标 0..{length - 1} 或用 [-1] 取末元素）。"
            )
        parent[actual] = value
    else:
        mk, mv = last_key
        matches = [item for item in parent if isinstance(item, dict) and item.get(mk) == mv]
        if len(matches) == 0:
            existing_vals = [item.get(mk) for item in parent if isinstance(item, dict)]
            raise PathNotFoundError(
                f"路径不存在：{full_prefix} 无匹配。现有 {mk} 值：{existing_vals}"
            )
        if len(matches) > 1:
            parent_path = full_prefix.rsplit("[", 1)[0]
            if not parent_path:
                parent_path = full_prefix
            raise MultipleMatchError(
                f"路径匹配到多个节点：{full_prefix} 命中 {len(matches)} 条，"
                f"请改用下标精确定位（如 {parent_path}[0]/{parent_path}[1]）。"
            )
        idx = parent.index(matches[0])
        parent[idx] = value
    return new_doc
