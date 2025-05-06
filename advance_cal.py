import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Grade Calculator",
    layout="wide",
)

st.title("🎓 Grade Calculator")
st.markdown("Upload either a **long** or **wide** CSV;")
st.markdown("tweak weights & maximums in the sidebar;")
st.markdown("see per-student breakdowns.")

# --- Upload & read ---
uploaded = st.file_uploader("Upload grades CSV", type="csv")
if not uploaded:
    st.info("Awaiting CSV upload…")
    st.stop()

df = pd.read_csv(uploaded)

# --- Detect long vs wide ---
long_cols = {"Name", "Category", "raw"}  # no longer require 'maximum'
if long_cols.issubset(df.columns):
    mode = "long"
elif any(col.endswith("_raw") for col in df.columns):
    mode = "wide"
else:
    st.error(
        "CSV not recognized. Must be either:\n"
        "- **Long** form with columns `Name, Category, raw`, OR\n"
        "- **Wide** form with `<Category>_raw` (and optionally `<Category>_maximum`) columns."
    )
    st.stop()

# --- Column mapping ---
with st.sidebar.expander("🔧 Column mapping", expanded=False):
    if mode == "long":
        name_col = st.selectbox("Student name column", df.columns, index=df.columns.get_loc("Name"))
        cat_col  = st.selectbox("Category column",     df.columns, index=df.columns.get_loc("Category"))
        raw_col  = st.selectbox("Raw score column",    df.columns, index=df.columns.get_loc("raw"))
    else:
        name_col = st.selectbox(
            "Student name column",
            df.columns,
            index=(df.columns.get_loc("Name") if "Name" in df.columns else 0)
        )

# --- Build list of file categories ---
if mode == "long":
    file_cats = sorted(df[cat_col].dropna().unique())
else:
    file_cats = sorted(cat[:-4] for cat in df.columns if cat.endswith("_raw"))

# --- Custom categories ---
if "custom_cats" not in st.session_state:
    st.session_state["custom_cats"] = []
with st.sidebar.expander("➕ Add a custom category", expanded=False):
    new_cat = st.text_input("New category name", "")
    new_w   = st.number_input("Default weight", min_value=0.0, value=0.0, step=1.0)
    if st.button("Add category"):
        if new_cat and new_cat not in file_cats and new_cat not in st.session_state["custom_cats"]:
            st.session_state["custom_cats"].append(new_cat)
            st.success(f"Added “{new_cat}”")
        else:
            st.warning("Provide a unique, non-empty name.")

all_categories = file_cats + st.session_state["custom_cats"]

# --- Select active categories ---
active = st.sidebar.multiselect(
    "✅ Active categories",
    options=all_categories,
    default=all_categories
)

# --- Weights ---
st.sidebar.header("Category Weights")
weights = {
    cat: st.sidebar.number_input(
        f"{cat} weight",
        min_value=0.0,
        value=(0.0 if cat in file_cats else 40.0),
        step=1.0,
        key=f"w_{cat}"
    )
    for cat in active
}

# --- Maximums (new!) ---
st.sidebar.header("Category Maximums")
max_scores = {}
for cat in active:
    # only use CSV max in wide-mode if <cat>_maximum truly exists
    if mode == "wide" and f"{cat}_maximum" in df.columns:
        max_scores[cat] = None
        st.sidebar.write(f"{cat}: using CSV `<{cat}_maximum>`")
    else:
        max_scores[cat] = st.sidebar.number_input(
            f"{cat} total points",
            min_value=0.0,
            value=100.0,
            step=1.0,
            key=f"maxinp_{cat}"
        )

total_point = sum(w for c, w in weights.items() if c.lower() != "extra credit")

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

# --- Compute results ---
results = []

if mode == "long":
    # group by student
    for student, grp in df.groupby(name_col):
        point_achieved = ec_total = 0.0
        detail = []
        for _, row in grp.iterrows():
            cat = row[cat_col]
            if cat not in active:
                continue

            raw = row[raw_col]
            mx  = max_scores[cat]      # always from sidebar in long-mode
            w   = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)

            if cat.lower() == "extra credit":
                ec_total += pts
            else:
                point_achieved += pts

            detail.append({
                "Category":      cat,
                "Raw":           raw,
                "Max":           mx,
                "Weight":        w,
                "Points Earned": round(pts, 2)
            })

        overall_pct = (point_achieved / total_point * 100) if total_point else 0
        results.append({
            "Name":             student,
            "Point Achieved":   round(point_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%",
            "Details":          detail
        })

else:  # wide mode
    for _, row in df.iterrows():
        student = row[name_col]
        point_achieved = ec_total = 0.0
        detail = []
        for cat in active:
            raw_col_name = f"{cat}_raw"
            if raw_col_name not in df.columns:
                continue

            raw = row[raw_col_name]
            # CSV max if present and we set max_scores[cat] is None
            if f"{cat}_maximum" in df.columns:
                mx = row[f"{cat}_maximum"]
            else:
                mx = max_scores[cat]

            w   = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)

            if cat.lower() == "extra credit":
                ec_total += pts
            else:
                point_achieved += pts

            detail.append({
                "Category":      cat,
                "Raw":           raw,
                "Max":           mx,
                "Weight":        w,
                "Points Earned": round(pts, 2)
            })

        overall_pct = (point_achieved / total_point * 100) if total_point else 0
        results.append({
            "Name":             student,
            "Point Achieved":   round(point_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%",
            "Details":          detail
        })

# --- Search & reorder ---
search_term = st.text_input("🔍 Search student", "")
if search_term:
    search_lower = search_term.lower()
    results = sorted(results, key=lambda r: search_lower not in r["Name"].lower())

# --- Summary table ---
df_res  = pd.DataFrame(results)
summary = df_res.drop(columns=["Details"], errors="ignore")

st.subheader("📋 Summary")
if "Name" in summary.columns:
    summary = summary.set_index("Name")
st.dataframe(summary)

# --- Download all details ---
all_details = []
for r in results:
    for d in r["Details"]:
        d_copy = d.copy()
        d_copy["Name"] = r["Name"]
        all_details.append(d_copy)
df_all = pd.DataFrame(all_details)
csv_details = df_all.to_csv(index=False)
st.download_button(
    label="📥 Download ALL students details",
    data=csv_details,
    file_name="all_students_details.csv",
    mime="text/csv",
    key="download_all_details"
)

# --- Per-student breakdowns ---
for idx, row in enumerate(results):
    with st.expander(f"🔍 {row['Name']}'s Breakdown"):
        detail_df = pd.DataFrame(row["Details"])
        if not detail_df.empty:
            for col in ["Raw", "Max", "Weight", "Points Earned"]:
                detail_df[col] = detail_df[col].apply(lambda x: f"{float(x):.2f}")
            st.table(detail_df.set_index("Category"))
            csv = detail_df.to_csv(index=False)
            st.download_button(
                label="📥 Download this student's breakdown",
                data=csv,
                file_name=f"{row['Name'].replace(' ', '_')}_breakdown.csv",
                mime="text/csv",
                key=f"download_{idx}"
            )
        else:
            st.write("No detail rows to display.")
