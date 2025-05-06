# Grade Calculator Streamlit App

A simple, interactive Streamlit application to calculate weighted grades from a CSV file. Supports both "long" and "wide" CSV formats, adjustable category weights, and user‑entered category maximums.

---

## Features

- 📤 **CSV Upload**: Upload either:
  - **Long form**: rows with `Name`, `Category`, and `raw` score columns (maximums are set in the sidebar).
  - **Wide form**: one row per student with `<Category>_raw` columns (maximums set in the sidebar).
- ⚖️ **Adjustable Weights**: Set per‑category weights via sidebar controls.
- 📊 **Automatic Totals**: Computes core total, extra credit, and overall percentage based on user‑provided maximums.
- 🔍 **Per‑Student Breakdown**: Expandable detail tables showing raw scores, weights, and points earned.

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
   - For **long** format, ensure columns: `Name, Category, raw`.  
   - For **wide** format, ensure `<Category>_raw` columns for each category.

4. **Adjust weights** and **enter total points** for each category in the sidebar.

5. **View** the summary table and expand student details for a full breakdown.

---

## CSV Formats

### Long Form

Rows with the following columns:

| Name  | Category | raw |
|-------|----------|-----|
| Alice | HW1      | 85  |
| Alice | Quiz1    | 18  |
| Bob   | Midterm  | 79  |

**Example CSV:**
```csv
Name,Category,raw
Alice,HW1,85
Alice,Quiz1,18
Bob,Midterm,79
```

### Wide Form

One row per student with `<Category>_raw` columns:

| Name  | HW1_raw | Quiz1_raw | Midterm_raw |
|-------|---------|-----------|-------------|
| Alice | 85      | 18        | 88          |
| Bob   | 92      | 16        | 79          |

**Example CSV:**
```csv
Name,HW1_raw,Quiz1_raw,Midterm_raw
Alice,85,18,88
Bob,92,16,79
```

---

## Category Maximums

After uploading your CSV, use the **Category Maximums** section in the sidebar to enter the total possible points for each category.

---

## License

MIT © Your Name
