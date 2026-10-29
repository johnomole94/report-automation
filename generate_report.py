"""
generate_report.py
------------------
Reads a CSV of monthly revenue and expenses, calculates profit and margin,
draws a chart, and writes a finished LaTeX report.

Usage:
    python generate_report.py                  # uses data/monthly_data.csv
    python generate_report.py data/other.csv   # uses a different CSV

CSV format (first row must be the header):
    Month,Revenue,Expenses
"""

import csv
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # lets matplotlib save images without opening a window
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
TEMPLATE_FILE = BASE_DIR / "template" / "report_template.tex"
OUTPUT_DIR = BASE_DIR / "output"


# ---------------------------------------------------------------- Step 1
def read_data(csv_path):
    """Read the CSV and return a list of rows (one dictionary per month)."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for line_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                rows.append({
                    "month": row["Month"].strip(),
                    "revenue": float(row["Revenue"]),
                    "expenses": float(row["Expenses"]),
                })
            except (KeyError, ValueError):
                sys.exit(f"Problem on line {line_number} of {csv_path}: "
                         "check the columns Month, Revenue, Expenses.")
    if not rows:
        sys.exit("The CSV file has no data rows.")
    return rows


# ---------------------------------------------------------------- Step 2
def calculate(rows):
    """Add profit and margin to every row, and compute the yearly totals."""
    for r in rows:
        r["profit"] = r["revenue"] - r["expenses"]            # P = R - E
        r["margin"] = r["profit"] / r["revenue"] * 100        # M = P / R * 100

    total_revenue = sum(r["revenue"] for r in rows)
    total_expenses = sum(r["expenses"] for r in rows)
    total_profit = sum(r["profit"] for r in rows)

    # Safety check: two different ways of getting total profit must agree.
    assert abs(total_profit - (total_revenue - total_expenses)) < 1e-6, \
        "Total profit does not match revenue minus expenses!"

    first, last = rows[0], rows[-1]
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "total_profit": total_profit,
        "avg_revenue": total_revenue / len(rows),
        "overall_margin": total_profit / total_revenue * 100,
        "growth": (last["revenue"] - first["revenue"]) / first["revenue"] * 100,
        "first_month": first["month"],
        "last_month": last["month"],
    }


# ---------------------------------------------------------------- Step 3
def make_chart(rows, path):
    """Draw revenue, expenses and profit and save the picture."""
    labels = [r["month"][:3] for r in rows]
    plt.figure(figsize=(9, 5))
    plt.plot(labels, [r["revenue"] for r in rows], marker="o", label="Revenue")
    plt.plot(labels, [r["expenses"] for r in rows], marker="o", label="Expenses")
    plt.plot(labels, [r["profit"] for r in rows], marker="o", label="Operating profit")
    plt.title("Monthly Revenue, Expenses and Operating Profit")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


# ---------------------------------------------------------------- Step 4
def money(x):
    """Format a number like 142,000."""
    return f"{x:,.0f}"


def make_table_rows(rows):
    """Build the LaTeX table rows, one line per month."""
    lines = []
    for r in rows:
        lines.append(f"{r['month']} & {money(r['revenue'])} & {money(r['expenses'])} "
                     f"& {money(r['profit'])} & {r['margin']:.1f}\\% \\\\")
    return "\n".join(lines)


def make_findings(rows, k):
    """Write the findings automatically from the numbers."""
    best = max(rows, key=lambda r: r["profit"])
    findings = [
        f"Revenue grew {k['growth']:.1f}\\% from {k['first_month']} to {k['last_month']}.",
        f"Total operating profit was {money(k['total_profit'])}, "
        f"an overall margin of {k['overall_margin']:.1f}\\%.",
        f"The most profitable month was {best['month']} "
        f"({money(best['profit'])}).",
    ]

    # Find any month where revenue fell compared with the month before.
    drops = [rows[i]["month"] for i in range(1, len(rows))
             if rows[i]["revenue"] < rows[i - 1]["revenue"]]
    if drops:
        findings.append("Revenue dipped compared with the previous month in: "
                        + ", ".join(drops) + ".")
    else:
        findings.append("Revenue rose in every month.")

    if any(r["expenses"] > r["revenue"] for r in rows):
        findings.append("Warning: at least one month had expenses above revenue.")
    else:
        findings.append("Expenses stayed below revenue in every month.")

    return "\n".join(f"\\item {text}" for text in findings)


# ---------------------------------------------------------------- Step 5
def fill_template(rows, k):
    """Put the numbers into the LaTeX template and return the finished text."""
    text = TEMPLATE_FILE.read_text(encoding="utf-8")
    values = {
        "DATE": date.today().strftime("%B %d, %Y"),
        "TABLE_ROWS": make_table_rows(rows),
        "TOTAL_REVENUE": money(k["total_revenue"]),
        "TOTAL_EXPENSES": money(k["total_expenses"]),
        "TOTAL_PROFIT": money(k["total_profit"]),
        "AVG_REVENUE": money(k["avg_revenue"]),
        "OVERALL_MARGIN": f"{k['overall_margin']:.1f}",
        "GROWTH": f"{k['growth']:.1f}",
        "FIRST_MONTH": k["first_month"],
        "LAST_MONTH": k["last_month"],
        "FINDINGS": make_findings(rows, k),
    }
    for name, value in values.items():
        text = text.replace(f"<<{name}>>", value)
    return text


# ---------------------------------------------------------------- Step 6
def compile_pdf(tex_path):
    """If LaTeX is installed, turn report.tex into report.pdf."""
    if shutil.which("pdflatex") is None:
        print("pdflatex not found - upload output/report.tex and output/chart.png "
              "to Overleaf to get the PDF.")
        return
    for _ in range(2):  # run twice so cross-references resolve
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_path.name],
            cwd=tex_path.parent, stdout=subprocess.DEVNULL, check=False,
        )
    print("Created", tex_path.with_suffix(".pdf"))


# ---------------------------------------------------------------- Main
def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "data" / "monthly_data.csv"
    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = read_data(csv_path)
    kpis = calculate(rows)
    make_chart(rows, OUTPUT_DIR / "chart.png")

    tex_path = OUTPUT_DIR / "report.tex"
    tex_path.write_text(fill_template(rows, kpis), encoding="utf-8")

    print(f"Read {len(rows)} months from {csv_path}")
    print(f"Total revenue : {money(kpis['total_revenue'])}")
    print(f"Total expenses: {money(kpis['total_expenses'])}")
    print(f"Total profit  : {money(kpis['total_profit'])}")
    print(f"Overall margin: {kpis['overall_margin']:.1f}%")
    compile_pdf(tex_path)


if __name__ == "__main__":
    main()
