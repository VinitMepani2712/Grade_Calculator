# Grade Calculator Streamlit App

A simple, interactive Streamlit application to calculate weighted grades from a CSV file. Supports both "long" and "wide" CSV formats, adjustable category weights, and separate handling of extra credit.

---

## Features

- 📤 **CSV Upload**: Upload either:
  - **Long form**: rows with `Name`, `Category`, `raw`, `maximum` columns.
  - **Wide form**: one row per student with `<Category>_raw` and `<Category>_maximum` columns.
- ⚖️ **Adjustable Weights**: Set per-category weights via sidebar controls.
- 📊 **Automatic Totals**: Computes core total, extra credit, and overall percentage.
- 🔍 **Per-Student Breakdown**: Expandable detail tables showing raw scores, maximums, weights, and points earned.

---

## Prerequisites

- Python 3.7 or higher
- [Streamlit](https://streamlit.io/) library

---

## Installation

1. **Clone this repository** (or download the files):
   ```bash
   git clone <your-repo-url>
   cd grade-calculator
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install streamlit pandas
   ```

---

## Usage

1. **Run the app**:
   ```bash
   streamlit run app.py
   ```

2. **Open** the URL shown in your terminal (usually `http://localhost:8501`).

3. **Upload** your grades CSV:
   - For **long** format, ensure columns: `Name, Category, raw, maximum`.  
   - For **wide** format, ensure at least one `<Category>_raw` and matching `<Category>_maximum` column.

4. **Adjust weights** in the sidebar as needed.

5. **View** the summary table and expand student details for a full breakdown.

---

## CSV Formats

### Long Form

| Name  | Category        | raw    | maximum |
|-------|-----------------|--------|---------|
| Vinit | HW First Half   | 742    | 800     |
| Vinit | Quiz First Half | 54.45  | 75      |
| ...   | ...             | ...    | ...     |

### Wide Form

| Name  | HW First Half_raw | HW First Half_maximum | Quiz First Half_raw | ... |
|-------|-------------------|-----------------------|---------------------|-----|
| Vinit | 742               | 800                   | 54.45               | ... |

---

## Project Structure

```
grade-calculator/
├── app.py         # Main Streamlit application
├── README.md      # This file
├── requirements.txt   # (optional) pinned dependencies
└── examples/
    ├── long_grades.csv
    └── wide_grades.csv
```

---

## Customization

- To add or remove categories, update the `default_weights` dictionary in `app.py` and restart the app.
- To change layout or styling, modify the Streamlit commands in `app.py`.

---

## License

MIT © Your Name
