import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grade Calculator", layout="wide")
st.title("🎓 Grade Calculator")
st.markdown("Upload a CSV (long, wide, or raw-only). Blank/Unnamed columns are ignored.")

with st.expander("📄 Example CSV formats", expanded=False):
    st.markdown("**1. Wide-format** (uses `_raw`/`_maximum` columns)")
    st.code(
        """\
Name,NetID,HW1_raw,HW1_maximum,Quiz1_raw,Quiz1_maximum,Final_raw,Final_maximum,Extra Credit_raw
Vinit,a123,80,100,18,25,150,180,5
Kano,b456,92,100,22,25,170,180,2
""",
        language="csv"
    )

    st.markdown("**2. Long-format** (one row per student × category)")
    st.code(
        """\
Name,Category,raw,maximum,NetID
Vinit,HW1,80,100,a123
Vinit,Quiz1,18,25,a123
Vinit,Final,150,180,a123
Vinit,Extra Credit,5,10,a123
Kano,HW1,92,100,b456
Kano,Quiz1,22,25,b456 
Kano,Final,170,180,b456
Kano,Extra Credit,2,10,b456
""",
        language="csv"
    )

    st.markdown("**3. Raw-only** (each column minus `Name` is a category , uses `_raw`)")
    st.code(
        """\
Name,HW1_raw,Quiz1_raw,Final_raw,Extra_raw Credit_raw,NetID
Vinit,80,18,150,5,a123
Kano,92,22,170,2,b456
""",
        language="csv"
    )

def _clear_df():
    st.session_state.pop("df", None)

uploaded = st.file_uploader(
    "Upload grades CSV",
    type="csv",
    key="uploaded_file",
    on_change=_clear_df
)

if "df" not in st.session_state:
    if not uploaded:
        st.info("Awaiting CSV upload…")
        st.stop()
    st.session_state.df = pd.read_csv(uploaded)
df = st.session_state.df

df = df.loc[:, [c for c in df.columns if str(c).strip() and not str(c).startswith("Unnamed")]]

if "Name" not in df.columns:
    st.error(" CSV must include a ‘Name’ column.")
    st.stop()

netid_col = next((c for c in df.columns if c.lower() == "netid"), None)

long_cols = {"Name", "Category", "raw"}
if long_cols.issubset(df.columns):
    mode = "long"
elif any(c.endswith("_raw") for c in df.columns):
    mode = "wide"
else:
    mode = "raw-only"

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
    new_w   = st.number_input("Default weight", min_value=0.0, value=0.0, step=1.0, key="new_w")
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

include_ec = st.sidebar.checkbox(
    "Include extra credit in total achieved", value=False, key="include_ec"
)

total_point = sum(w for c, w in weights.items() if c.lower() != "extra credit")

default_min_pct = {"A":95.0, "B+":90.0, "B":85.0, "C+":80.0, "C":70.0, "F":0.0}
default_max_pct = {"A":100.0,"B+":94.99,"B":89.99,"C+":84.99,"C":79.99,"F":69.99}
default_min_pts = {g: total_point * p/100 for g, p in default_min_pct.items()}
default_max_pts = {g: total_point * p/100 for g, p in default_max_pct.items()}

grade_defs = {}
with st.sidebar.expander("📝 Letter Grade Settings", expanded=False):
    show_letter = st.checkbox("Show letter grades", key="show_letter")
    grade_mode  = st.selectbox("Assign by", ["Percentage", "Points"], key="grade_mode")

    if show_letter:
        for letter in ["A","B+","B","C+","C","F"]:
            min_key = f"{letter}_min"
            max_key = f"{letter}_max"
            col_low, col_high = st.columns(2)
            if grade_mode == "Percentage":
                with col_low:
                    low = st.number_input(
                        f"{letter} min %", min_value=0.0, max_value=100.0,
                        value=default_min_pct[letter], key=min_key
                    )
                with col_high:
                    high = st.number_input(
                        f"{letter} max %", min_value=0.0, max_value=100.0,
                        value=default_max_pct[letter], key=max_key
                    )
            else:
                with col_low:
                    low = st.number_input(
                        f"{letter} min pts", min_value=0.0, max_value=total_point,
                        value=default_min_pts[letter], key=min_key
                    )
                with col_high:
                    high = st.number_input(
                        f"{letter} max pts", min_value=0.0, max_value=total_point,
                        value=default_max_pts[letter], key=max_key
                    )
            grade_defs[letter] = (low, high)

def assign_grade(pct, pts):
    if not show_letter:
        return ""
    val = pct if grade_mode == "Percentage" else pts
    for letter in ["A","B+","B","C+","C","F"]:
        low, high = grade_defs.get(letter, (None, None))
        if low is not None and high is not None and low <= val <= high:
            return letter
    return ""

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

results = []
if mode == "long":
    for student, grp in df.groupby(st.session_state.name_col):
        point_achieved = ec_total = 0.0
        detail = []
        netid_val = grp[netid_col].iloc[0] if netid_col else None

        for _, row in grp.iterrows():
            cat = row[st.session_state.cat_col]
            if cat not in active:
                continue
            raw = row[st.session_state.raw_col]
            mx  = max_scores[cat]
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

        total_achieved = point_achieved + ec_total if include_ec else point_achieved
        overall_pct    = (point_achieved / total_point * 100) if total_point else 0.0

        entry = {
            "Name":             student,
            "Point Achieved":   round(total_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%"
        }
        if netid_col:
            entry["NetID"] = netid_val
        if show_letter:
            entry["Grade"] = assign_grade(overall_pct, total_achieved)
        entry["Details"] = detail
        results.append(entry)

else:
    for _, row in df.iterrows():
        student = row[st.session_state.name_col]
        point_achieved = ec_total = 0.0
        detail = []
        netid_val = row[netid_col] if netid_col else None

        for cat in active:
            raw_col_name = f"{cat}_raw"
            if raw_col_name not in df.columns:
                continue
            raw = row[raw_col_name]
            mx  = row.get(f"{cat}_maximum", max_scores[cat])
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

        total_achieved = point_achieved + ec_total if include_ec else point_achieved
        overall_pct    = (point_achieved / total_point * 100) if total_point else 0.0

        entry = {
            "Name":             student,
            "Point Achieved":   round(total_achieved, 2),
            "Extra Credit":     round(ec_total, 2),
            "Total Point":      total_point,
            "Overall % (core)": f"{overall_pct:.2f}%"
        }
        if netid_col:
            entry["NetID"] = netid_val
        if show_letter:
            entry["Grade"] = assign_grade(overall_pct, total_achieved)
        entry["Details"] = detail
        results.append(entry)

search_term = st.text_input("🔍 Search student", key="search_term")
if search_term:
    results = sorted(
        results,
        key=lambda r: search_term.lower() not in r["Name"].lower()
    )

df_res = pd.DataFrame(results)
summary = df_res.drop(columns=["Details"], errors="ignore")
if "Name" in summary.columns:
    summary = summary.set_index("Name")

st.subheader("📋 Summary")
st.dataframe(summary)

for idx, row in enumerate(results):
    with st.expander(f"🔍 {row['Name']}'s Breakdown"):
        detail_df = pd.DataFrame(row["Details"])
        if not detail_df.empty:
            for col in ["Raw", "Max", "Weight", "Points Earned"]:
                detail_df[col] = detail_df[col].apply(lambda x: f"{float(x):.2f}")
            st.table(detail_df.set_index("Category"))
        else:
            st.write("No detail rows to display.")
