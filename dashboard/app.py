import streamlit as st
import pandas as pd
import altair as alt
import json
import markdown
import textwrap
import re
import os
from translations import TRANSLATIONS

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================
st.set_page_config(page_title="BLW Metadata Dashboard", layout="wide", page_icon="🏆")

# We hardcode weights here so the "Help" tab calculator works without importing src.config
WEIGHTS = {
    "WEIGHT_FINDABILITY_KEYWORDS": 30,
    "WEIGHT_FINDABILITY_CATEGORIES": 30,
    "WEIGHT_FINDABILITY_GEO_SEARCH": 20,
    "WEIGHT_FINDABILITY_TIME_SEARCH": 20,
    "WEIGHT_ACCESSIBILITY_ACCESS_URL": 50,
    "WEIGHT_ACCESSIBILITY_DOWNLOAD_URL": 20,
    "WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID": 30,
    "WEIGHT_INTEROP_FORMAT": 20,
    "WEIGHT_INTEROP_MEDIA_TYPE": 10,
    "WEIGHT_INTEROP_VOCABULARY": 10,
    "WEIGHT_INTEROP_NON_PROPRIETARY": 20,
    "WEIGHT_INTEROP_MACHINE_READABLE": 20,
    "WEIGHT_INTEROP_DCAT_AP": 30,
    "WEIGHT_REUSE_LICENSE": 20,
    "WEIGHT_REUSE_LICENSE_VOCAB": 10,
    "WEIGHT_REUSE_ACCESS_RESTRICTION": 10,
    "WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB": 5,
    "WEIGHT_REUSE_CONTACT_POINT": 20,
    "WEIGHT_REUSE_PUBLISHER": 10,
    "WEIGHT_CONTEXT_RIGHTS": 5,
    "WEIGHT_CONTEXT_FILE_SIZE": 5,
    "WEIGHT_CONTEXT_ISSUE_DATE": 5,
    "WEIGHT_CONTEXT_MODIFICATION_DATE": 5
}

# ==============================================================================
# 2. UTILITIES
# ==============================================================================

def render_quality_card(title: str, content: str, level: str = "info"):
    """
    Renders a custom HTML card using the BLW color palette defined in style.css.
    """
    icon_map = {
        "high": "🚨",
        "med": "⚠️",
        "low": "💡",
        "info": "ℹ️"
    }
    icon = icon_map.get(level, "")
    
    clean_content = textwrap.dedent(content).strip()
    clean_content = re.sub(r'(\n)([*-] )', r'\n\n\2', clean_content)
    content_html = markdown.markdown(clean_content)
    
    html = f"""
    <div class="blw-card {level}">
        <h4>{title}</h4>
        <div class="card-content">
            {content_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def load_css(file_name):
    current_dir = os.path.dirname(__file__)
    css_path = os.path.join(current_dir, file_name)
    try:
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {css_path}")

load_css("style.css")

def get_localized_text(data, lang_code: str) -> str:
    if not isinstance(data, dict): return str(data)
    return data.get(lang_code) or data.get("de") or next(iter(data.values()), "N/A")

# ==============================================================================
# 3. DATA LOADING (LAZY & OPTIMIZED)
# ==============================================================================

@st.cache_data(ttl=600)
def load_summary_data():
    """
    EAGER LOAD: Loads immediately on startup.
    Contains ONLY what is needed for the main table (ID, Title, Score).
    """
    json_path = "data_summary.json"
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), "data_summary.json")

    if not os.path.exists(json_path):
        return pd.DataFrame()

    try:
        return pd.read_json(json_path)
    except Exception as e:
        st.error(f"Error loading summary data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_all_details_cached():
    """
    LAZY LOAD: loads the ENTIRE details map into memory ONCE.
    We cache this function so subsequent lookups are instant.
    """
    json_path = "data_details.json"
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), "data_details.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading details file: {e}")
        return {}

def get_dataset_details(dataset_id: str):
    """
    Accessor function that calls the cached loader.
    """
    all_details = load_all_details_cached()
    return all_details.get(dataset_id, None)

# ==============================================================================
# 4. UI LOGIC
# ==============================================================================

if 'lang' not in st.session_state: st.session_state.lang = 'de'
if 'inspector_search' not in st.session_state: st.session_state.inspector_search = ""

def set_lang(code): st.session_state.lang = code
def clear_search(): st.session_state.inspector_search = ""

# --- HEADER & LANGUAGE ---
col_header, col_spacer, col_lang = st.columns([6, 0.5, 2.5])
with col_lang:
    b_de, b_fr, b_it, b_en = st.columns(4)
    if b_de.button("DE", type="primary" if st.session_state.lang == 'de' else "secondary", use_container_width=True): set_lang('de'); st.rerun()
    if b_fr.button("FR", type="primary" if st.session_state.lang == 'fr' else "secondary", use_container_width=True): set_lang('fr'); st.rerun()
    if b_it.button("IT", type="primary" if st.session_state.lang == 'it' else "secondary", use_container_width=True): set_lang('it'); st.rerun()
    if b_en.button("EN", type="primary" if st.session_state.lang == 'en' else "secondary", use_container_width=True): set_lang('en'); st.rerun()

lang_code = st.session_state.lang
T = TRANSLATIONS[lang_code]
S_TXT = {"de": {"ph": "Filter...", "clear": "X"}, "en": {"ph": "Filter...", "clear": "Clear"}}.get(lang_code, {"ph": "Filter...", "clear": "Clear"})

with col_header:
    st.title(T["app_title"])

# LOAD SUMMARY (Fast)
df = load_summary_data()

if df.empty:
    st.warning("⚠️ No data loaded. Please ensure 'data_summary.json' is generated.")
    st.stop()

# Compute display title for the summary table
df['display_title'] = df['title'].apply(lambda x: get_localized_text(x, lang_code))
filtered_df = df

# ==============================================================================
# Responsive Button Navigation Bar
# ==============================================================================

if "active_tab_index" not in st.session_state:
    st.session_state.active_tab_index = 0

tab_names = [T["tab_overview"], T["tab_inspector"], T["tab_help"]]

col_nav, col_spacer = st.columns([3, 2]) 

with col_nav:
    nav_cols = st.columns(len(tab_names))
    
    for i, (col, name) in enumerate(zip(nav_cols, tab_names)):
        button_type = "primary" if st.session_state.active_tab_index == i else "secondary"
        if col.button(name, key=f"nav_tab_{i}", type=button_type, use_container_width=True):
            st.session_state.active_tab_index = i
            st.rerun()

st.divider()

# ==============================================================================
# CONTENT RENDERING
# ==============================================================================

# --- TAB 1: OVERVIEW ---
if st.session_state.active_tab_index == 0:
    
    c1, c2, c3 = st.columns(3)
    c1.metric(T["metric_total"], len(filtered_df))
    c2.metric(T["metric_score"], f"{filtered_df['swiss_score'].mean():.0f}")
    c3.metric(T["metric_violations"], int(filtered_df['schema_violations_count'].sum()))
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    # --- LEFT: Score Distribution ---
    with col_chart1:
        h_col, p_col = st.columns([5, 1])
        h_col.markdown(f"#### {T['chart_score_dist']}")
        with p_col:
            with st.popover("ℹ️", use_container_width=False):
                st.markdown(T['help_score_desc'])
        
        chart_data = filtered_df.sort_values(by="swiss_score", ascending=False).reset_index(drop=True)
        chart_data["rank"] = chart_data.index + 1

        chart_dist = alt.Chart(chart_data).mark_bar(
            color="#1c83e1",
            stroke="white",
            strokeWidth=0.2     
        ).encode(
            x=alt.X('rank:Q', title='Dataset Rank', axis=alt.Axis(tickMinStep=1, grid=False), scale=alt.Scale(domainMin=0) ),
            y=alt.Y('swiss_score:Q', title='FAIRC Score', scale=alt.Scale(domainMin=0, domainMax=420)),
            tooltip=[
                alt.Tooltip('rank', title='Rank'),
                alt.Tooltip('display_title', title=T["col_title"]),
                alt.Tooltip('swiss_score', title='FAIRC Score')
            ]
        ).properties(
            height=220
        ).interactive()

        st.altair_chart(chart_dist, use_container_width=True) 

    # --- RIGHT: Top Errors (Horizontal) ---
    with col_chart2:
        h_col, p_col = st.columns([5, 1])
        h_col.markdown(f"#### {T['chart_top_errors']}")
        with p_col:
            with st.popover("ℹ️", use_container_width=False):
                st.markdown(T['help_vio_desc'])
        
        all_errors = []
        if 'schema_violation_messages' in filtered_df.columns:
            for msgs in filtered_df['schema_violation_messages']:
                if isinstance(msgs, list): 
                    all_errors.extend(msgs)
        
        if all_errors: 
            error_counts = pd.Series(all_errors).value_counts().reset_index()
            error_counts.columns = ["error_message", "count"]
            top_errors = error_counts.head(5)

            chart_err = alt.Chart(top_errors).mark_bar(
                color="#1c83e1" 
            ).encode(
                x=alt.X('count:Q', title='Count', axis=alt.Axis(tickMinStep=1)),
                y=alt.Y(
                    'error_message:N', 
                    title=None,
                    sort='-x', 
                    axis=alt.Axis(labelLimit=250)
                ),
                tooltip=[
                    alt.Tooltip('error_message', title='Error'),
                    alt.Tooltip('count', title='Count')
                ]
            ).properties(
                height=220
            ).interactive()

            st.altair_chart(chart_err, use_container_width=True)
        else: 
            render_quality_card("Info", "No validation errors found.", "info")

    st.divider()

    # 3. BOTTOM: WORKLIST DATAFRAME
    st.markdown(f"### {T['tab_overview']}")

    def categorize_severity_visual(row):
        if row['schema_violations_count'] > 0:
            return f"🔴 {T['severity_high']}" 
        elif row['swiss_score'] < 200:
            return f"🟠 {T['severity_med']}" 
        return f"🔵 {T['severity_low']}" 

    def format_violations(count):
        if count == 0:
            return None 
        return f"{count}"

    worklist_df = filtered_df.copy()
    worklist_df['severity_display'] = worklist_df.apply(categorize_severity_visual, axis=1)
    worklist_df['violations_display'] = worklist_df['schema_violations_count'].apply(format_violations)

    worklist_df['sev_rank'] = worklist_df['schema_violations_count'].apply(lambda x: 0 if x > 0 else 2)
    worklist_df.loc[(worklist_df['sev_rank'] == 2) & (worklist_df['swiss_score'] < 200), 'sev_rank'] = 1
    
    worklist_df = worklist_df.sort_values(by=['sev_rank', 'swiss_score'], ascending=[True, True])

    selection = st.dataframe(
        worklist_df[['display_title', 'swiss_score', 'violations_display', 'severity_display', 'id']],
        column_config={
            "display_title": st.column_config.TextColumn(
                T["col_title"], 
                width="large", 
                help="Dataset Title"
            ),
            "swiss_score": st.column_config.ProgressColumn(
                f"{T['col_score']} ℹ️", 
                format="%.0f", 
                min_value=0, 
                max_value=405,
                width="medium",
                help=T.get("tooltip_score", "") 
            ),
            "violations_display": st.column_config.TextColumn(
                f"{T['col_violations']} ℹ️", 
                width="small",
                help=T.get("tooltip_violations", "") 
            ),
            "severity_display": st.column_config.TextColumn(
                f"{T['col_severity']} ℹ️", 
                width="small",
                help=T.get("tooltip_severity", "") 
            ),
            "id": st.column_config.TextColumn(
                T["col_id"], 
                width="small",
                help="Internal Identifier (Copyable)"
            )
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun", 
        selection_mode="single-row", 
        key="overview_worklist" 
    )

    if len(selection.selection.rows) > 0:
        selected_row_index = selection.selection.rows[0]
        selected_id = worklist_df.iloc[selected_row_index]['id']
        st.session_state.active_tab_index = 1
        st.session_state.inspector_search = selected_id
        st.rerun()

# --- TAB 2: INSPECTOR ---
elif st.session_state.active_tab_index == 1:
    st.markdown(f"### {T['tab_inspector']}")
    
    col_search, col_clear = st.columns([9, 1], gap="small")
    
    with col_search:
        search_query = st.text_input(
            "Filter", 
            key="inspector_search", 
            placeholder=S_TXT["ph"], 
            label_visibility="collapsed"
        )
        
    with col_clear:
        st.button(
            "✕", 
            type="secondary", 
            on_click=clear_search,
            help="Clear filter",
            key="btn_clear_search" 
        )

    if search_query:
        subset = filtered_df[filtered_df['display_title'].str.contains(search_query, case=False, na=False) | filtered_df['id'].str.contains(search_query, case=False, na=False)]
    else:
        subset = filtered_df

    if not subset.empty:
        dataset_map = {row['id']: row['display_title'] for _, row in subset.iterrows()}
        selected_id = st.selectbox(T["inspector_select"], options=dataset_map.keys(), format_func=lambda x: dataset_map[x], key="inspector_dataset_selector")

        if selected_id:
            # --- LAZY LOAD: FETCH DETAILS ---
            with st.spinner(T.get("loading_details", "Loading details...")):
                record = get_dataset_details(selected_id)
            
            if not record:
                st.error("Could not load details for this dataset.")
                st.stop()
            
            
            record['display_title'] = get_localized_text(record.get('title'), lang_code)
            
            st.divider()
            st.markdown(f"### {record['display_title']}")
            c_meta2, c_meta3 = st.columns([1, 1])
            
            c_meta2.caption(T["inspector_id"])
            c_meta2.code(record['id'])
            
            c_meta3.caption(T["inspector_overall_score"])
            score = record.get('swiss_score', 0)
            color = "red" if score < 100 else "orange" if score < 250 else "green"
            c_meta3.markdown(f":{color}[**{score:.0f}**] / 405")
            
            st.divider()
            
            with st.expander(f"📊 {T['inspector_details']}", expanded=True):
                cols_scores = st.columns(5)
                dims = [
                    ("Findability", 'findability_score', 100),
                    ("Accessibility", 'accessibility_score', 100),
                    ("Interoperability", 'interoperability_score', 110),
                    ("Reusability", 'reusability_score', 75),
                    ("Contextuality", 'contextuality_score', 20)
                ]
                
                for col, (label, key, max_val) in zip(cols_scores, dims):
                    val = record.get(key, 0)
                    col.progress(min(val / max_val, 1.0))
                    col.caption(f"**{label}**")
                    col.markdown(f"{val:.0f} pts")

            has_violations = record.get('schema_violations_count', 0) > 0
            with st.expander(f"🚨 {T['sec_schema_violations']}", expanded=has_violations):
                if has_violations:
                    for msg in record.get('schema_violation_messages', []):
                        render_quality_card(T["msg_schema_violation"], msg, "high")
                else:
                    render_quality_card(T["msg_valid_title"], T["msg_valid_body"], "info")
            
            dists = record.get('distributions', [])
            has_broken_links = False
            if dists:
                for d in dists:
                    a_s = d.get('access_url_status')
                    d_s = d.get('download_url_status')
                    if (d.get('access_url') and (not a_s or not (200 <= a_s < 400))) or \
                       (d.get('download_url') and (not d_s or not (200 <= d_s < 400))):
                        has_broken_links = True
                        break
            
            with st.expander(f"🔗 {T['sec_link_health']}", expanded=has_broken_links):
                if not dists:
                    st.info(T["msg_no_dists"])
                else:
                    broken_dists = []
                    healthy_dists = []

                    for dist in dists:
                        is_broken = False
                        acc_url = dist.get('access_url')
                        acc_status = dist.get('access_url_status')
                        if acc_url and (not acc_status or not (200 <= acc_status < 400)):
                            is_broken = True
                        
                        dl_url = dist.get('download_url')
                        dl_status = dist.get('download_url_status')
                        if dl_url and (not dl_status or not (200 <= dl_status < 400)):
                            is_broken = True

                        if is_broken:
                            broken_dists.append(dist)
                        else:
                            healthy_dists.append(dist)

                    if not broken_dists:
                        render_quality_card(T["msg_all_ok_title"], T["msg_all_ok_body"].format(count=len(healthy_dists)), "low")
                    else:
                        st.error(T["msg_broken_detected"].format(count=len(broken_dists)))
                        for i, dist in enumerate(broken_dists):
                            fmt = dist.get('format_type', T["lbl_unknown_fmt"])
                            acc_s = dist.get('access_url_status')
                            dl_s = dist.get('download_url_status')
                            
                            with st.container(border=True):
                                st.markdown(f"**❌ {fmt}**")
                                if dist.get('access_url') and (not acc_s or not (200 <= acc_s < 400)):
                                    st.markdown(f"- **{T['lbl_access_url']}:** `HTTP {acc_s or 'Err'}`")
                                    st.caption(f"[{dist.get('access_url')}]({dist.get('access_url')})")
                                if dist.get('download_url') and (not dl_s or not (200 <= dl_s < 400)):
                                    st.markdown(f"- **{T['lbl_download_url']}:** `HTTP {dl_s or 'Err'}`")
                                    st.caption(f"[{dist.get('download_url')}]({dist.get('download_url')})")

                    if healthy_dists:
                        
                        if st.checkbox(T["msg_view_healthy"].format(count=len(healthy_dists)), key=f"toggle_healthy_{selected_id}"):
                            for i, dist in enumerate(healthy_dists):
                                fmt = dist.get('format_type', T["lbl_unknown_fmt"])
                                st.markdown(f"**{i+1}. {fmt}**")
                                
                                url_acc = dist.get('access_url')
                                status_acc = dist.get('access_url_status')
                                if url_acc:
                                    badge = f":green[[HTTP {status_acc}]]" if status_acc else ""
                                    st.markdown(f"&nbsp;&nbsp; 🔗 **{T['lbl_access_url']}**: [{url_acc}]({url_acc}) {badge}")

                                url_dl = dist.get('download_url')
                                status_dl = dist.get('download_url_status')
                                if url_dl:
                                    badge = f":green[[HTTP {status_dl}]]" if status_dl else ""
                                    st.markdown(f"&nbsp;&nbsp; 📥 **{T['lbl_download_url']}**: [{url_dl}]({url_dl}) {badge}")
                                
                                if i < len(healthy_dists) - 1:
                                    st.markdown("---")

            with st.expander(f"🚀 {T['inspector_improvement']}", expanded=True):
                suggestions = record.get('quality_suggestions', [])
                if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                    for sug in suggestions:
                        dim = sug.get("dimension", "General")
                        key = sug.get("key", "")
                        pts = sug.get("points", 0)
                        text = T.get(key, key)
                        severity = "med" if pts >= 20 else "low"
                        render_quality_card(f"{dim} (+{pts} pts)", text, severity)
                else:
                    if score >= 405:
                        st.balloons()
                        render_quality_card(T["msg_perfect_title"], T["msg_perfect_body"], "info")
                    else:
                        render_quality_card(T["msg_info_title"], T["msg_no_sug_body"], "info")

            with st.expander(T["inspector_raw"]):
                raw_view = record.copy()
                if 'display_title' in raw_view: del raw_view['display_title']
                st.json(raw_view)

elif st.session_state.active_tab_index == 2:
    
    st.markdown(f"### {T['tab_help']}")
    st.markdown(T["help_intro"])
    
    # --- EXPANDER 1: CONCEPTS (Violations vs Score) ---
    with st.expander(f"ℹ️ {T['help_overview']} & {T['help_goal']}", expanded=False):
        
        # Card 1: Violations
        with st.container():
            col_v1, col_v2 = st.columns([2, 1])
            with col_v1:
                render_quality_card(T['help_vio_title'], T["help_vio_desc"], "high")
            with col_v2:
                render_quality_card(T["help_goal"], T["help_vio_goal"], "high")

        st.divider()

        # Card 2: Quality Score
        with st.container():
            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                render_quality_card(T['help_score_title'], T["help_score_desc"], "low")
            with col_s2:
                render_quality_card(T["help_goal"], T["help_score_goal"], "low")

    # --- EXPANDER 2: SEVERITY LEGEND ---
    with st.expander(T['help_sev_title'], expanded=False):
        st.markdown(T['help_sev_desc'])
        
        severity_table = f"""
| | {T['col_severity']} | {T['help_table_info']} |
| :--- | :--- | :--- |
| 🔴 | **{T['severity_high']}** | {T['help_sev_high']} |
| 🟠 | **{T['severity_med']}** | {T['help_sev_med']} |
| 🔵 | **{T['severity_low']}** | {T['help_sev_low']} |
"""
        st.markdown(severity_table)

    # --- EXPANDER 3: DETAILED CALCULATOR (Collapsed by default) ---
    with st.expander(T['help_calc_title'], expanded=False):
        
        def row(dim, crit_key, weight_key, def_key=None):
            # MODIFIED: Look up from local WEIGHTS dict instead of src.config
            w = WEIGHTS.get(weight_key, 0)
            definition = T[def_key] if def_key else ""
            return f"| **{dim}** | {T[crit_key]} | +{w} | {definition} |"

        table_md = f"""
| {T['help_table_dim']} | {T['help_table_crit']} | {T['help_table_pts']} | {T['help_table_info']} |
| :--- | :--- | :--- | :--- |
{row('Findability', 'crit_keywords', 'WEIGHT_FINDABILITY_KEYWORDS')}
{row('', 'crit_themes', 'WEIGHT_FINDABILITY_CATEGORIES')}
{row('', 'crit_geo', 'WEIGHT_FINDABILITY_GEO_SEARCH')}
{row('', 'crit_time', 'WEIGHT_FINDABILITY_TIME_SEARCH')}
{row('Accessibility', 'crit_access', 'WEIGHT_ACCESSIBILITY_ACCESS_URL', 'def_http')}
{row('', 'crit_download_valid', 'WEIGHT_ACCESSIBILITY_DOWNLOAD_URL_VALID', 'def_http')}
{row('', 'crit_download', 'WEIGHT_ACCESSIBILITY_DOWNLOAD_URL')}
{row('Interoperability', 'crit_machine', 'WEIGHT_INTEROP_MACHINE_READABLE', 'def_machine')}
{row('', 'crit_openfmt', 'WEIGHT_INTEROP_NON_PROPRIETARY', 'def_open')}
{row('', 'crit_dcat', 'WEIGHT_INTEROP_DCAT_AP')}
{row('', 'crit_format', 'WEIGHT_INTEROP_FORMAT')}
{row('', 'crit_media', 'WEIGHT_INTEROP_MEDIA_TYPE')}
{row('', 'crit_vocab', 'WEIGHT_INTEROP_VOCABULARY')}
{row('Reusability', 'crit_access_vocab', 'WEIGHT_REUSE_ACCESS_RESTRICTION_VOCAB', 'def_access')}
{row('', 'crit_lic_vocab', 'WEIGHT_REUSE_LICENSE_VOCAB', 'def_license')}
{row('', 'crit_license', 'WEIGHT_REUSE_LICENSE')}
{row('', 'crit_access_res', 'WEIGHT_REUSE_ACCESS_RESTRICTION')}
{row('', 'crit_contact', 'WEIGHT_REUSE_CONTACT_POINT')}
{row('', 'crit_publisher', 'WEIGHT_REUSE_PUBLISHER')}
{row('Contextuality', 'crit_rights', 'WEIGHT_CONTEXT_RIGHTS')}
{row('', 'crit_filesize', 'WEIGHT_CONTEXT_FILE_SIZE')}
{row('', 'crit_issue', 'WEIGHT_CONTEXT_ISSUE_DATE')}
{row('', 'crit_mod', 'WEIGHT_CONTEXT_MODIFICATION_DATE')}
        """
        st.markdown(table_md)