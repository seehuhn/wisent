#! /usr/bin/env python3

import getpass
from imaplib import IMAP4_SSL
import re

M = IMAP4_SSL("vseehuhn.vpn.seehuhn.de")
M.login(getpass.getuser(), getpass.getpass())
M.select('INBOX', True)
typ, data = M.search(None, 'ALL')
for num in data[0].split():
    typ, data = M.fetch(num, '(RFC822.HEADER)')
    assert typ == "OK"

    headers = data[0][1]
    headers = re.sub(r'\r\n([\t ])', r'\1', headers)
    for l in headers.splitlines():
        if not l.strip():
            continue
        try:
            key, val = l.split(":", 1)
        except:
            continue
        key = key.strip()
        val = val.strip()
        if key.lower() in [ "reply-to", "from", "sender", "resent-reply-to",
                            "resent-from", "resent-sender", "to", "cc", "bcc",
                            "resent-to", "resent-cc", "resent-bcc" ]:
            print(val)
M.close()
M.logout()
