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

# Import settings and models
from src.config import settings
from src.models import DatasetInput 
from src.logic import QualityScorer

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
    
    /* Fix for Language Buttons on small screens */
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
        # FIX: Added 'contact_point' to this list to prevent Pydantic validation errors
        json_cols = ['title', 'description', 'keywords', 'themes', 'contact_point', 'schema_violation_messages']
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
    
# Initialize Inspector Search State
if 'inspector_search' not in st.session_state:
    st.session_state.inspector_search = ""

def set_lang(code):
    st.session_state.lang = code

def clear_search():
    """Callback to clear search state."""
    st.session_state.inspector_search = ""

# Layout: Title (Left) vs Buttons (Right)
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

# Quick internal translation for search components
SEARCH_LABELS = {
    "de": {"ph": "Filter nach Titel oder ID...", "clear": "Filter löschen"},
    "fr": {"ph": "Filtrer par titre ou ID...", "clear": "Effacer"},
    "it": {"ph": "Filtra per titolo o ID...", "clear": "Cancellare"},
    "en": {"ph": "Filter by Title or ID...", "clear": "Clear Filter"}
}
S_TXT = SEARCH_LABELS.get(lang_code, SEARCH_LABELS["en"])

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

    # --- SMART SELECTION LAYOUT ---
    col_search, col_clear = st.columns([5, 1])
    
    with col_search:
        search_query = st.text_input(
            "Filter", 
            key="inspector_search",
            placeholder=S_TXT["ph"], 
            label_visibility="collapsed"
        )
        
    with col_clear:
        st.button(S_TXT["clear"], type="secondary", width="stretch", on_click=clear_search)

    # Filter Logic
    if search_query:
        subset = filtered_df[
            filtered_df['display_title'].str.contains(search_query, case=False, na=False) |
            filtered_df['id'].str.contains(search_query, case=False, na=False)
        ]
        match_count = len(subset)
        if match_count == 0:
            st.warning(T["inspector_no_data"])
        else:
            st.caption(f"{match_count} matches found.")
    else:
        subset = filtered_df

    # Selectbox
    if not subset.empty:
        dataset_map = {row['id']: row['display_title'] for _, row in subset.iterrows()}
        
        # Use specific key to prevent tab switching on selection
        selected_id = st.selectbox(
            T["inspector_select"], 
            options=dataset_map.keys(), 
            format_func=lambda x: dataset_map[x],
            key="inspector_dataset_selector" 
        )

        # --- RECORD DISPLAY ---
        if selected_id:
            record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
            
            st.divider()
            
            # Header
            st.caption(T["inspector_ds_title"])
            st.markdown(f"**{record['display_title']}**")
            st.caption(f"ID: `{record['id']}`")

            st.divider()
            
            # Content Columns
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                st.markdown(f"**{T['metric_violations']}:**")
                if record['schema_violations_count'] > 0:
                    msgs = record.get('schema_violation_messages', [])
                    if isinstance(msgs, list):
                        for msg in msgs: st.error(f"• {msg}")
                else:
                    st.success(T.get("inspector_no_data", "No violations.")) # Reuse or add specific "No violations" string
                    
            with col_d2:
                st.markdown(f"**{T['inspector_details']}:**")
                
                if 'swiss_score' in record and record['swiss_score'] > 0:
                     st.info(f"**FAIRC Score:** {record['swiss_score']:.0f} / 405")
                     
                     st.markdown(f"""
                     * **Findability:** {record.get('findability_score', 0)}
                     * **Accessibility:** {record.get('accessibility_score', 0)}
                     * **Interoperability:** {record.get('interoperability_score', 0)}
                     * **Reusability:** {record.get('reusability_score', 0)}
                     * **Contextuality:** {record.get('contextuality_score', 0)}
                     """)
                else:
                     st.caption("Deep quality checks pending.")

            # --- NEW: IMPROVEMENT RECOMMENDATIONS ---
            st.divider()
            st.markdown(f"#### {T['inspector_improve_title']}")
            
            # 1. Convert Pandas Row back to Pydantic for Logic processing
            # We filter the dict to remove DB-only fields that might confuse the Pydantic model if strict
            try:
                # Convert Pandas Series to dict
                record_dict = record.to_dict()
                
                # Helper to map DB snake_case back to Input aliases if necessary, 
                # but DatasetInput is robust. We might need to map 'distributions' manually if it was JSON parsed.
                # NOTE: distributions are currently NOT fetched by the simple SELECT * FROM datasets in load_data
                # We need to fetch them if we want to run deep analysis on distributions
                
                # FIX: Fetch distributions for this dataset from the DB to accurately score
                engine = get_db_engine()
                dists_df = pd.read_sql(f"SELECT * FROM distributions WHERE dataset_id = '{record['id']}'", engine)
                
                # Map DB columns back to Input keys expected by DatasetInput (which uses aliases like dcat:accessURL)
                # OR simply create DistributionInput objects from the DF rows and attach to record_dict
                
                # The Pydantic model expects 'dcat:distribution'.
                # We need to reconstruct the list of dicts for distributions
                dist_list = []
                for _, d_row in dists_df.iterrows():
                    dist_obj = {
                        "dct:identifier": d_row['identifier'],
                        "dcat:accessURL": d_row['access_url'],
                        "dcat:downloadURL": d_row['download_url'],
                        "dct:format": d_row['format_type'],
                        "dcat:mediaType": d_row['media_type'],
                        "dct:license": d_row['license_id'],
                        # Inject statuses for scoring logic
                        "access_url_status": d_row['access_url_status'],
                        "download_url_status": d_row['download_url_status']
                    }
                    dist_list.append(dist_obj)
                
                record_dict['dcat:distribution'] = dist_list
                
                # Map other aliased fields if they are missing in record_dict (pandas uses DB col names)
                record_dict['dct:identifier'] = record_dict['id']
                record_dict['dct:title'] = record_dict['title']
                record_dict['dct:description'] = record_dict['description']
                record_dict['dcat:keyword'] = record_dict['keywords']
                record_dict['dcat:theme'] = record_dict['themes']
                record_dict['dct:publisher'] = record_dict['publisher']
                record_dict['dcat:contactPoint'] = record_dict['contact_point']
                record_dict['dct:issued'] = record_dict['issued']
                record_dict['dct:modified'] = record_dict['modified']
                record_dict['dct:accessRights'] = record_dict['access_rights']
                
                ds_input = DatasetInput(**record_dict)
                
                # 2. Run Analysis
                scorer = QualityScorer()
                gaps = scorer.analyze_scoring_gaps(ds_input)
                
                if not gaps:
                    st.balloons()
                    st.success(T['inspector_perfect_score'])
                else:
                    st.caption(T['inspector_improve_desc'])
                    for gap in gaps:
                        # Get translated message using the key from logic
                        msg = T.get(gap['msg_key'], gap['msg_key'])
                        pts = f"+{gap['points']}" if isinstance(gap['points'], int) else "Fix"
                        st.warning(f"**{gap['dim']}**: {msg} ({pts})")
                        
            except Exception as e:
                st.error(f"Could not generate recommendations: {e}")

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