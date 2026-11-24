#!/usr/bin/env python3
"""Sanity-check generated KiCad files without KiCad: bracket balance, duplicate uuids,
and a few structural counts. Usage: python3 tools/check_sch.py out/*/*.kicad_sch out/*/*.kicad_sym"""
import re
import sys
import glob


def check(path):
    text = open(path, encoding='utf-8').read()
    depth = 0
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                return 'NEGATIVE depth (%s)' % path
    uu = re.findall(r'\(uuid "([^"]+)"\)', text)
    fields = [path.split('/')[-1], 'depth=%d' % depth,
              'sym=%d' % text.count('(symbol (lib_id'),
              'wire=%d' % text.count('(wire '),
              'label=%d' % text.count('(label '),
              'pins=%d' % text.count('(pin "'),
              'uuid=%d/%d' % (len(uu), len(set(uu)))]
    return '  '.join(fields)


def main(patterns):
    files = []
    for p in patterns:
        files += glob.glob(p)
    bad = 0
    for f in sorted(files):
        r = check(f)
        print('%-46s %s' % (f, r))
        if r.startswith('NEGATIVE'):
            bad += 1
    print('\n%d file(s) checked, %d with bracket errors' % (len(files), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] or ['out/*/*.kicad_sch', 'out/*/*.kicad_sym']))
