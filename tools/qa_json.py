"""Lenient JSON extraction for the Claude-vision QA scripts.

Model replies occasionally contain an unescaped double quote inside a string value
(e.g. a "hook" shape) or a trailing comma. A strict json.loads then throws away a
paid vision call. lenient_loads() tries strict parsing first, then a conservative
repair: quotes inside strings that are not followed by a structural character are
escaped, raw newlines inside strings are escaped, and trailing commas are removed.
Run `python3 tools/qa_json.py` for the self-test.
"""
import json
import re


def repair_json(t: str) -> str:
    out, in_str, i, n = [], False, 0, len(t)
    while i < n:
        c = t[i]
        if in_str:
            if c == '\\':
                out.append(c)
                if i + 1 < n:
                    out.append(t[i + 1])
                i += 2
                continue
            if c == '"':
                j = i + 1
                while j < n and t[j] in ' \t\r\n':
                    j += 1
                closing = j >= n or t[j] in ':}]'
                if not closing and j < n and t[j] == ',':
                    # A comma after the quote only closes the string if what follows can start a key or value.
                    k = j + 1
                    while k < n and t[k] in ' \t\r\n':
                        k += 1
                    nxt = t[k:k + 5] if k < n else ''
                    closing = (not nxt or nxt[0] in '"{[-0123456789}]'
                               or nxt.startswith(('true', 'false', 'null')))
                if closing:
                    in_str = False
                    out.append(c)
                else:
                    out.append('\\"')
                i += 1
                continue
            if c == '\n':
                out.append('\\n'); i += 1; continue
            out.append(c); i += 1; continue
        if c == '"':
            in_str = True
        out.append(c); i += 1
    s = ''.join(out)
    return re.sub(r',\s*([}\]])', r'\1', s)


def extract_object(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    s, e = t.find("{"), t.rfind("}")
    if s < 0 or e < 0:
        raise ValueError(f"Could not locate JSON in response:\n{text[:800]}")
    return t[s:e + 1]


def lenient_loads(text: str) -> dict:
    body = extract_object(text)
    try:
        return json.loads(body)
    except json.JSONDecodeError as strict_error:
        try:
            return json.loads(repair_json(body))
        except json.JSONDecodeError:
            raise ValueError(f"Unparseable JSON even after repair ({strict_error}):\n{body[:1200]}") from strict_error


if __name__ == "__main__":
    samples = [
        '```json\n{"a": "it has a "hook" shape", "b": [1, 2,], "c": {"d": "x",}}\n```',
        '{"note": "reads as a stray "hook", with one prong visible, "x" marks", "status": "partial"}',
        'Here you go:\n{"summary": "line one\nline two", "verdict": "pass"} thanks',
        '{"note": "escaped \\"ok\\" here", "n": 3}',
    ]
    for s in samples:
        d = lenient_loads(s)
        assert isinstance(d, dict) and d, d
    assert lenient_loads(samples[0])["a"] == 'it has a "hook" shape'
    assert lenient_loads(samples[1])["note"] == 'reads as a stray "hook", with one prong visible, "x" marks'
    assert lenient_loads(samples[2])["summary"] == "line one\nline two"
    print("qa_json self-test ok")
