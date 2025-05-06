import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Grade Calculator",
    layout="wide",
)

st.title("🎓 Grade Calculator")
st.markdown("Upload either a **long** or **wide** CSV; tweak weights in the sidebar; see per-student breakdowns.")

st.sidebar.header("Category Weights")
default_weights = {
    'HW First Half':   40,
    'Quiz First Half': 60,
    'Midterm I':       90,
    'HW Second Half':  50,
    'Quiz Second Half':60,
    'Midterm II':      90,
    'Project':         30,
    'Final':          180,
    'Extra Credit':    40,
}
weights = {
    cat: st.sidebar.number_input(cat, min_value=0.0, value=float(w), step=1.0)
    for cat, w in default_weights.items()
}

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

def weighted_score(raw, maximum, weight):
    return (raw / maximum) * weight if maximum else 0

core_denominator = sum(w for cat, w in weights.items() if cat != 'Extra Credit')

results = []

if mode == 'long':
    for student, grp in df.groupby('Name'):
        core_total = ec_total = 0.0
        detail = []
        for _, row in grp.iterrows():
            cat = row['Category']
            raw, mx = row['raw'], row['maximum']
            w = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)
            if cat == 'Extra Credit':
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
    cats_present = [
        cat for cat in weights
        if f"{cat}_raw" in df.columns and f"{cat}_maximum" in df.columns
    ]
    for _, row in df.iterrows():
        student = row['Name']
        core_total = ec_total = 0.0
        detail = []
        for cat in cats_present:
            raw = row[f"{cat}_raw"]
            mx  = row[f"{cat}_maximum"]
            w   = weights.get(cat, 0)
            pts = weighted_score(raw, mx, w)
            if cat == 'Extra Credit':
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

summary = pd.DataFrame(results).drop(columns=['Details'])
st.subheader("📋 Summary")
st.dataframe(summary.set_index('Name'))

for row in results:
    with st.expander(f"🔍 {row['Name']}'s Breakdown"):
        detail_df = pd.DataFrame(row['Details'])
        st.table(detail_df.set_index('Category'))
