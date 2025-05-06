import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Grade Calculator",
    layout="wide",
)

st.title("🎓 Grade Calculator")
st.markdown("Upload either a **long** or **wide** CSV; " \
"tweak weights in the sidebar; " \
"see per-student breakdowns.")

uploaded = st.file_uploader("Upload grades CSV", type="csv")
if not uploaded:
    st.info("Awaiting CSV upload…")
    st.stop()

df = pd.read_csv(uploaded)

long_cols = {'Name','Category','raw','maximum'}
if long_cols.issubset(df.columns):
    mode = 'long'
elif any(col.endswith('_raw') for col in df.columns):
    mode = 'wide'
else:
    st.error(
        "CSV not recognized. Must be either:\n"
        "- **Long** form with columns `Name, Category, raw, maximum`, OR\n"
        "- **Wide** form with `<Category>_raw` & `<Category>_maximum` columns."
    )
    st.stop()

with st.sidebar.expander("🔧 Column mapping", expanded=False):
    if mode == 'long':
        name_col    = st.selectbox("Student name column",  df.columns.tolist(), index=df.columns.get_loc('Name'))
        cat_col     = st.selectbox("Category column",      df.columns.tolist(), index=df.columns.get_loc('Category'))
        raw_col     = st.selectbox("Raw score column",     df.columns.tolist(), index=df.columns.get_loc('raw'))
        max_col     = st.selectbox("Max score column",     df.columns.tolist(), index=df.columns.get_loc('maximum'))
    else:
        name_col = st.selectbox("Student name column", df.columns.tolist(), index=df.columns.get_loc('Name') if 'Name' in df.columns else 0)

if mode == 'long':
    file_cats = sorted(df[cat_col].unique())
else:
    file_cats = sorted(
        cat[:-4]
        for cat in df.columns
        if cat.endswith('_raw')
    )

if 'custom_cats' not in st.session_state:
    st.session_state['custom_cats'] = []

with st.sidebar.expander("➕ Add a custom category", expanded=False):
    new_cat = st.text_input("New category name", "")
    new_w   = st.number_input("Default weight", min_value=0.0, value=0.0, step=1.0, key="newcat_w")
    if st.button("Add category"):
        if new_cat and new_cat not in st.session_state['custom_cats'] and new_cat not in file_cats:
            st.session_state['custom_cats'].append(new_cat)
            st.success(f"Added “{new_cat}”")
        else:
            st.warning("Provide a unique, non-empty name.")

all_categories = file_cats + st.session_state['custom_cats']

active = st.sidebar.multiselect(
    "✅ Active categories",
    options=all_categories,
    default=all_categories
)

st.sidebar.header("Category Weights")
weights = {}
for cat in active:
    weights[cat] = st.sidebar.number_input(f"{cat} weight", min_value=0.0, value=40.0 if cat not in file_cats else 0.0, step=1.0, key=f"w_{cat}")

core_denominator = sum(w for cat,w in weights.items() if cat.lower() != 'extra credit')

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

results = []
if mode == 'long':
    for student, grp in df.groupby(name_col):
        core_total = ec_total = 0.0
        detail = []
        for _, row in grp.iterrows():
            cat = row[cat_col]
            if cat not in active:
                continue
            raw = row[raw_col]
            mx  = row[max_col]
            w   = weights.get(cat, 0)
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
                'Points Earned': round(pts,2)
            })
        overall_pct = core_total / core_denominator * 100 if core_denominator else 0
        results.append({
            'Name':             student,
            'Core Total':       round(core_total,2),
            'Extra Credit':     round(ec_total,2),
            'Core Denominator': core_denominator,
            'Overall % (core)': f"{overall_pct:.2f}%",
            'Details':          detail
        })
else:
    
    for _, row in df.iterrows():
        student = row.get(name_col, '')
        core_total = ec_total = 0.0
        detail = []
        for cat in active:
            if f"{cat}_raw" not in df.columns or f"{cat}_maximum" not in df.columns:
                continue
            raw = row[f"{cat}_raw"]
            mx  = row[f"{cat}_maximum"]
            w   = weights.get(cat, 0)
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
                'Points Earned': round(pts,2)
            })
        overall_pct = core_total / core_denominator * 100 if core_denominator else 0
        results.append({
            'Name':             student,
            'Core Total':       round(core_total,2),
            'Extra Credit':     round(ec_total,2),
            'Core Denominator': core_denominator,
            'Overall % (core)': f"{overall_pct:.2f}%",
            'Details':          detail
        })

df_res  = pd.DataFrame(results)
summary = df_res.drop(columns=['Details'], errors='ignore')

st.subheader("📋 Summary")
if 'Name' in summary.columns:
    summary = summary.set_index('Name')
else:
    st.warning("⚠️ Couldn’t find your mapped ‘Name’ column; showing all columns instead.")

st.dataframe(summary)

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
