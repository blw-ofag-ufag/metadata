import streamlit as st
import pandas as pd
import json
from sqlalchemy import create_engine
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import static translations
from dashboard.translations import TRANSLATIONS

# Import settings (to get DB_URL and Weights)
from src.config import settings

# ---------------------------------------------------------------------------
# 1. Helper Functions & Setup
# ---------------------------------------------------------------------------

st.set_page_config(page_title="BLW Metadata Dashboard", layout="wide", page_icon="🏆")

# --- CUSTOM CSS FOR TOP RIGHT BUTTONS ---
# added CSS to prevent text wrapping in buttons and reduce padding
st.markdown("""
    <style>
    /* Aligns buttons vertically with the title */
    div[data-testid="column"] {
        align-items: center;
    }
    
    /* Fix for Language Buttons on small screens:
       1. Prevent text from wrapping (D \n E)
       2. Reduce padding so text fits in narrow columns
    */
    div[data-testid="stButton"] button {
        white-space: nowrap !important;
        padding-left: 4px !important;
        padding-right: 4px !important;
        min-width: 0px !important;
    }
    
    /* Ensure the text inside the button is centered and visible */
    div[data-testid="stButton"] button p {
        font-weight: bold;
        margin: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_db_engine():
    """Initialize DB connection cached."""
    return create_engine(settings.DB_URL)

def get_localized_text(data, lang_code: str) -> str:
    """Fallback logic for multilingual JSON fields."""
    if not isinstance(data, dict):
        return str(data)
    if text := data.get(lang_code):
        return text
    if text := data.get("de"):
        return text
    if data:
        return next(iter(data.values()))
    return "N/A"

@st.cache_data(ttl=600)
def load_data():
    """Fetch all datasets from SQLite into a Pandas DataFrame."""
    engine = get_db_engine()
    
    try:
        df = pd.read_sql("SELECT * FROM datasets", engine)
        
        # Parse JSON columns
        json_cols = ['title', 'description', 'keywords', 'themes', 'schema_violation_messages']
        for col in json_cols:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.loads(x) if x and isinstance(x, str) else (x if isinstance(x, (dict, list)) else {})
                )
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# 2. Header & Language Config (Top Right)
# ---------------------------------------------------------------------------

# Initialize Session State
if 'lang' not in st.session_state:
    st.session_state.lang = 'de'

def set_lang(code):
    st.session_state.lang = code

# Layout: Title (Left) vs Buttons (Right)
# Adjusted Ratio slightly to give buttons more breathing room (from [6,1,2] to [6, 0.5, 2.5])
col_header, col_spacer, col_lang = st.columns([6, 0.5, 2.5])

# Language Buttons
with col_lang:
    b_de, b_fr, b_it, b_en = st.columns(4)
    
    if b_de.button("DE", type="primary" if st.session_state.lang == 'de' else "secondary", width="stretch"):
        set_lang('de'); st.rerun()
    if b_fr.button("FR", type="primary" if st.session_state.lang == 'fr' else "secondary", width="stretch"):
        set_lang('fr'); st.rerun()
    if b_it.button("IT", type="primary" if st.session_state.lang == 'it' else "secondary", width="stretch"):
        set_lang('it'); st.rerun()
    if b_en.button("EN", type="primary" if st.session_state.lang == 'en' else "secondary", width="stretch"):
        set_lang('en'); st.rerun()

lang_code = st.session_state.lang
T = TRANSLATIONS[lang_code]

with col_header:
    st.title(T["app_title"])

# ---------------------------------------------------------------------------
# 3. Data Loading & Processing
# ---------------------------------------------------------------------------

df = load_data()

if df.empty:
    st.warning(T["inspector_no_data"])
    st.stop()

# Pre-process Localized Titles
df['display_title'] = df['title'].apply(lambda x: get_localized_text(x, lang_code))
filtered_df = df

# ---------------------------------------------------------------------------
# 4. Dashboard Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    T["tab_worklist"], 
    T["tab_overview"], 
    T["tab_inspector"], 
    T["tab_help"]
])

# --- TAB 1: WORKLIST ---
with tab1:
    st.markdown(f"### {T['tab_worklist']}")
    
    def categorize_severity(row):
        if row['schema_violations_count'] > 0:
            return T["severity_high"]
        elif row['input_quality_score'] < 5000: 
            return T["severity_med"]
        return T["severity_low"]

    def format_violations(count):
        if count == 0:
            return f"0 ✅"
        else:
            return f"{count} 🚨"

    worklist_df = filtered_df.copy()
    worklist_df['severity'] = worklist_df.apply(categorize_severity, axis=1)
    worklist_df['violations_display'] = worklist_df['schema_violations_count'].apply(format_violations)
    
    st.dataframe(
        worklist_df[['severity', 'display_title', 'violations_display', 'input_quality_score', 'id']],
        column_config={
            "severity": st.column_config.TextColumn(T["col_severity"]),
            "display_title": st.column_config.TextColumn(T["col_title"], width="medium"),
            "violations_display": st.column_config.TextColumn(T["col_violations"]),
            "input_quality_score": st.column_config.ProgressColumn(
                T["col_score"], format="%.0f", min_value=0, 
                max_value=float(worklist_df['input_quality_score'].max()) if not worklist_df.empty else 100
            ),
            "id": st.column_config.TextColumn(T["col_id"], width="small", help="DCAT Identifier")
        },
        hide_index=True,
        width="stretch"
    )

# --- TAB 2: OVERVIEW ---
with tab2:
    st.markdown(f"### {T['tab_overview']}")
    c1, c2, c3 = st.columns(3)
    c1.metric(T["metric_total"], len(filtered_df))
    c2.metric(T["metric_score"], f"{filtered_df['input_quality_score'].mean():.0f}")
    c3.metric(T["metric_violations"], int(filtered_df['schema_violations_count'].sum()))
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.caption(T["chart_score_dist"])
        st.bar_chart(filtered_df['input_quality_score'])
        
    with col_chart2:
        st.caption(T["chart_top_errors"])
        all_errors = []
        if 'schema_violation_messages' in filtered_df.columns:
            for msgs in filtered_df['schema_violation_messages']:
                if isinstance(msgs, list):
                    all_errors.extend(msgs)
        
        if all_errors:
            st.bar_chart(pd.Series(all_errors).value_counts().head(5))
        else:
            st.info("No validation errors found.")

# --- TAB 3: INSPECTOR ---
with tab3:
    st.markdown(f"### {T['tab_inspector']}")
    dataset_map = {
        f"{row['display_title']} ({str(row['id'])[:8]}...)": row['id'] 
        for _, row in filtered_df.iterrows()
    }
    
    selected_display = st.selectbox(T["inspector_select"], options=dataset_map.keys())
    
    if selected_display:
        selected_id = dataset_map[selected_display]
        record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        sc1, sc2, sc3 = st.columns([1, 3, 1])
        with sc1:
            score = record['input_quality_score']
            if score > 10000: st.success(f"Score: {score:.0f}")
            elif score > 5000: st.warning(f"Score: {score:.0f}")
            else: st.error(f"Score: {score:.0f}")
        with sc2:
            st.subheader(record['display_title'])
            st.caption(f"ID: {record['id']}")
            
        st.divider()
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**Schema Violations:**")
            if record['schema_violations_count'] > 0:
                msgs = record.get('schema_violation_messages', [])
                if isinstance(msgs, list):
                    for msg in msgs: st.error(f"• {msg}")
            else:
                st.success("No violations.")
                
        with col_d2:
            st.markdown("**Quality Details:**")
            if 'swiss_score' in record and record['swiss_score'] > 0:
                 st.info(f"Swiss FAIRC Score: {record['swiss_score']:.0f} / 225")
                 st.progress(min(record['swiss_score'] / 225.0, 1.0))
            else:
                 st.info("Deep quality checks pending.")

        with st.expander(T["inspector_raw"]):
            raw_view = record.to_dict()
            if 'display_title' in raw_view: del raw_view['display_title']
            if 'severity' in raw_view: del raw_view['severity']
            st.json(raw_view)

# --- TAB 4: HELP & METHODOLOGY ---
with tab4:
    st.markdown(f"### {T['tab_help']}")
    
    # Core Concept
    st.info(T["help_intro"])

    # ROW 1: Descriptions
    col_desc1, col_desc2 = st.columns(2)
    with col_desc1:
        st.markdown(f"#### {T['help_vio_title']}")
        st.markdown(T["help_vio_desc"])
    with col_desc2:
        st.markdown(f"#### {T['help_score_title']}")
        st.markdown(T["help_score_desc"])

    # ROW 2: Goals
    col_goal1, col_goal2 = st.columns(2)
    with col_goal1:
        st.success(T["help_vio_goal"])
    with col_goal2:
        st.success(T["help_score_goal"])

    st.divider()
    
    # TABLE: Grouped by Dimension, Sorted by Importance
    st.markdown(f"### {T['help_calc_title']}")
    
    table_md = f"""
| {T['help_table_dim']} | {T['help_table_crit']} | {T['help_table_pts']} |
| :--- | :--- | :--- |
| **Findability** | {T['crit_keywords']} (`dcat:keyword`) | +{settings.WEIGHT_FINDABILITY_KEYWORDS} |
| | {T['crit_themes']} (`dcat:theme`) | +{settings.WEIGHT_FINDABILITY_CATEGORIES} |
| | {T['crit_geo']} (`dct:spatial`) | +{settings.WEIGHT_FINDABILITY_GEO_SEARCH} |
| | {T['crit_time']} (`dct:temporal`) | +{settings.WEIGHT_FINDABILITY_TIME_SEARCH} |
| **Accessibility**| {T['crit_access']} (HTTP 200) | +{settings.WEIGHT_ACCESSIBILITY_ACCESS_URL} |
| | {T['crit_download_valid']} (HTTP 200) | +{settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID} |
| | {T['crit_download']} | +{settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL} |
| **Interoperability**| {T['crit_dcat']} | +{settings.WEIGHT_INTEROP_DCAT_AP} |
| | {T['crit_format']} | +{settings.WEIGHT_INTEROP_FORMAT} |
| | {T['crit_openfmt']} | +{settings.WEIGHT_INTEROP_NON_PROPRIETARY} |
| | {T['crit_machine']} | +{settings.WEIGHT_INTEROP_MACHINE_READABLE} |
| | {T['crit_media']} | +{settings.WEIGHT_INTEROP_MEDIA_TYPE} |
| | {T['crit_vocab']} | +{settings.WEIGHT_INTEROP_VOCABULARY} |
| **Reusability** | {T['crit_license']} | +{settings.WEIGHT_REUSE_LICENSE} |
| | {T['crit_contact']} | +{settings.WEIGHT_REUSE_CONTACT_POINT} |
| | {T['crit_lic_vocab']} | +{settings.WEIGHT_REUSE_LICENSE_VOCAB} |
| | {T['crit_access_res']} | +{settings.WEIGHT_REUSE_ACCESS_RESTRICTION} |
| | {T['crit_publisher']} | +{settings.WEIGHT_REUSE_PUBLISHER} |
| | {T['crit_access_vocab']} | +{settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB} |
| **Contextuality** | {T['crit_rights']} | +{settings.WEIGHT_CONTEXT_RIGHTS} |
| | {T['crit_filesize']} | +{settings.WEIGHT_CONTEXT_FILE_SIZE} |
| | {T['crit_issue']} | +{settings.WEIGHT_CONTEXT_ISSUE_DATE} |
| | {T['crit_mod']} | +{settings.WEIGHT_CONTEXT_MODIFICATION_DATE} |
    """
    
    st.markdown(table_md)