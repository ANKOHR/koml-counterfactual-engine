# Local build evidence

Acceptance checked on 2026-10-01 with Python 3.12.10 on Windows, CPU only.
30 pytest cases passed. The installed kce.exe completed fixture generation,
200-record run and Markdown report in 0.612 seconds (under 5 seconds).
The report was rendered to demo/report.md, an ignored local artifact.

All eight totals match the independent expectations exactly; all 100 planted
hypothetical cheaper IDs match, with zero false positives. A cost mutation
changes the result, proving computation. Empty input, malformed JSON, duplicate
IDs, future dates, negative/noninteger values, unsupported formats, Unicode,
long strings, atomic write failure and byte-identical reports were checked.

This is synthetic acceptance evidence. No measured operator savings, real-data
accuracy, adoption or commercial value is claimed. Real-use verdict is pending.
