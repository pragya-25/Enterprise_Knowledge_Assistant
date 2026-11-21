"""
Create FICTIONAL confidential documents so access control can be demonstrated.
All names, numbers and findings below are invented.

    python -m scripts.make_synthetic_docs
    python -m scripts.ingest          # re-run ingestion afterwards
"""
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

NOTE = "> SYNTHETIC DATA: fictional content created for a demo. Not a real company document.\n\n"

DOCS = {
"finance/synthetic__salary-bands-2026.md": '''---
title: "Salary Bands 2026 (Confidential)"
---
''' + NOTE + '''# Salary Bands 2026

## Purpose and access
These salary bands are confidential and visible only to the Finance team and administrators. They are used for offer approvals and the annual compensation review. Do not share band ranges with employees or candidates.

## Engineering bands (annual base, USD)
- Software Engineer L3: 78,000 to 102,000
- Software Engineer L4: 98,000 to 128,000
- Senior Software Engineer L5: 124,000 to 162,000
- Staff Engineer L6: 155,000 to 205,000
- Engineering Manager M1: 150,000 to 198,000

## Sales bands (annual base, USD)
- Account Executive: 70,000 to 95,000 base with a 50/50 base-to-variable split
- Senior Account Executive: 92,000 to 120,000 base with a 50/50 split
- Sales Director: 140,000 to 185,000 base with a 60/40 split

## Exceptions
Offers above the band maximum need written approval from the CFO. In 2026 a total of nine exceptions were approved, all in machine learning engineering roles.
''',

"finance/synthetic__q3-budget-2026.md": '''---
title: "Q3 Budget Review 2026 (Confidential)"
---
''' + NOTE + '''# Q3 Budget Review 2026

## Summary
Total operating expenses for the quarter were 4.2 million USD against a plan of 4.0 million USD. The overrun is mostly caused by cloud infrastructure spend.

## Spend by department
- Engineering: 1.8 million USD
- Sales and Marketing: 1.1 million USD
- Cloud infrastructure: 620 thousand USD, which is 14 percent over plan
- General and Administrative: 480 thousand USD
- Contingency reserve: 200 thousand USD

## Decisions
A hiring freeze applies to all non-engineering roles until January 2027. Finance will renegotiate the cloud contract in Q4 to bring monthly spend back to plan.
''',

"hr/synthetic__performance-improvement-plans.md": '''---
title: "Performance Improvement Plans: Active Case Summary (Confidential)"
---
''' + NOTE + '''# Performance Improvement Plans

## Process
A performance improvement plan lasts 60 days. The manager and an HR partner hold check-ins every two weeks. HR must approve the plan before it is shared with the employee.

## Q3 2026 summary (no individual names)
- Seven plans were active during the quarter
- Three were completed successfully and the employees returned to normal status
- Two ended in separation
- Two are still in progress

## Access
This summary is visible to HR and administrators only. Managers receive guidance for their own team members through their HR partner.
''',

"hr/synthetic__restructuring-draft-2027.md": '''---
title: "Restructuring Proposal Draft 2027 (Strictly Confidential)"
---
''' + NOTE + '''# Restructuring Proposal Draft 2027

## Proposal
Leadership is evaluating the consolidation of two customer support teams. The draft plan would reduce twelve roles by the end of Q1 2027. No decision has been made and no announcement date is set.

## Severance draft
The draft severance package is eight weeks of base pay plus two additional weeks for each full year of service. Health coverage would continue for three months.

## Confidentiality
Only HR leadership and administrators may see this draft. Discussing it outside the working group is a policy violation and may lead to disciplinary action.
''',

"security/synthetic__open-vulnerabilities-q3-report.md": '''---
title: "Open Vulnerabilities Report Q3 2026 (Confidential)"
---
''' + NOTE + '''# Open Vulnerabilities Report Q3 2026

## Summary
The internal scan at the end of Q3 found 4 critical, 19 high and 63 medium open findings across production services. Counts are taken from the vulnerability tracker on the last day of the quarter and exclude findings already marked as fixed.

## Overdue critical finding
Finding INT-2026-014 is the oldest critical issue. It affects the payment webhook service and has been open for 41 days, which breaches the 30 day SLA. The remediation owner is the Platform Security team.

## Next steps
An external penetration test is scheduled for December 2026. Details of unpatched findings must not be shared outside the security team and engineering leads.
''',
}


def main():
    for rel, text in DOCS.items():
        path = RAW / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print("created", rel)
    print("\nNow re-run:  python -m scripts.ingest")


if __name__ == "__main__":
    main()
