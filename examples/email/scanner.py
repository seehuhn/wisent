#! /usr/bin/env python

def tokenize(s):
    """Tokenize the body of structured RFC 822 header fields."""
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        i += 1

        if c in [' ', '\t']:
            pass
        elif c == '(':
            nest = 1
            cc = ""
            while i < n and nest > 0:
                if s[i] == ')':
                    nest -= 1
                elif s[i] == '(':
                    nest += 1
                elif s[i] == '\\':
                    i += 1
                cc += s[i]
                i += 1
            yield ("comment", cc[:-1])
        elif c == '"':
            cc = ""
            while i < n:
                if s[i] == '"':
                    break
                elif s[i] == '\\':
                    i += 1
                cc += s[i]
                i += 1
            i += 1
            yield ('quoted-string', cc)
        elif c == '[':
            cc = ""
            while i < n:
                if s[i] == ']':
                    break
                elif s[i] == '\\':
                    i += 1
                cc += s[i]
                i += 1
            yield ('domain-literal', cc)
        elif c in ['<', '>', ',', ';', ':', '@', '.']:
            yield ('special', c)
        else:
            cc = c
            while i < n and s[i] not in [ ' ', '\t', '@', '<', '>', '[', '(', ',', ';', ':', '.', '"']:
                cc += s[i]
                i += 1
            yield ('atom', cc)
