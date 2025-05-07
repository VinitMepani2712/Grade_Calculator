import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grade Calculator", layout="wide")
st.title("🎓 Grade Calculator")
st.markdown("Upload a CSV (long, wide, or raw-only). Blank/Unnamed columns are ignored.")

def _clear_df():
    st.session_state.pop("df", None)

uploaded = st.file_uploader(
    "Upload grades CSV",
    type="csv",
    key="uploaded_file",
    on_change=_clear_df
)

# — load or reuse the dataframe —
if "df" not in st.session_state:
    if not uploaded:
        st.info("Awaiting CSV upload…")
        st.stop()
    st.session_state.df = pd.read_csv(uploaded)
df = st.session_state.df

# — drop blank/unnamed columns —
df = df.loc[:, [c for c in df.columns if str(c).strip() and not str(c).startswith("Unnamed")]]

# — require a Name column —
if "Name" not in df.columns:
    st.error(" CSV must include a ‘Name’ column.")
    st.stop()

# — detect NetID column (case-insensitive) —
netid_col = next((c for c in df.columns if c.lower() == "netid"), None)

# — determine mode —
long_cols = {"Name", "Category", "raw"}
if long_cols.issubset(df.columns):
    mode = "long"
elif any(c.endswith("_raw") for c in df.columns):
    mode = "wide"
else:
    mode = "raw-only"

# — sidebar: column mapping for long vs wide/raw-only —
with st.sidebar.expander("🔧 Column mapping", expanded=False):
    if mode == "long":
        name_col = st.selectbox(
            "Student name column",
            df.columns,
            index=df.columns.get_loc("Name"),
            key="name_col"
        )
        cat_col = st.selectbox(
            "Category column",
            df.columns,
            index=df.columns.get_loc("Category"),
            key="cat_col"
        )
        raw_col = st.selectbox(
            "Raw score column",
            df.columns,
            index=df.columns.get_loc("raw"),
            key="raw_col"
        )
    else:
        name_col = st.selectbox(
            "Student name column",
            df.columns,
            index=df.columns.get_loc("Name") if "Name" in df.columns else 0,
            key="name_col"
        )

# — gather categories from file and custom additions —
if mode == "long":
    file_cats = sorted(df[st.session_state.cat_col].dropna().unique())
elif mode == "wide":
    file_cats = sorted(c[:-4] for c in df.columns if c.endswith("_raw"))
else:
    file_cats = [c for c in df.columns if c != st.session_state.name_col]

if "custom_cats" not in st.session_state:
    st.session_state.custom_cats = []
with st.sidebar.expander("➕ Add a custom category", expanded=False):
    new_cat = st.text_input("New category name", key="new_cat")
    new_w = st.number_input("Default weight", min_value=0.0, value=0.0, step=1.0, key="new_w")
    if st.button("Add category"):
        if new_cat and new_cat not in file_cats and new_cat not in st.session_state.custom_cats:
            st.session_state.custom_cats.append(new_cat)
            st.success(f"Added “{new_cat}”")
        else:
            st.warning("Provide a unique, non-empty name.")

all_categories = file_cats + st.session_state.custom_cats
active = st.sidebar.multiselect(
    " Active categories",
    options=all_categories,
    default=all_categories,
    key="active"
)

# — weights & maximums UI —
st.sidebar.header("Category Weights")
weights = {
    cat: st.sidebar.number_input(
        f"{cat} weight",
        min_value=0.0,
        value=st.session_state.get(f"w_{cat}", 40.0 if cat not in file_cats else 0.0),
        step=1.0,
        key=f"w_{cat}"
    )
    for cat in active
}

st.sidebar.header("Category Maximums")
max_scores = {}
for cat in active:
    if mode == "wide" and f"{cat}_maximum" in df.columns:
        max_scores[cat] = None
        st.sidebar.write(f"{cat}: using CSV `<{cat}_maximum>`")
    else:
        max_scores[cat] = st.sidebar.number_input(
            f"{cat} total points",
            min_value=0.0,
            value=st.session_state.get(f"max_{cat}", 100.0),
            step=1.0,
            key=f"max_{cat}"
        )

# — denominator for overall percentage —
total_point = sum(w for c, w in weights.items() if c.lower() != "extra credit")

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

# — compute results —
results = []
if mode == "long":
    for student, grp in df.groupby(st.session_state.name_col):
        point_achieved = ec_total = 0.0
        detail = []
        # grab NetID if available
        netid_val = grp[netid_col].iloc[0] if netid_col else None

        for _, row in grp.iterrows():
            cat = row[st.session_state.cat_col]
            if cat not in active:
                continue
            raw = row[st.session_state.raw_col]
            mx = max_scores[cat]
            w = weights.get(cat, 0)
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
        entry = {
            "Name":             student,
            "Point Achieved":   round(point_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%",
            "Details":          detail
        }
        if netid_col:
            entry["NetID"] = netid_val
        results.append(entry)

else:
    for _, row in df.iterrows():
        student = row[st.session_state.name_col]
        point_achieved = ec_total = 0.0
        detail = []
        netid_val = row[netid_col] if netid_col else None

        for cat in active:
            raw_col = f"{cat}_raw"
            if raw_col not in df.columns:
                continue
            raw = row[raw_col]
            mx = row[f"{cat}_maximum"] if f"{cat}_maximum" in row else max_scores[cat]
            w = weights.get(cat, 0)
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
        entry = {
            "Name":             student,
            "Point Achieved":   round(point_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%",
            "Details":          detail
        }
        if netid_col:
            entry["NetID"] = netid_val
        results.append(entry)

# — optional search —
search_term = st.text_input("🔍 Search student", key="search_term")
if search_term:
    results = sorted(
        results,
        key=lambda r: search_term.lower() not in r["Name"].lower()
    )

# — build summary DataFrame —
df_res = pd.DataFrame(results)
summary = df_res.drop(columns=["Details"], errors="ignore")
if "Name" in summary.columns:
    summary = summary.set_index("Name")

st.subheader("📋 Summary")
st.dataframe(summary)

# — per-student breakdowns —
for idx, row in enumerate(results):
    with st.expander(f"🔍 {row['Name']}'s Breakdown"):
        detail_df = pd.DataFrame(row["Details"])
        if not detail_df.empty:
            for col in ["Raw", "Max", "Weight", "Points Earned"]:
                detail_df[col] = detail_df[col].apply(lambda x: f"{float(x):.2f}")
            st.table(detail_df.set_index("Category"))
        else:
            st.write("No detail rows to display.")
