#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate zh_CN.ini against the official en.ini.

Checks:
  * identical key sets
  * placeholder compatibility
  * escape sequences (\\n \\t \\s \\")
  * alert separators (<< >> == -- ||)
  * mnemonic handling (a lone & is removed in Chinese; && kept)

Usage: python3 tools/validate.py i18n/en.ini i18n/zh_CN.ini
"""
import re
import sys

POS_RE = re.compile(r"\{(\d*)\}")
NAMED_RE = re.compile(r"\{[^{}0-9][^{}]*\}")


def parse(path):
    sections, cur = [], None
    for line in open(path, encoding="utf-8"):
        s = line.rstrip("\n")
        t = s.strip()
        if not t or t.startswith("#"):
            continue
        m = re.match(r"^\[(.+)\]$", t)
        if m:
            cur = {"name": m.group(1), "pairs": []}
            sections.append(cur)
        elif "=" in s and cur is not None:
            k, v = s.split("=", 1)
            cur["pairs"].append((k.strip(), v.strip()))
    return sections


def flat(sections):
    return {f"{s['name']}.{k}": v for s in sections for k, v in s["pairs"]}


def counts(s):
    return (
        s.count("\\n"), s.count("\\t"), s.count("\\s"), s.count('\\"'),
        s.count("<<"), s.count(">>"), s.count("=="), s.count("--"), s.count("||"),
    )


def main():
    en = flat(parse(sys.argv[1]))
    zh = flat(parse(sys.argv[2]))
    fails = []

    missing = sorted(set(en) - set(zh))
    extra = sorted(set(zh) - set(en))
    fails += [f"missing: {k}" for k in missing]
    fails += [f"extra: {k}" for k in extra]

    for k in en:
        if k not in zh:
            continue
        a, b = en[k], zh[k]
        if POS_RE.findall(a) != POS_RE.findall(b):
            fails.append(f"positional placeholder mismatch: {k}")
        if sorted(NAMED_RE.findall(a)) != sorted(NAMED_RE.findall(b)):
            fails.append(f"named placeholder mismatch: {k}")
        if counts(a) != counts(b):
            fails.append(f"escape/separator count mismatch: {k}")
        if "&" in b:
            if a.count("&&") != b.count("&&"):
                fails.append(f"'&&' count mismatch: {k}")
            if "&" in b.replace("&&", ""):
                fails.append(f"single '&' left in translation: {k}")

    print(f"en: {len(en)} strings, zh: {len(zh)} strings")
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails[:200]:
            print(" -", f)
        return 1
    print("OK: 所有键、占位符、转义与分隔符均一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
