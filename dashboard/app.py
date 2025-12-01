import streamlit as st
import pandas as pd
import altair as alt
import json
import markdown
import textwrap
import re
from sqlalchemy import create_engine
import sys
import os

# Adjust path to find src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dashboard.translations import TRANSLATIONS
from src.config import settings

st.set_page_config(page_title="BLW Metadata Dashboard", layout="wide", page_icon="🏆")

# --- CUSTOM UI HELPERS ---
def render_quality_card(title: str, content: str, level: str = "info"):
    """
    Renders a custom HTML card using the BLW color palette defined in style.css.
    
    Args:
        title: The header text.
        content: The body text (supports Markdown).
        level: 'high' (Red), 'med' (Orange), 'low' (Yellow), 'info' (Blue/Beige).
    """
    # Map levels to icons
    icon_map = {
        "high": "🚨",
        "med": "⚠️",
        "low": "💡",
        "info": "ℹ️"
    }
    icon = icon_map.get(level, "")
    
    # 1. CLEANUP: Remove indentation from the source string
    # This prevents the markdown parser from treating the text as a code block.
    clean_content = textwrap.dedent(content).strip()
    clean_content = re.sub(r'(\n)([*-] )', r'\n\n\2', clean_content)
    

    # 2. CONVERT: Markdown -> HTML
    content_html = markdown.markdown(clean_content)
    
    # 3. RENDER
    html = f"""
    <div class="blw-card {level}">
        <h4>{title}</h4>
        <div class="card-content">
            {content_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# 2. LOAD EXTERNAL CSS
def load_css(file_name):
    """Loads a CSS file relative to the current script."""
    current_dir = os.path.dirname(__file__)
    css_path = os.path.join(current_dir, file_name)
    
    try:
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {css_path}")

load_css("style.css")

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
        # 1. Fetch Datasets (Parent Table)
        df_ds = pd.read_sql("SELECT * FROM datasets", engine)
        
        # 2. Fetch Distributions (Child Table)
        df_dists = pd.read_sql("SELECT * FROM distributions", engine)
        
        # 3. Parse JSON columns in Datasets
        json_cols = ['title', 'description', 'keywords', 'themes', 'schema_violation_messages', 'quality_suggestions']
        for col in json_cols:
            if col in df_ds.columns:
                df_ds[col] = df_ds[col].apply(
                    lambda x: json.loads(x) if x and isinstance(x, str) else (x if isinstance(x, (dict, list)) else {})
                )
        
        # 4. Nest Distributions into Datasets
        if not df_dists.empty:
            # Group by dataset_id and convert the group to a list of dictionaries
            # This creates a Series where the index is 'dataset_id' and the value is [ {dist1}, {dist2} ]
            dists_grouped = df_dists.groupby('dataset_id').apply(
                lambda x: x.to_dict(orient='records')
            ).reset_index(name='distributions')
            
            # Merge this new 'distributions' column into the main dataframe
            # LEFT JOIN ensures we keep datasets that have 0 distributions
            df_final = pd.merge(df_ds, dists_grouped, left_on='id', right_on='dataset_id', how='left')
            
            # Cleanup: Replace NaN (for datasets with no dists) with empty lists []
            # Check for NaN using isinstance to avoid pandas errors
            df_final['distributions'] = df_final['distributions'].apply(
                lambda x: x if isinstance(x, list) else []
            )
            
            # Remove the extra joining column if present
            if 'dataset_id' in df_final.columns:
                df_final = df_final.drop(columns=['dataset_id'])
                
            return df_final
        else:
            # Fallback if distributions table is empty
            df_ds['distributions'] = [[] for _ in range(len(df_ds))]
            return df_ds

    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

def set_lang(code): st.session_state.lang = code
def clear_search(): st.session_state.inspector_search = ""

# --- HEADER & LANGUAGE ---
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
    render_quality_card("Error", T["inspector_no_data"], "high")
    st.stop()

df['display_title'] = df['title'].apply(lambda x: get_localized_text(x, lang_code))
filtered_df = df

# ==============================================================================
# Responsive Button Navigation Bar
# ==============================================================================

# 1. Initialize Active Tab State
if "active_tab_index" not in st.session_state:
    st.session_state.active_tab_index = 0

# 2. Define Options
tab_names = [T["tab_overview"], T["tab_inspector"], T["tab_help"]]

# 3. Layout: Constrain width first (Mimic Language Button behavior)
col_nav, col_spacer = st.columns([3, 2]) 

with col_nav:
    # 4. Divide the constrained area into equal slots for buttons
    nav_cols = st.columns(len(tab_names))
    
    for i, (col, name) in enumerate(zip(nav_cols, tab_names)):
        
        # Highlight the active tab with "primary" style
        button_type = "primary" if st.session_state.active_tab_index == i else "secondary"
        
        # Create button filling its column slot
        if col.button(name, key=f"nav_tab_{i}", type=button_type, use_container_width=True):
            st.session_state.active_tab_index = i
            st.rerun()

st.divider()

# ==============================================================================
# CONTENT RENDERING
# ==============================================================================

# --- TAB 1: OVERVIEW ---
if st.session_state.active_tab_index == 0:
    
    # 1. TOP: KEY METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric(T["metric_total"], len(filtered_df))
    c2.metric(T["metric_score"], f"{filtered_df['swiss_score'].mean():.0f}")
    c3.metric(T["metric_violations"], int(filtered_df['schema_violations_count'].sum()))
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    # --- LEFT: Score Distribution ---
    with col_chart1:
        st.markdown(f"#### {T['chart_score_dist']}")
        
        chart_data = filtered_df.sort_values(by="swiss_score", ascending=False).reset_index(drop=True)
        chart_data["rank"] = chart_data.index + 1

        chart_dist = alt.Chart(chart_data).mark_bar(
            color="#2f4356",    # BLW Blue
            stroke="white",     # Slice border
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
            height=220  # <--- Reduced Height to prevent visual dominance
        ).interactive()

        st.altair_chart(chart_dist, use_container_width=True)
        
    # --- RIGHT: Top Errors (Horizontal) ---
    with col_chart2:
        st.markdown(f"#### {T['chart_top_errors']}")
        
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
                color="#2f4356" 
            ).encode(
                x=alt.X('count:Q', title='Count', axis=alt.Axis(tickMinStep=1)),
                y=alt.Y(
                    'error_message:N', 
                    title=None, # Remove Y-title to save space for labels
                    sort='-x', 
                    axis=alt.Axis(labelLimit=250) # Limit label width to prevent overlap
                ),
                tooltip=[
                    alt.Tooltip('error_message', title='Error'),
                    alt.Tooltip('count', title='Count')
                ]
            ).properties(
                height=220 # <--- Matching Height
            ).interactive()

            st.altair_chart(chart_err, use_container_width=True)
        else: 
            render_quality_card("Info", "No validation errors found.", "info")

    st.divider()

    # 3. BOTTOM: WORKLIST DATAFRAME
    st.markdown(f"### {T['tab_overview']}")

    def categorize_severity(row):
        if row['schema_violations_count'] > 0:
            return T["severity_high"]
        elif row['swiss_score'] < 200:
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
        worklist_df[['severity', 'display_title', 'violations_display', 'swiss_score', 'id']],
        column_config={
            "severity": st.column_config.TextColumn(T["col_severity"]),
            "display_title": st.column_config.TextColumn(T["col_title"], width="medium"),
            "violations_display": st.column_config.TextColumn(T["col_violations"]),
            "swiss_score": st.column_config.ProgressColumn(
                T["col_score"], 
                format="%.0f", 
                min_value=0, 
                max_value=405,
                color="#2f4356" 
            ),
            "id": st.column_config.TextColumn(T["col_id"], width="small")
        },
        hide_index=True,
        width="stretch"
    )
# --- TAB 2: INSPECTOR ---
elif st.session_state.active_tab_index == 1:
    st.markdown(f"### {T['tab_inspector']}")
    
    # 1. Search & Filter
    col_search, col_clear = st.columns([5, 1])
    with col_search:
        search_query = st.text_input("Filter", key="inspector_search", placeholder=S_TXT["ph"], label_visibility="collapsed")
    with col_clear:
        st.button(S_TXT["clear"], type="secondary", width="stretch", on_click=clear_search)

    if search_query:
        subset = filtered_df[filtered_df['display_title'].str.contains(search_query, case=False, na=False) | 
                             filtered_df['id'].str.contains(search_query, case=False, na=False)]
    else:
        subset = filtered_df

    # 2. Dataset Selector
    if not subset.empty:
        dataset_map = {row['id']: row['display_title'] for _, row in subset.iterrows()}
        selected_id = st.selectbox(T["inspector_select"], options=dataset_map.keys(), format_func=lambda x: dataset_map[x], key="inspector_dataset_selector")

        if selected_id:
            record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
            
            # --- HEADER INFO ---
            st.divider()
            st.markdown(f"### {record['display_title']}")
            c_meta2, c_meta3 = st.columns([1, 1])
            
            c_meta2.caption(T["inspector_id"])
            c_meta2.code(record['id'])
            
            c_meta3.caption(T["inspector_overall_score"])
            # Large Score Badge
            score = record.get('swiss_score', 0)
            color = "red" if score < 100 else "orange" if score < 250 else "green"
            c_meta3.markdown(f":{color}[**{score:.0f}**] / 405")
            
            st.divider()
            
            # --- SECTION A: FAIRC SCORE BREAKDOWN ---
            # We keep this open as a visual dashboard summary
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

            # --- SECTION B: SCHEMA VIOLATIONS ---
            has_violations = record['schema_violations_count'] > 0
            # Auto-expand only if there are errors
            with st.expander(f"🚨 {T['sec_schema_violations']}", expanded=has_violations):
                if has_violations:
                    for msg in record.get('schema_violation_messages', []):
                        render_quality_card(T["msg_schema_violation"], msg, "high")
                else:
                    render_quality_card(T["msg_valid_title"], T["msg_valid_body"], "info")
            
            # --- SECTION C: DEEP LINK ANALYSIS ---
            dists = record.get('distributions', [])
            
            # Calculate if we should expand (if broken links exist)
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

                    # 1. Sort distributions into buckets
                    for dist in dists:
                        is_broken = False
                        
                        # Check Access URL
                        acc_url = dist.get('access_url')
                        acc_status = dist.get('access_url_status')
                        if acc_url and (not acc_status or not (200 <= acc_status < 400)):
                            is_broken = True
                        
                        # Check Download URL
                        dl_url = dist.get('download_url')
                        dl_status = dist.get('download_url_status')
                        if dl_url and (not dl_status or not (200 <= dl_status < 400)):
                            is_broken = True

                        if is_broken:
                            broken_dists.append(dist)
                        else:
                            healthy_dists.append(dist)

                    # 2. Render Logic
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
                        with st.expander(T["msg_view_healthy"].format(count=len(healthy_dists))):
                            for i, dist in enumerate(healthy_dists):
                                fmt = dist.get('format_type', T["lbl_unknown_fmt"])
                                
                                # 1. Distribution Title
                                st.markdown(f"**{i+1}. {fmt}**")
                                
                                # 2. Access URL Details
                                url_acc = dist.get('access_url')
                                status_acc = dist.get('access_url_status')
                                if url_acc:
                                    # Create a clickable link with the status code in a code badge
                                    badge = f":green[[HTTP {status_acc}]]" if status_acc else ""
                                    st.markdown(f"&nbsp;&nbsp; 🔗 **{T['lbl_access_url']}**: [{url_acc}]({url_acc}) {badge}")

                                # 3. Download URL Details (if distinct)
                                url_dl = dist.get('download_url')
                                status_dl = dist.get('download_url_status')
                                
                                # Only show download URL if it exists
                                if url_dl:
                                    badge = f":green[[HTTP {status_dl}]]" if status_dl else ""
                                    st.markdown(f"&nbsp;&nbsp; 📥 **{T['lbl_download_url']}**: [{url_dl}]({url_dl}) {badge}")
                                
                                # Add a small visual separator between distributions, but not after the last one
                                if i < len(healthy_dists) - 1:
                                    st.markdown("---")

            # --- SECTION D: SUGGESTIONS ---
            # Always expanded to encourage improvement
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

            # Raw Data
            with st.expander(T["inspector_raw"]):
                raw_view = record.to_dict()
                # Remove pandas specific artifacts if any
                if 'display_title' in raw_view: del raw_view['display_title']
                st.json(raw_view)

# --- TAB 3: HELP ---
elif st.session_state.active_tab_index == 2:
    st.markdown(f"#### {T['help_overview']}")
    st.markdown(T["help_intro"])
    
    with st.container():
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            render_quality_card(T['help_vio_title'], T["help_vio_desc"], "high")
        with col_v2:
            render_quality_card(T["help_goal"], T["help_vio_goal"], "high")

    st.divider()

    with st.container():
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            render_quality_card(T['help_score_title'], T["help_score_desc"], "low")
        with col_s2:
            render_quality_card(T["help_goal"], T["help_score_goal"], "low")

    st.markdown(f"#### {T['help_calc_title']}")
    
    def row(dim, crit_key, weight, def_key=None):
        definition = T[def_key] if def_key else ""
        return f"| **{dim}** | {T[crit_key]} | +{weight} | {definition} |"


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