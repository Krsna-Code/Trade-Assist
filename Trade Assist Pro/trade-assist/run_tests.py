"""
Trade Assist Pro — Test Runner & HTML Report Generator
Usage:  python run_tests.py
Output: test_reports/report_<timestamp>.html
"""

import os
import sys
import time
import traceback
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM RESULT COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class TimedResult(unittest.TestResult):

    STATUS_PASS  = "PASS"
    STATUS_FAIL  = "FAIL"
    STATUS_ERROR = "ERROR"
    STATUS_SKIP  = "SKIP"

    def __init__(self):
        super().__init__()
        self.results     = []
        self._timings    = {}
        self._suite_t0   = time.perf_counter()

    def startTest(self, test):
        super().startTest(test)
        self._timings[id(test)] = time.perf_counter()

    def _elapsed(self, test):
        return round(time.perf_counter() - self._timings.get(id(test), 0), 4)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results.append(self._entry(test, self.STATUS_PASS))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append(self._entry(test, self.STATUS_FAIL, err))

    def addError(self, test, err):
        super().addError(test, err)
        self.results.append(self._entry(test, self.STATUS_ERROR, err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        e = self._entry(test, self.STATUS_SKIP)
        e["message"] = reason
        self.results.append(e)

    def _entry(self, test, status, err=None):
        short = getattr(test, "_testMethodDoc", None) or test._testMethodName
        entry = {
            "class":    test.__class__.__name__,
            "method":   test._testMethodName,
            "short":    short,
            "status":   status,
            "duration": self._elapsed(test),
            "message":  "",
            "trace":    "",
        }
        if err:
            entry["message"] = traceback.format_exception_only(*err[:2])[-1].strip()
            entry["trace"]   = "".join(traceback.format_exception(*err)).strip()
        return entry

    @property
    def total_duration(self):
        return round(time.perf_counter() - self._suite_t0, 2)

    def summary(self):
        passed  = sum(1 for r in self.results if r["status"] == self.STATUS_PASS)
        failed  = sum(1 for r in self.results if r["status"] == self.STATUS_FAIL)
        errors  = sum(1 for r in self.results if r["status"] == self.STATUS_ERROR)
        skipped = sum(1 for r in self.results if r["status"] == self.STATUS_SKIP)
        total   = len(self.results)
        return dict(passed=passed, failed=failed, errors=errors,
                    skipped=skipped, total=total)

    def by_module(self):
        modules = {}
        for r in self.results:
            cls = r["class"]
            modules.setdefault(cls, []).append(r)
        return modules


# ═══════════════════════════════════════════════════════════════════════════════
# HTML REPORT
# ═══════════════════════════════════════════════════════════════════════════════

_CSS = """
:root{--pass:#22c55e;--fail:#ef4444;--error:#f97316;--skip:#94a3b8;
      --bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;
      --muted:#94a3b8;--accent:#38bdf8;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);
     color:var(--text);padding:2rem;line-height:1.5;}
h1{font-size:1.8rem;font-weight:700;color:var(--accent);}
h2{font-size:1.1rem;font-weight:600;color:var(--muted);margin-bottom:1rem;}
.meta{color:var(--muted);font-size:.85rem;margin:.3rem 0 1.5rem;}
.summary{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem;}
.card{background:var(--card);border:1px solid var(--border);border-radius:.5rem;
      padding:1rem 1.5rem;min-width:120px;text-align:center;}
.card .num{font-size:2rem;font-weight:700;}
.card .lbl{font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;}
.card.pass .num{color:var(--pass);}
.card.fail .num{color:var(--fail);}
.card.error .num{color:var(--error);}
.card.skip .num{color:var(--skip);}
.card.total .num{color:var(--accent);}
.rate-bar{background:var(--card);border:1px solid var(--border);border-radius:.5rem;
          padding:1rem 1.5rem;margin-bottom:2rem;}
.rate-bar .label{font-size:.85rem;color:var(--muted);margin-bottom:.5rem;}
.bar-track{background:var(--border);border-radius:1rem;height:12px;overflow:hidden;}
.bar-fill{height:100%;border-radius:1rem;transition:width .4s;}
.section{background:var(--card);border:1px solid var(--border);border-radius:.5rem;
         margin-bottom:2rem;overflow:hidden;}
.section-header{padding:.75rem 1rem;background:#162032;
                font-size:.9rem;font-weight:600;border-bottom:1px solid var(--border);}
table{width:100%;border-collapse:collapse;font-size:.875rem;}
th{text-align:left;padding:.5rem 1rem;color:var(--muted);
   font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;
   background:#162032;border-bottom:1px solid var(--border);}
td{padding:.5rem 1rem;border-bottom:1px solid var(--border);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:rgba(56,189,248,.04);}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:.25rem;
       font-size:.75rem;font-weight:600;letter-spacing:.03em;}
.badge.PASS {background:rgba(34,197,94,.15); color:var(--pass);}
.badge.FAIL {background:rgba(239,68,68,.15);  color:var(--fail);}
.badge.ERROR{background:rgba(249,115,22,.15); color:var(--error);}
.badge.SKIP {background:rgba(148,163,184,.15);color:var(--skip);}
.mod-ok  td:first-child{border-left:3px solid var(--pass);}
.mod-bad td:first-child{border-left:3px solid var(--fail);}
details{border-top:1px solid var(--border);}
details summary{padding:.5rem 1rem;cursor:pointer;font-size:.85rem;
                color:var(--muted);list-style:none;display:flex;align-items:center;gap:.5rem;}
details summary:hover{background:rgba(255,255,255,.03);}
details[open] summary{color:var(--text);}
.trace{background:#080f1a;padding:1rem;font-family:'Courier New',monospace;
       font-size:.78rem;white-space:pre-wrap;word-break:break-all;
       color:#fca5a5;margin:.5rem 1rem 1rem;border-radius:.4rem;
       border:1px solid rgba(239,68,68,.2);}
.dur{color:var(--muted);font-size:.8rem;}
"""

_JS = """
function toggleAll(show){
  document.querySelectorAll('details').forEach(d=>d.open=show);
}
"""

def _badge(status):
    icons = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIP": "⏭️"}
    return f'<span class="badge {status}">{icons.get(status,"")} {status}</span>'


def _module_row(cls_name, tests):
    total   = len(tests)
    passed  = sum(1 for t in tests if t["status"] == "PASS")
    failed  = sum(1 for t in tests if t["status"] in ("FAIL", "ERROR"))
    skipped = sum(1 for t in tests if t["status"] == "SKIP")
    ok      = failed == 0
    row_cls = "mod-ok" if ok else "mod-bad"
    icon    = "✅" if ok else "❌"
    dur     = round(sum(t["duration"] for t in tests), 3)
    return (
        f'<tr class="{row_cls}">'
        f'<td>{icon} <strong>{cls_name}</strong></td>'
        f'<td>{total}</td>'
        f'<td style="color:var(--pass)">{passed}</td>'
        f'<td style="color:var(--fail)">{failed}</td>'
        f'<td style="color:var(--skip)">{skipped}</td>'
        f'<td class="dur">{dur}s</td>'
        f'</tr>'
    )


def _test_row(r):
    trace_html = ""
    if r["trace"]:
        trace_html = (
            f'<details><summary>▶ Show traceback</summary>'
            f'<div class="trace">{r["trace"]}</div></details>'
        )
    msg = f'<div style="color:var(--muted);font-size:.8rem;margin-top:.25rem">{r["message"]}</div>' \
          if r["message"] else ""
    return (
        f'<tr>'
        f'<td>{r["method"]}{msg}{trace_html}</td>'
        f'<td>{_badge(r["status"])}</td>'
        f'<td class="dur">{r["duration"]}s</td>'
        f'</tr>'
    )


def generate_html(result: TimedResult, output_path: str):
    s     = result.summary()
    total = s["total"]
    rate  = round(s["passed"] / total * 100, 1) if total else 0
    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    dur   = result.total_duration

    bar_color = (
        "var(--pass)"  if rate >= 90 else
        "var(--error)" if rate >= 70 else
        "var(--fail)"
    )

    overall_icon = "✅ ALL PASSED" if s["failed"] == 0 and s["errors"] == 0 \
                   else "❌ SOME FAILURES"

    # --- summary cards ---
    cards = "".join([
        f'<div class="card total"><div class="num">{total}</div><div class="lbl">Total</div></div>',
        f'<div class="card pass"><div class="num">{s["passed"]}</div><div class="lbl">Passed</div></div>',
        f'<div class="card fail"><div class="num">{s["failed"]}</div><div class="lbl">Failed</div></div>',
        f'<div class="card error"><div class="num">{s["errors"]}</div><div class="lbl">Errors</div></div>',
        f'<div class="card skip"><div class="num">{s["skipped"]}</div><div class="lbl">Skipped</div></div>',
    ])

    # --- module breakdown ---
    mod_rows = "".join(
        _module_row(cls, tests)
        for cls, tests in sorted(result.by_module().items())
    )
    module_table = f"""
    <div class="section">
      <div class="section-header">📦 Module Breakdown</div>
      <table>
        <thead><tr><th>Module</th><th>Total</th><th>Passed</th>
        <th>Failed/Error</th><th>Skipped</th><th>Duration</th></tr></thead>
        <tbody>{mod_rows}</tbody>
      </table>
    </div>"""

    # --- detailed results per module ---
    detail_sections = []
    for cls, tests in sorted(result.by_module().items()):
        rows = "".join(_test_row(r) for r in tests)
        n_fail = sum(1 for t in tests if t["status"] in ("FAIL","ERROR"))
        cls_icon = "❌" if n_fail else "✅"
        detail_sections.append(f"""
        <div class="section">
          <div class="section-header">{cls_icon} {cls}
            <span style="float:right;font-weight:400;color:var(--muted)">
              {len(tests)} tests
            </span>
          </div>
          <table>
            <thead><tr><th>Test</th><th>Status</th><th>Duration</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""")

    details_html = "\n".join(detail_sections)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trade Assist Pro — Test Report</title>
<style>{_CSS}</style>
</head>
<body>
<h1>🛢️ Trade Assist Pro — Test Report</h1>
<div class="meta">
  Generated: {ts} &nbsp;|&nbsp; Duration: {dur}s &nbsp;|&nbsp;
  <strong style="color:{'var(--pass)' if rate>=90 else 'var(--fail)'}">{overall_icon}</strong>
</div>

<div class="summary">{cards}</div>

<div class="rate-bar">
  <div class="label">Pass Rate: <strong>{rate}%</strong>
    &nbsp;({s['passed']} of {total} tests)
    <span style="float:right">
      <button onclick="toggleAll(true)"
        style="background:var(--card);color:var(--muted);border:1px solid var(--border);
               padding:.2rem .6rem;border-radius:.3rem;cursor:pointer;font-size:.8rem;
               margin-right:.5rem">Expand all</button>
      <button onclick="toggleAll(false)"
        style="background:var(--card);color:var(--muted);border:1px solid var(--border);
               padding:.2rem .6rem;border-radius:.3rem;cursor:pointer;font-size:.8rem">
        Collapse all</button>
    </span>
  </div>
  <div class="bar-track">
    <div class="bar-fill" style="width:{rate}%;background:{bar_color}"></div>
  </div>
</div>

{module_table}

<h2 style="margin-top:2rem;margin-bottom:1rem">🔬 Detailed Results</h2>
{details_html}

<script>{_JS}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromName("tests.test_suite")

    result = TimedResult()

    print("\n" + "═" * 60)
    print("  🛢️  TRADE ASSIST PRO — TEST SUITE")
    print("═" * 60)

    for test in unittest.TestSuite.__iter__(suite):
        if not isinstance(test, unittest.TestCase):
            continue
        name = f"{test.__class__.__name__}.{test._testMethodName}"
        sys.stdout.write(f"  {name:<60}")
        sys.stdout.flush()

        t0 = time.perf_counter()
        test(result)
        elapsed = round(time.perf_counter() - t0, 3)

        last = result.results[-1] if result.results else None
        if last:
            icons = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIP": "⏭️"}
            icon  = icons.get(last["status"], "?")
            print(f" {icon}  ({elapsed}s)")
        else:
            print()

    s   = result.summary()
    dur = result.total_duration

    print("\n" + "─" * 60)
    print(f"  Total:   {s['total']}")
    print(f"  ✅ Pass:  {s['passed']}")
    print(f"  ❌ Fail:  {s['failed']}")
    print(f"  💥 Error: {s['errors']}")
    print(f"  ⏭️  Skip:  {s['skipped']}")
    rate = round(s["passed"] / s["total"] * 100, 1) if s["total"] else 0
    print(f"  Rate:    {rate}%")
    print(f"  Time:    {dur}s")
    print("─" * 60)

    ts          = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(ROOT, "test_reports", f"report_{ts}.html")
    generate_html(result, report_path)

    print(f"\n  📄 HTML report → {report_path}")
    print("═" * 60 + "\n")

    return 0 if (s["failed"] == 0 and s["errors"] == 0) else 1


if __name__ == "__main__":
    sys.exit(run())
