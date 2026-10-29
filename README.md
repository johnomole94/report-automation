# Automated Business Report Generator

A small Python project that turns a CSV of monthly revenue and expenses into a finished, professionally formatted LaTeX report (PDF).

## What it does
1. Reads `data/monthly_data.csv` (columns: `Month, Revenue, Expenses`)
2. Calculates monthly profit and margin, plus yearly totals and revenue growth
3. Checks its own arithmetic (total profit must equal revenue minus expenses)
4. Draws a chart with matplotlib
5. Writes the findings automatically (best month, revenue dips, expense warnings)
6. Fills `template/report_template.tex` and writes `output/report.tex`
7. Compiles `output/report.pdf` if LaTeX is installed

Change the CSV, run the script again, and you get a new report with no manual typing.

## How to run
```
pip install matplotlib
python generate_report.py                 # uses data/monthly_data.csv
python generate_report.py data/mine.csv   # uses your own file
```
No LaTeX installed? Upload `output/report.tex` and `output/chart.png` to Overleaf and compile there.

## Project layout
```
generate_report.py        main script
data/monthly_data.csv     sample (fictional) data
template/report_template.tex   LaTeX layout with <<PLACEHOLDERS>>
output/                   generated chart, .tex and PDF
```

## Why I built it
My earlier hand-typed report had totals that did not match its monthly rows. Automating the calculation removed that error and made the report repeatable.

## Next steps
- Add an AI step that drafts the written findings from the numbers
- Read data from Google Sheets instead of a CSV
- Email the finished PDF automatically
