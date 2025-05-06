import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Grade Calculator",
    layout="wide",
)

st.title("🎓 Grade Calculator")
st.markdown("Upload either a **long** or **wide** CSV; ")
st.markdown("tweak weights & maximums in the sidebar; ")
st.markdown("see per-student breakdowns.")

uploaded = st.file_uploader("Upload grades CSV", type="csv")
if not uploaded:
    st.info("Awaiting CSV upload…")
    st.stop()

df = pd.read_csv(uploaded)

# detect long vs wide
long_cols = {'Name','Category','raw','maximum'}
if long_cols.issubset(df.columns):
    mode = 'long'
elif any(col.endswith('_raw') for col in df.columns):
    mode = 'wide'
else:
    st.error(
        "CSV not recognized. Must be either:\n"
        "- **Long** form with columns `Name, Category, raw, maximum`, OR\n"
        "- **Wide** form with `<Category>_raw` (and optionally `<Category>_maximum`) columns."
    )
    st.stop()

# — Column mapping —
with st.sidebar.expander("🔧 Column mapping", expanded=False):
    if mode == 'long':
        name_col = st.selectbox("Student name column",  df.columns, index=df.columns.get_loc('Name'))
        cat_col  = st.selectbox("Category column",      df.columns, index=df.columns.get_loc('Category'))
        raw_col  = st.selectbox("Raw score column",     df.columns, index=df.columns.get_loc('raw'))
        max_col  = st.selectbox("Max score column",     df.columns, index=df.columns.get_loc('maximum'))
    else:
        name_col = st.selectbox(
            "Student name column",
            df.columns,
            index=(df.columns.get_loc('Name') if 'Name' in df.columns else 0)
        )

# build list of categories found in file
if mode == 'long':
    file_cats = sorted(df[cat_col].unique())
else:
    file_cats = sorted(cat[:-4] for cat in df.columns if cat.endswith('_raw'))

# allow custom categories
if 'custom_cats' not in st.session_state:
    st.session_state['custom_cats'] = []
with st.sidebar.expander("➕ Add a custom category", expanded=False):
    new_cat = st.text_input("New category name", "")
    new_w   = st.number_input("Default weight", min_value=0.0, value=0.0, step=1.0, key="newcat_w")
    if st.button("Add category"):
        if new_cat and new_cat not in file_cats and new_cat not in st.session_state['custom_cats']:
            st.session_state['custom_cats'].append(new_cat)
            st.success(f"Added “{new_cat}”")
        else:
            st.warning("Provide a unique, non-empty name.")
all_categories = file_cats + st.session_state['custom_cats']

# which categories to include
active = st.sidebar.multiselect("✅ Active categories", options=all_categories, default=all_categories)

# — Weights —
st.sidebar.header("Category Weights")
weights = {
    cat: st.sidebar.number_input(f"{cat} weight", min_value=0.0, value=40.0 if cat not in file_cats else 0.0, step=1.0, key=f"w_{cat}")
    for cat in active
}

# — Maximums (new!) —
st.sidebar.header("Category Maximums")
# we'll collect a default max for each category if CSV has none
max_scores = {}
for cat in active:
    csv_has_max = (
        (mode == 'long' and max_col in df.columns) or
        (mode == 'wide' and f"{cat}_maximum" in df.columns)
    )
    if csv_has_max:
        # mark as None to signal “take from CSV”
        max_scores[cat] = None
        st.sidebar.write(f"{cat}: using CSV maximum")
    else:
        # ask user
        max_scores[cat] = st.sidebar.number_input(
            f"{cat} total points",
            min_value=0.0,
            value=100.0,
            step=1.0,
            key=f"maxinp_{cat}"
        )

core_denominator = sum(w for c,w in weights.items() if c.lower() != 'extra credit')

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

results = []

if mode == 'long':
    # long form: each row has its own maximum, or we use user-specified max
    for student, grp in df.groupby(name_col):
        core_total = ec_total = 0.0
        detail = []
        for _, row in grp.iterrows():
            cat = row[cat_col]
            if cat not in active:
                continue
            raw = row[raw_col]
            # determine maximum: CSV value or sidebar entry
            mx = row[max_col] if max_col in df.columns and max_scores.get(cat) is None else max_scores[cat]
            w  = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)
            if cat.lower() == 'extra credit':
                ec_total += pts
            else:
                core_total += pts
            detail.append({
                'Category':      cat,
                'Raw':           raw,
                'Max':           mx,
                'Weight':        w,
                'Points Earned': round(pts, 2)
            })
        overall_pct = (core_total / core_denominator * 100) if core_denominator else 0
        results.append({
            'Name':             student,
            'Core Total':       round(core_total, 2),
            'Extra Credit':     round(ec_total, 2),
            'Core Denominator': core_denominator,
            'Overall % (core)': f"{overall_pct:.2f}%",
            'Details':          detail
        })

else:
    # wide form: one row per student
    for _, row in df.iterrows():
        student = row.get(name_col, '')
        core_total = ec_total = 0.0
        detail = []
        for cat in active:
            raw_col_name = f"{cat}_raw"
            csv_max_col = f"{cat}_maximum"
            if raw_col_name not in df.columns:
                continue
            raw = row[raw_col_name]
            # pick CSV max if available, else sidebar
            mx = row[csv_max_col] if csv_max_col in df.columns and max_scores.get(cat) is None else max_scores[cat]
            w  = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)
            if cat.lower() == 'extra credit':
                ec_total += pts
            else:
                core_total += pts
            detail.append({
                'Category':      cat,
                'Raw':           raw,
                'Max':           mx,
                'Weight':        w,
                'Points Earned': round(pts, 2)
            })
        overall_pct = (core_total / core_denominator * 100) if core_denominator else 0
        results.append({
            'Name':             student,
            'Core Total':       round(core_total, 2),
            'Extra Credit':     round(ec_total, 2),
            'Core Denominator': core_denominator,
            'Overall % (core)': f"{overall_pct:.2f}%",
            'Details':          detail
        })

# build summary DataFrame
df_res  = pd.DataFrame(results)
summary = df_res.drop(columns=['Details'], errors='ignore')

st.subheader("📋 Summary")
if 'Name' in summary.columns:
    summary = summary.set_index('Name')
else:
    st.warning("⚠️ Couldn’t find your mapped ‘Name’ column; showing all columns instead.")

st.dataframe(summary)

# per-student breakdowns
for row in results:
    student = row.get('Name', '')
    with st.expander(f"🔍 {student}'s Breakdown"):
        detail_df = pd.DataFrame(row.get('Details', []))
        if not detail_df.empty:
            for col in ['Raw','Max','Weight','Points Earned']:
                detail_df[col] = detail_df[col].apply(lambda x: f"{float(x):.2f}")
            st.table(detail_df.set_index('Category'))
        else:
            st.write("No detail rows to display.")
