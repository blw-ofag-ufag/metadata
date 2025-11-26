import streamlit as st
import pandas as pd
import json
from sqlalchemy import create_engine
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dashboard.translations import TRANSLATIONS
from src.config import settings

st.set_page_config(page_title="BLW Metadata Dashboard", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    div[data-testid="column"] { align-items: center; }
    div[data-testid="stButton"] button {
        white-space: nowrap !important;
        padding-left: 4px !important;
        padding-right: 4px !important;
        min-width: 0px !important;
    }
    div[data-testid="stButton"] button p { font-weight: bold; margin: 0px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_db_engine():
    return create_engine(settings.DB_URL)

def get_localized_text(data, lang_code: str) -> str:
    if not isinstance(data, dict): return str(data)
    return data.get(lang_code) or data.get("de") or next(iter(data.values()), "N/A")

@st.cache_data(ttl=600)
def load_data():
    engine = get_db_engine()
    try:
        df = pd.read_sql("SELECT * FROM datasets", engine)
        # ADDED: quality_suggestions to the list of JSON columns
        json_cols = ['title', 'description', 'keywords', 'themes', 'schema_violation_messages', 'quality_suggestions']
        for col in json_cols:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.loads(x) if x and isinstance(x, str) else (x if isinstance(x, (dict, list)) else {})
                )
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

if 'lang' not in st.session_state: st.session_state.lang = 'de'
if 'inspector_search' not in st.session_state: st.session_state.inspector_search = ""

def set_lang(code): st.session_state.lang = code
def clear_search(): st.session_state.inspector_search = ""

col_header, col_spacer, col_lang = st.columns([6, 0.5, 2.5])
with col_lang:
    b_de, b_fr, b_it, b_en = st.columns(4)
    if b_de.button("DE", type="primary" if st.session_state.lang == 'de' else "secondary", width="stretch"): set_lang('de'); st.rerun()
    if b_fr.button("FR", type="primary" if st.session_state.lang == 'fr' else "secondary", width="stretch"): set_lang('fr'); st.rerun()
    if b_it.button("IT", type="primary" if st.session_state.lang == 'it' else "secondary", width="stretch"): set_lang('it'); st.rerun()
    if b_en.button("EN", type="primary" if st.session_state.lang == 'en' else "secondary", width="stretch"): set_lang('en'); st.rerun()

lang_code = st.session_state.lang
T = TRANSLATIONS[lang_code]
S_TXT = {"de": {"ph": "Filter...", "clear": "X"}, "en": {"ph": "Filter...", "clear": "Clear"}}.get(lang_code, {"ph": "Filter...", "clear": "Clear"})

with col_header:
    st.title(T["app_title"])

df = load_data()
if df.empty:
    st.warning(T["inspector_no_data"])
    st.stop()

df['display_title'] = df['title'].apply(lambda x: get_localized_text(x, lang_code))
filtered_df = df

tab1, tab2, tab3, tab4 = st.tabs([T["tab_worklist"], T["tab_overview"], T["tab_inspector"], T["tab_help"]])

with tab1:
    st.markdown(f"### {T['tab_worklist']}")
    
    def categorize_severity(row):
        if row['schema_violations_count'] > 0:
            return T["severity_high"]
        elif row['swiss_score'] < 200: # Updated threshold for FAIRC scale (approx 50%)
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
    
    # CHANGED: Replaced 'input_quality_score' with 'swiss_score'
    st.dataframe(
        worklist_df[['severity', 'display_title', 'violations_display', 'swiss_score', 'id']],
        column_config={
            "severity": st.column_config.TextColumn(T["col_severity"]),
            "display_title": st.column_config.TextColumn(T["col_title"], width="medium"),
            "violations_display": st.column_config.TextColumn(T["col_violations"]),
            
            # CHANGED: Configured for 0-405 scale
            "swiss_score": st.column_config.ProgressColumn(
                T["col_score"], 
                format="%.0f", 
                min_value=0, 
                max_value=405
            ),
            "id": st.column_config.TextColumn(T["col_id"], width="small", help="DCAT Identifier")
        },
        hide_index=True,
        width="stretch"
    )

with tab2:
    st.markdown(f"### {T['tab_overview']}")
    c1, c2, c3 = st.columns(3)
    c1.metric(T["metric_total"], len(filtered_df))
    c2.metric(T["metric_score"], f"{filtered_df['swiss_score'].mean():.0f}")
    c3.metric(T["metric_violations"], int(filtered_df['schema_violations_count'].sum()))
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.caption(T["chart_score_dist"])
        st.bar_chart(filtered_df['swiss_score'])
    with col_chart2:
        st.caption(T["chart_top_errors"])
        all_errors = []
        if 'schema_violation_messages' in filtered_df.columns:
            for msgs in filtered_df['schema_violation_messages']:
                if isinstance(msgs, list): all_errors.extend(msgs)
        if all_errors: st.bar_chart(pd.Series(all_errors).value_counts().head(5))
        else: st.info("No validation errors found.")

with tab3:
    st.markdown(f"### {T['tab_inspector']}")
    col_search, col_clear = st.columns([5, 1])
    with col_search:
        search_query = st.text_input("Filter", key="inspector_search", placeholder=S_TXT["ph"], label_visibility="collapsed")
    with col_clear:
        st.button(S_TXT["clear"], type="secondary", width="stretch", on_click=clear_search)

    if search_query:
        subset = filtered_df[filtered_df['display_title'].str.contains(search_query, case=False, na=False) | filtered_df['id'].str.contains(search_query, case=False, na=False)]
    else:
        subset = filtered_df

    if not subset.empty:
        dataset_map = {row['id']: row['display_title'] for _, row in subset.iterrows()}
        selected_id = st.selectbox(T["inspector_select"], options=dataset_map.keys(), format_func=lambda x: dataset_map[x], key="inspector_dataset_selector")

        if selected_id:
            record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
            st.divider()
            st.caption("Dataset ID")
            st.markdown(f"`{record['id']}`")
            st.caption("Dataset Title")
            st.markdown(f"**{record['display_title']}**")
            st.divider()
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("**Schema Violations:**")
                if record['schema_violations_count'] > 0:
                    for msg in record.get('schema_violation_messages', []): st.error(f"• {msg}")
                else:
                    st.success("No violations.")
            with col_d2:
                st.markdown("**Quality Details:**")
                st.info(f"**FAIRC Score:** {record.get('swiss_score', 0):.0f} / 405")
                st.markdown(f"""
                * **Findability:** {record.get('findability_score', 0)}
                * **Accessibility:** {record.get('accessibility_score', 0)}
                * **Interoperability:** {record.get('interoperability_score', 0)}
                * **Reusability:** {record.get('reusability_score', 0)}
                * **Contextuality:** {record.get('contextuality_score', 0)}
                """)

            # --- IMPROVEMENT OPPORTUNITIES ---
            st.markdown("### 🚀 " + ("Improvement Opportunities" if lang_code == "en" else "Verbesserungspotenzial"))
            st.caption("Fulfill the following criteria to maximize your score:")
            
            suggestions = record.get('quality_suggestions', [])
            if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                for sug in suggestions:
                    # Logic: Get translation for key, fallback to key itself
                    dim = sug.get("dimension", "General")
                    key = sug.get("key", "")
                    pts = sug.get("points", 0)
                    text = T.get(key, key) # Try to get translation
                    
                    st.warning(f"**{dim}**: {text} (+{pts})")
            else:
                if record.get('swiss_score', 0) >= 405:
                    st.balloons()
                    st.success("Perfect Score! 🏆")
                else:
                    st.info("No specific suggestions available.")

            with st.expander(T["inspector_raw"]):
                raw_view = record.to_dict()
                for k in ['display_title', 'severity']: 
                    if k in raw_view: del raw_view[k]
                st.json(raw_view)

with tab4:
    st.markdown(f"### {T['tab_help']}")
    st.info(T["help_intro"])
    
    # -----------------------------------------------------------------------
    # SECTION 1: MANDATORY VIOLATIONS
    # -----------------------------------------------------------------------
    # Removed spacer <br> to ensure alignment
    with st.container():
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            st.error(f"#### {T['help_vio_title']}")
            st.markdown(T["help_vio_desc"])
        with col_v2:
            st.error(T["help_vio_goal"], icon="🎯")

    st.divider()

    # -----------------------------------------------------------------------
    # SECTION 2: QUALITY SCORING (FAIRC) & CALCULATOR
    # -----------------------------------------------------------------------
    # Removed spacer <br> to ensure alignment
    with st.container():
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            st.success(f"#### {T['help_score_title']}")
            st.markdown(T["help_score_desc"])
        with col_s2:
            st.success(T["help_score_goal"], icon="🎯")

        st.markdown(f"#### {T['help_calc_title']}")
        
        # Helper to create table rows with optional definitions
        def row(dim, crit_key, weight, def_key=None):
            definition = T[def_key] if def_key else ""
            return f"| **{dim}** | {T[crit_key]} | +{weight} | {definition} |"

        # Build the table markdown
        table_md = f"""
| {T['help_table_dim']} | {T['help_table_crit']} | {T['help_table_pts']} | {T['help_table_info']} |
| :--- | :--- | :--- | :--- |
{row('Findability', 'crit_keywords', settings.WEIGHT_FINDABILITY_KEYWORDS)}
{row('', 'crit_themes', settings.WEIGHT_FINDABILITY_CATEGORIES)}
{row('', 'crit_geo', settings.WEIGHT_FINDABILITY_GEO_SEARCH)}
{row('', 'crit_time', settings.WEIGHT_FINDABILITY_TIME_SEARCH)}
{row('Accessibility', 'crit_access', settings.WEIGHT_ACCESSIBILITY_ACCESS_URL, 'def_http')}
{row('', 'crit_download_valid', settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID, 'def_http')}
{row('', 'crit_download', settings.WEIGHT_ACCESSIBILITY_DOWNLOAD_URL)}
{row('Interoperability', 'crit_machine', settings.WEIGHT_INTEROP_MACHINE_READABLE, 'def_machine')}
{row('', 'crit_openfmt', settings.WEIGHT_INTEROP_NON_PROPRIETARY, 'def_open')}
{row('', 'crit_dcat', settings.WEIGHT_INTEROP_DCAT_AP)}
{row('', 'crit_format', settings.WEIGHT_INTEROP_FORMAT)}
{row('', 'crit_media', settings.WEIGHT_INTEROP_MEDIA_TYPE)}
{row('', 'crit_vocab', settings.WEIGHT_INTEROP_VOCABULARY)}
{row('Reusability', 'crit_access_vocab', settings.WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB, 'def_access')}
{row('', 'crit_lic_vocab', settings.WEIGHT_REUSE_LICENSE_VOCAB, 'def_license')}
{row('', 'crit_license', settings.WEIGHT_REUSE_LICENSE)}
{row('', 'crit_access_res', settings.WEIGHT_REUSE_ACCESS_RESTRICTION)}
{row('', 'crit_contact', settings.WEIGHT_REUSE_CONTACT_POINT)}
{row('', 'crit_publisher', settings.WEIGHT_REUSE_PUBLISHER)}
{row('Contextuality', 'crit_rights', settings.WEIGHT_CONTEXT_RIGHTS)}
{row('', 'crit_filesize', settings.WEIGHT_CONTEXT_FILE_SIZE)}
{row('', 'crit_issue', settings.WEIGHT_CONTEXT_ISSUE_DATE)}
{row('', 'crit_mod', settings.WEIGHT_CONTEXT_MODIFICATION_DATE)}
        """
        
        st.markdown(table_md)