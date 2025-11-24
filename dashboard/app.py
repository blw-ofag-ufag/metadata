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

# Import settings (to get DB_URL)
from src.config import settings

# ---------------------------------------------------------------------------
# 1. Helper Functions & Setup
# ---------------------------------------------------------------------------

st.set_page_config(page_title="BLW Metadata Dashboard", layout="wide", page_icon="🏆")

# --- CUSTOM CSS FOR TOP RIGHT BUTTONS ---
st.markdown("""
    <style>
    /* Aligns buttons vertically with the title */
    div[data-testid="column"] {
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_db_engine():
    """Initialize DB connection cached."""
    return create_engine(settings.DB_URL)

def get_localized_text(data, lang_code: str) -> str:
    """
    Fallback logic for multilingual JSON fields (e.g., titles).
    Priority: Selected Lang -> DE -> First available key -> 'N/A'
    """
    if not isinstance(data, dict):
        return str(data)
    
    # 1. Try selected language
    if text := data.get(lang_code):
        return text
    
    # 2. Fallback to German (Official standard)
    if text := data.get("de"):
        return text
    
    # 3. Fallback to first available key
    if data:
        return next(iter(data.values()))
    
    return "N/A"

@st.cache_data(ttl=600)
def load_data():
    """Fetch all datasets from SQLite into a Pandas DataFrame."""
    engine = get_db_engine()
    
    query = "SELECT * FROM datasets" 
    
    try:
        df = pd.read_sql(query, engine)
        
        # Parse JSON columns that came back as strings from SQLite
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

# Initialize Session State for Language
if 'lang' not in st.session_state:
    st.session_state.lang = 'de'

def set_lang(code):
    """Callback to set language and force rerun"""
    st.session_state.lang = code

# Layout: Title (Left) vs Buttons (Right)
col_header, col_spacer, col_lang = st.columns([6, 1, 2])

# Language Buttons (Right Side)
with col_lang:
    # Create 4 small columns for the buttons
    b_de, b_fr, b_it, b_en = st.columns(4)
    
    # We use buttons. If clicked, we update state.
    # 'type="primary"' highlights the active language
    if b_de.button("DE", type="primary" if st.session_state.lang == 'de' else "secondary", use_container_width=True):
        set_lang('de')
        st.rerun()
        
    if b_fr.button("FR", type="primary" if st.session_state.lang == 'fr' else "secondary", use_container_width=True):
        set_lang('fr')
        st.rerun()
        
    if b_it.button("IT", type="primary" if st.session_state.lang == 'it' else "secondary", use_container_width=True):
        set_lang('it')
        st.rerun()
        
    if b_en.button("EN", type="primary" if st.session_state.lang == 'en' else "secondary", use_container_width=True):
        set_lang('en')
        st.rerun()

# Set current language context
lang_code = st.session_state.lang
T = TRANSLATIONS[lang_code]

# Title (Left Side) - Updated after language selection
with col_header:
    st.title(T["app_title"])

# ---------------------------------------------------------------------------
# 3. Data Loading & Processing
# ---------------------------------------------------------------------------

df = load_data()

if df.empty:
    st.warning(T["inspector_no_data"])
    st.stop()

# Pre-process Localized Titles for display
df['display_title'] = df['title'].apply(lambda x: get_localized_text(x, lang_code))

# Filter Logic (Simplified: No Organization Filter)
filtered_df = df

# ---------------------------------------------------------------------------
# 4. Dashboard Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs([T["tab_worklist"], T["tab_overview"], T["tab_inspector"]])

# --- TAB 1: WORKLIST (PRIORITY) ---
with tab1:
    st.markdown(f"### {T['tab_worklist']}")
    
    # 1. Logic: Prioritize items with Schema Violations or Low Quality
    def categorize_severity(row):
        if row['schema_violations_count'] > 0:
            return T["severity_high"]
        elif row['input_quality_score'] < 5000: 
            return T["severity_med"]
        return T["severity_low"]

    worklist_df = filtered_df.copy()
    worklist_df['severity'] = worklist_df.apply(categorize_severity, axis=1)

    # 2. NEW LOGIC: Create a display column for violations
    # This allows conditional formatting (Checkmark vs Siren)
    def format_violations(count):
        if count == 0:
            return f"0 ✅" # Green check for zero errors
        else:
            return f"{count} 🚨" # Siren for errors

    worklist_df['violations_display'] = worklist_df['schema_violations_count'].apply(format_violations)
    
    # 3. Update columns to display (swap raw count for display column)
    display_cols = ['severity', 'display_title', 'violations_display', 'input_quality_score', 'id']
    
    st.dataframe(
        worklist_df[display_cols],
        column_config={
            "severity": st.column_config.TextColumn(T["col_severity"]),
            "display_title": st.column_config.TextColumn(T["col_title"], width="medium"),
            
            # UPDATED CONFIGURATION
            "violations_display": st.column_config.TextColumn(
                T["col_violations"], 
                help="Schema validation errors"
            ),
            
            "input_quality_score": st.column_config.ProgressColumn(
                T["col_score"], 
                format="%.0f", 
                min_value=0, 
                # Dynamic max value based on data
                max_value=float(worklist_df['input_quality_score'].max()) if not worklist_df.empty else 100
            ),
            "id": st.column_config.TextColumn(T["col_id"], width="small", help="DCAT Identifier")
        },
        hide_index=True,
        use_container_width=True
    )

# --- TAB 2: OVERVIEW ---
with tab2:
    st.markdown(f"### {T['tab_overview']}")
    
    # Top Metrics
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
        # Flatten schema validation messages to count top errors
        all_errors = []
        if 'schema_violation_messages' in filtered_df.columns:
            for msgs in filtered_df['schema_violation_messages']:
                if isinstance(msgs, list):
                    all_errors.extend(msgs)
        
        if all_errors:
            error_counts = pd.Series(all_errors).value_counts().head(5)
            st.bar_chart(error_counts)
        else:
            st.info("No validation errors found.")

# --- TAB 3: INSPECTOR ---
with tab3:
    st.markdown(f"### {T['tab_inspector']}")
    
    # Create a mapping for the selectbox: "Title (ID)" -> ID
    dataset_map = {
        f"{row['display_title']} ({str(row['id'])[:8]}...)": row['id'] 
        for _, row in filtered_df.iterrows()
    }
    
    selected_display = st.selectbox(
        T["inspector_select"], 
        options=dataset_map.keys()
    )
    
    if selected_display:
        selected_id = dataset_map[selected_display]
        record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        # Scorecard Header
        sc1, sc2, sc3 = st.columns([1, 3, 1])
        with sc1:
            score = record['input_quality_score']
            if score > 10000:
                st.success(f"Score: {score:.0f}")
            elif score > 5000:
                st.warning(f"Score: {score:.0f}")
            else:
                st.error(f"Score: {score:.0f}")
                
        with sc2:
            st.subheader(record['display_title'])
            st.caption(f"ID: {record['id']}")
            
        # Details
        st.divider()
        st.markdown(f"#### {T['inspector_details']}")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**Schema Violations:**")
            if record['schema_violations_count'] > 0:
                # Use proper column name for messages
                msgs = record.get('schema_violation_messages', [])
                if isinstance(msgs, list):
                    for msg in msgs:
                        st.error(f"• {msg}")
            else:
                st.success("No schema violations passed from input.")
                
        with col_d2:
            st.markdown("**Computed Quality Checks (Phase 3):**")
            # Displaying the computed Swiss Score if available
            if 'swiss_score' in record and record['swiss_score'] > 0:
                 st.info(f"Swiss FAIRC Score: {record['swiss_score']:.0f} / 225")
                 st.progress(min(record['swiss_score'] / 225.0, 1.0))
            else:
                 st.info("Deep quality checks pending.")

        with st.expander(T["inspector_raw"]):
            # Convert Series to dict, dropping internal columns for cleaner view
            raw_view = record.to_dict()
            # Remove display helpers
            if 'display_title' in raw_view: del raw_view['display_title']
            if 'severity' in raw_view: del raw_view['severity']
            st.json(raw_view)