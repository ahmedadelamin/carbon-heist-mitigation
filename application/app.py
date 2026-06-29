import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# PAGE CONFIGURATION Using CSS
# ==========================================
st.set_page_config(
    page_title="ESG & Carbon Mitigation Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded" 
)

COLOR_GREEN = "#10B981"  
COLOR_RED = "#EF4444"    
COLOR_ORANGE = "#F59E0B" 
COLOR_BLUE = "#3B82F6"   
COLOR_BG = "#0f172a"     
COLOR_CARD = "#1e293b"   

st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; color: #f8fafc; }}
    
    /* KPI Cards */
    .kpi-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 2rem;
    }}
    .kpi-card {{
        background-color: {COLOR_CARD};
        border-radius: 12px;
        padding: 1.5rem;
        flex: 1;
        min-width: 150px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-top: 4px solid {COLOR_BLUE};
    }}
    .kpi-card.risk {{ border-top-color: {COLOR_RED}; }}
    .kpi-card.good {{ border-top-color: {COLOR_GREEN}; }}
    .kpi-title {{ font-size: 0.875rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem; }}
    .kpi-value {{ font-size: 1.75rem; font-weight: 700; color: #f8fafc; }}
    
    h1, h2, h3 {{ color: #f8fafc !important; font-weight: 600; }}
    
    /* Image styling */
    .header-image {{ border-radius: 12px; margin-bottom: 1rem; object-fit: cover; width: 100%; height: 180px; opacity: 0.8; }}
    
    /* Insight Panel tweaks */
    .streamlit-expanderHeader {{ color: #94a3b8 !important; font-weight: 500; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATA HANDLING 
# ==========================================
@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "results.csv"
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        st.error("Data file not found. Please ensure 'results.csv' is in the directory.")
        st.stop()

    numeric_targets = [
        "Total GHG Emissions (Metric Tons CO2e)", "Net Emissions (Metric Tons CO2e)",
        "Base LL97 Penalty", "ENERGY STAR Score", "Building Age", "Year Built",
        "Total GHG Emissions Intensity (kgCO2e/ft²)", 
        "Avoided Emissions - Onsite and Offsite Green Power (Metric Tons CO2e)",
        "Electricity Use - Grid Purchase (kBtu)", "Natural Gas Use (kBtu)",
        "District Steam Use (kBtu)", "Fuel Oil #2 Use (kBtu)", "Diesel #2 Use (kBtu)"
    ]
    
    for col in numeric_targets:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Recalculate LL97 Penalty on Total GHG (not just excess)
    if "Total GHG Emissions (Metric Tons CO2e)" in df.columns:
        df["Base LL97 Penalty"] = df["Total GHG Emissions (Metric Tons CO2e)"] * 268

    if "Year Built" in df.columns and "Building Age" not in df.columns:
        df["Building Age"] = 2026 - df["Year Built"]
        
    if "Year Built" in df.columns:
        df["Decade Built"] = (df["Year Built"] // 10) * 10
        
    return df

raw_df = load_data()

C_NAME = "Property Name"
C_GHG = "Total GHG Emissions (Metric Tons CO2e)"
C_NET = "Net Emissions (Metric Tons CO2e)"
C_PENALTY = "Base LL97 Penalty"
C_SCORE = "ENERGY STAR Score"
C_INTENSITY = "Total GHG Emissions Intensity (kgCO2e/ft²)"
C_AVOIDED = "Avoided Emissions - Onsite and Offsite Green Power (Metric Tons CO2e)" # <--- ADD THIS LINE
C_TYPE = "Primary Property Type - Portfolio Manager-Calculated"
C_BORO = "Borough"
C_CITY = "City"
C_AGE = "Building Age"
C_DECADE = "Decade Built"
C_ALERTS = "Alerts"
C_OCCUPANCY = "Occupancy"
C_CONSTRUCTION = "Construction Status"

# ==========================================
# SIDEBAR & ADVANCED FILTERS
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?q=80&w=600&auto=format&fit=crop", caption="ESG Data Hub")
st.sidebar.title("🌍 Global Filters")


with st.sidebar.expander("📍 Location Filters", expanded=False):
    sel_cities = st.multiselect("City", raw_df[C_CITY].dropna().unique() if C_CITY in raw_df.columns else [])
    sel_boros = st.multiselect("Borough", raw_df[C_BORO].dropna().unique() if C_BORO in raw_df.columns else [])

with st.sidebar.expander("🏢 Property Details", expanded=False):
    sel_types = st.multiselect("Primary Property Type", raw_df[C_TYPE].dropna().unique() if C_TYPE in raw_df.columns else [])
    sel_decades = st.multiselect("Decade Built", sorted(raw_df[C_DECADE].dropna().unique()) if C_DECADE in raw_df.columns else [])
    sel_occ = st.multiselect("Occupancy Status", raw_df[C_OCCUPANCY].dropna().unique() if C_OCCUPANCY in raw_df.columns else [])
    sel_const = st.multiselect("Construction Status", raw_df[C_CONSTRUCTION].dropna().unique() if C_CONSTRUCTION in raw_df.columns else [])
    
    if C_AGE in raw_df.columns:
        age_min, age_max = int(raw_df[C_AGE].min()), int(raw_df[C_AGE].max())
    else:
        age_min, age_max = 0, 100
    sel_age = st.slider("Building Age Range", age_min, age_max, (age_min, age_max))

with st.sidebar.expander("📈 Performance & Risk", expanded=False):
    score_min, score_max = 0, 100
    sel_score = st.slider("ENERGY STAR Score", score_min, score_max, (score_min, score_max))
    
    if C_GHG in raw_df.columns:
        ghg_min, ghg_max = float(raw_df[C_GHG].min()), float(raw_df[C_GHG].max())
    else:
        ghg_min, ghg_max = 0.0, 1000.0
    sel_ghg = st.slider("GHG Emissions (tCO₂e)", ghg_min, ghg_max, (ghg_min, ghg_max))
    
    if C_PENALTY in raw_df.columns:
        pen_min, pen_max = float(raw_df[C_PENALTY].min()), float(raw_df[C_PENALTY].max())
    else:
        pen_min, pen_max = 0.0, 1000000.0
    sel_pen = st.slider("LL97 Penalty ($)", pen_min, pen_max, (pen_min, pen_max))

with st.sidebar.expander("⚠️ Data Quality", expanded=False):
    exc_alerts = st.multiselect("Exclude Properties with Alerts", 
                                ['Energy Meter Gaps', 'Missing Energy Meters', 'Less than 12 Months of Data'])

search_term = st.sidebar.text_input("🔍 Search Property Name", "")

# --- Apply Filters ---
df = raw_df.copy()

if search_term and C_NAME in df.columns:
    df = df[df[C_NAME].str.contains(search_term, case=False, na=False)]
if sel_cities and C_CITY in df.columns:
    df = df[df[C_CITY].isin(sel_cities)]
if sel_boros and C_BORO in df.columns:
    df = df[df[C_BORO].isin(sel_boros)]
if sel_types and C_TYPE in df.columns:
    df = df[df[C_TYPE].isin(sel_types)]
if sel_decades and C_DECADE in df.columns:
    df = df[df[C_DECADE].isin(sel_decades)]
if sel_occ and C_OCCUPANCY in df.columns:
    df = df[df[C_OCCUPANCY].isin(sel_occ)]
if sel_const and C_CONSTRUCTION in df.columns:
    df = df[df[C_CONSTRUCTION].isin(sel_const)]
if C_AGE in df.columns:
    df = df[df[C_AGE].between(sel_age[0], sel_age[1])]
if C_SCORE in df.columns:
    df = df[df[C_SCORE].fillna(0).between(sel_score[0], sel_score[1])]
if C_GHG in df.columns:
    df = df[df[C_GHG].between(sel_ghg[0], sel_ghg[1])]
if C_PENALTY in df.columns:
    df = df[df[C_PENALTY].between(sel_pen[0], sel_pen[1])]
if exc_alerts and C_ALERTS in df.columns:
    df = df[~df[C_ALERTS].isin(exc_alerts)]


# ==========================================
# HELPER FUNCTIONS 
# ==========================================
def get_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(size=16, color="#f8fafc")),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=30, l=30, r=30),
        font=dict(color="#94a3b8")
    )

def plot_horizontal_bar(data, x, y, title, color_hex, hover_cols=None):
    fig = px.bar(data, x=x, y=y, orientation='h', hover_data=hover_cols)
    fig.update_traces(marker_color=color_hex)
    fig.update_layout(get_layout(title), yaxis={'categoryorder':'total ascending'})
    return fig

# ==========================================
# MAIN DASHBOARD LAYOUT
# ==========================================
st.title("🌍 ESG & Carbon Mitigation Dashboard")

tab1, tab2 = st.tabs(["Section 1: Problem Analysis", "Section 2: Mitigation Scenarios"])

# ---------------------------------------------------------
# TAB 1: PROBLEM ANALYSIS
# ---------------------------------------------------------
with tab1:
    #st.markdown('<img src="https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?q=80&w=1200&auto=format&fit=crop" class="header-image">', unsafe_allow_html=True)
    
    kpi_ghg = df[C_GHG].sum() if C_GHG in df.columns else 0
    kpi_net = df[C_NET].sum() if C_NET in df.columns else 0
    kpi_penalty = df[C_PENALTY].sum() if C_PENALTY in df.columns else 0
    kpi_score = df[C_SCORE].mean() if C_SCORE in df.columns else 0
    kpi_intensity = df[C_INTENSITY].mean() if C_INTENSITY in df.columns else 0
    kpi_avoided = df[C_AVOIDED].sum() if C_AVOIDED in df.columns else 0
    high_risk_count = len(df[df[C_PENALTY] > df[C_PENALTY].quantile(0.75)]) if C_PENALTY in df.columns else 0
    bldg_count = len(df)
    
    st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card"><div class="kpi-title">Total Properties</div><div class="kpi-value">🏢 {bldg_count:,}</div></div>
            <div class="kpi-card risk"><div class="kpi-title">Total GHG (tCO₂e)</div><div class="kpi-value">🏭 {kpi_ghg:,.0f}</div></div>
            <div class="kpi-card risk"><div class="kpi-title">Total LL97 Penalty</div><div class="kpi-value">💵 ${kpi_penalty:,.0f}</div></div>
            <div class="kpi-card good"><div class="kpi-title">Avg ENERGY STAR</div><div class="kpi-value">⭐ {kpi_score:.1f}/100</div></div>
        </div>
        <div class="kpi-container">
            <div class="kpi-card good"><div class="kpi-title">Avoided Emissions</div><div class="kpi-value">🌿 {kpi_avoided:,.0f} <span class="kpi-badge badge-green">tCO₂e</span></div></div>
            <div class="kpi-card risk"><div class="kpi-title">Avg Intensity</div><div class="kpi-value">📊 {kpi_intensity:.2f} <span class="kpi-badge badge-red">kgCO₂/ft²</span></div></div>
            <div class="kpi-card"><div class="kpi-title">Net Emissions</div><div class="kpi-value">📉 {kpi_net:,.0f}</div></div>
            <div class="kpi-card risk"><div class="kpi-title">High-Risk Assets</div><div class="kpi-value">⚠️ {high_risk_count}</div></div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Executive Summary Panel
    highest_emitter = df.loc[df[C_GHG].idxmax()][C_NAME] if C_GHG in df.columns and not df[C_GHG].isna().all() else "N/A"
    highest_penalty_bldg = df.loc[df[C_PENALTY].idxmax()][C_NAME] if C_PENALTY in df.columns and not df[C_PENALTY].isna().all() else "N/A"
    best_performer = df.loc[df[C_SCORE].idxmax()][C_NAME] if C_SCORE in df.columns and not df[C_SCORE].isna().all() else "N/A"
    
    st.markdown(f"""
        <div class="exec-panel">
            <h3>📑 Chief Sustainability Officer Summary</h3>
            <p>The current portfolio configuration carries an aggregate LL97 exposure of <b>${kpi_penalty:,.0f}</b> driven by <b>{kpi_ghg:,.0f} metric tons</b> of CO₂e. 
            The most severe environmental bottleneck is <b>{highest_emitter}</b>, while <b>{highest_penalty_bldg}</b> poses the most immediate financial threat. 
            Conversely, <b>{best_performer}</b> serves as the portfolio benchmark. Priority capital allocation should target the highest-risk assets to rapidly mitigate statutory fines.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🚨 High-Risk Identification")
    c1, c2 = st.columns(2)
    with c1:
        if all(c in df.columns for c in [C_NAME, C_GHG]):
            top_ghg = df.nlargest(10, C_GHG).sort_values(C_GHG, ascending=True)
            st.plotly_chart(plot_horizontal_bar(top_ghg, C_GHG, C_NAME, "Top 10 Polluting Buildings", COLOR_RED, hover_cols=[C_TYPE, C_BORO]), use_container_width=True)
            st.caption("Buildings contributing the highest gross metric tons of CO₂ equivalent.")
            
            with st.expander("🔍 Show Insights: Top Polluters"):
                if len(top_ghg) > 0:
                    highest_bldg = top_ghg.iloc[-1]
                    pct_total = (highest_bldg[C_GHG] / kpi_ghg * 100) if kpi_ghg > 0 else 0
                    diff = highest_bldg[C_GHG] - (top_ghg.iloc[-2][C_GHG] if len(top_ghg)>1 else 0)
                    st.info(f"""
                    * ✅ **Highest Emitter:** {highest_bldg[C_NAME]} with {highest_bldg[C_GHG]:,.0f} tCO₂e.
                    * ⚠️ **Concentration Risk:** This single building accounts for **{pct_total:.1f}%** of the currently filtered emissions.
                    * 📈 **Outlier Check:** It emits **{diff:,.0f} tCO₂e** more than the second-highest emitter.
                    """)
            
    with c2:
        if all(c in df.columns for c in [C_NAME, C_PENALTY]):
            top_pen = df.nlargest(10, C_PENALTY).sort_values(C_PENALTY, ascending=True)
            st.plotly_chart(plot_horizontal_bar(top_pen, C_PENALTY, C_NAME, "Highest Financial Risk (LL97 Penalties)", COLOR_RED, hover_cols=[C_GHG]), use_container_width=True)
            st.caption("Buildings facing the largest estimated statutory fines under Local Law 97.")
            
            with st.expander("💡 AI Insights: Financial Risk"):
                if len(top_pen) > 0:
                    highest_risk = top_pen.iloc[-1]
                    top10_pen_total = top_pen[C_PENALTY].sum()
                    pct_risk = (top10_pen_total / kpi_penalty * 100) if kpi_penalty > 0 else 0
                    st.warning(f"""
                    * 💰 **Maximum Liability:** {highest_risk[C_NAME]} is facing the highest potential penalty of **${highest_risk[C_PENALTY]:,.0f}**.
                    * ⚠️ **Risk Concentration:** The top 10 buildings shown represent **{pct_risk:.1f}%** (${top10_pen_total:,.0f}) of total portfolio penalties.
                    * 🌱 **Action Required:** Prioritizing retrofits on these specific properties will yield the highest ROI in penalty avoidance.
                    """)

    st.markdown("### 🏢 Structural & Regional Distribution")
    c3, c4 = st.columns(2)
    with c3:
        if C_TYPE in df.columns and C_GHG in df.columns:
            type_df = df.groupby(C_TYPE)[C_GHG].sum().reset_index().nlargest(10, C_GHG).sort_values(C_GHG, ascending=True)
            st.plotly_chart(plot_horizontal_bar(type_df, C_GHG, C_TYPE, "Emissions by Building Type", COLOR_BLUE), use_container_width=True)
            st.caption("Aggregated emissions footprint categorized by primary property use-case.")
            
            with st.expander("📊 Key Findings: Building Types"):
                if len(type_df) > 0:
                    top_type = type_df.iloc[-1]
                    avg_by_type = df.groupby(C_TYPE)[C_GHG].mean().loc[top_type[C_TYPE]]
                    st.info(f"""
                    * ✅ **Primary Contributor:** **{top_type[C_TYPE]}** properties generate the most aggregate emissions ({top_type[C_GHG]:,.0f} tCO₂e).
                    * 📈 **Averages:** On average, a {top_type[C_TYPE]} building emits **{avg_by_type:,.0f} tCO₂e**.
                    * 🌱 **Strategy Focus:** Targeted guidelines specific to {top_type[C_TYPE]} operations will have the largest systemic impact.
                    """)
            
    with c4:
        if C_BORO in df.columns and C_PENALTY in df.columns:
            boro_df = df.groupby(C_BORO)[[C_GHG, C_PENALTY]].sum().reset_index()
            fig_boro = px.bar(boro_df, x=C_BORO, y=[C_GHG, C_PENALTY], barmode='group', 
                              color_discrete_sequence=[COLOR_BLUE, COLOR_RED])
            fig_boro.update_layout(get_layout("Borough Analysis: Emissions & Penalties"))
            fig_boro.update_layout(legend_title_text='')
            st.plotly_chart(fig_boro, use_container_width=True)
            st.caption("Comparison of physical emissions vs. financial risk distributed geographically.")
            
            with st.expander("🔍 Show Insights: Geography"):
                if len(boro_df) > 0:
                    worst_boro = boro_df.loc[boro_df[C_GHG].idxmax()]
                    best_boro = boro_df.loc[boro_df[C_GHG].idxmin()]
                    st.info(f"""
                    * ✅ **Highest Emissions:** **{worst_boro[C_BORO]}** accounts for the most emissions ({worst_boro[C_GHG]:,.0f} tCO₂e).
                    * 💰 **Highest Penalties:** {boro_df.loc[boro_df[C_PENALTY].idxmax()][C_BORO]} faces the highest cumulative LL97 fines.
                    * 🌱 **Best Performer:** **{best_boro[C_BORO]}** shows the lowest aggregate footprint in the selected filters.
                    """)

    st.markdown("### ⚡ Operational Insights")
    c5, c6 = st.columns(2)
    with c5:
        if all(c in df.columns for c in [C_AGE, C_INTENSITY, C_NAME]):
            fig_age = px.scatter(df, x=C_AGE, y=C_INTENSITY, opacity=0.6, hover_name=C_NAME, hover_data=[C_TYPE, C_GHG],
                                 trendline="ols", trendline_color_override=COLOR_ORANGE)
            fig_age.update_traces(marker_color=COLOR_BLUE)
            fig_age.update_layout(get_layout("Building Age vs. Emission Intensity"))
            st.plotly_chart(fig_age, use_container_width=True)
            st.caption("Visualizing the relationship between infrastructure age and carbon efficiency.")
            
            with st.expander("💡 AI Insights: Infrastructure Age"):
                if len(df.dropna(subset=[C_AGE, C_INTENSITY])) > 2:
                    corr = df[C_AGE].corr(df[C_INTENSITY])
                    trend_txt = "tend to be less efficient" if corr > 0 else "show minimal efficiency loss compared to newer builds"
                    st.info(f"""
                    * 📈 **Trend Analysis:** Older buildings in this portfolio {trend_txt} (Correlation: {corr:.2f}).
                    * ✅ **Oldest Asset:** {df.loc[df[C_AGE].idxmax()][C_NAME]} ({df[C_AGE].max():.0f} years old).
                    * ⚠️ **Highest Intensity:** {df.loc[df[C_INTENSITY].idxmax()][C_NAME]} is the least carbon-efficient property per square foot.
                    """)
            
    with c6:
        energy_cols = [c for c in df.columns if "Use (kBtu)" in c]
        if energy_cols:
            energy_sums = df[energy_cols].sum().sort_values(ascending=True)
            energy_df = pd.DataFrame({'Source': energy_sums.index.str.replace(' Use (kBtu)', '', regex=False), 'Total kBtu': energy_sums.values})
            st.plotly_chart(plot_horizontal_bar(energy_df, 'Total kBtu', 'Source', "Portfolio Energy Source Breakdown", COLOR_BLUE), use_container_width=True)
            st.caption("Aggregate energy consumption separated by utility and fuel type.")
            
            with st.expander("📊 Key Findings: Energy Use"):
                if len(energy_sums) > 0:
                    top_energy = energy_sums.index[-1]
                    total_energy = energy_sums.sum()
                    pct_energy = (energy_sums.iloc[-1] / total_energy * 100) if total_energy > 0 else 0
                    st.info(f"""
                    * ✅ **Dominant Source:** **{top_energy.replace(' Use (kBtu)', '')}** is the primary driver of consumption.
                    * 📈 **Distribution:** It accounts for **{pct_energy:.1f}%** of the total energy modeled.
                    * 🌱 **Opportunity:** Targeting {top_energy.replace(' Use (kBtu)', '')} efficiency systems (like HVAC electrification or grid PPAs) provides the fastest reduction pathway.
                    """)

    c7, c8 = st.columns(2)
    with c7:
        if all(c in df.columns for c in [C_SCORE, C_INTENSITY, C_NAME]):
            fig_bench = px.scatter(df, x=C_SCORE, y=C_INTENSITY, color=C_SCORE, hover_name=C_NAME,
                                   color_continuous_scale="RdYlGn", opacity=0.7)
            fig_bench.update_layout(get_layout("ENERGY STAR Score vs. Emission Intensity"))
            st.plotly_chart(fig_bench, use_container_width=True)
            st.caption("Benchmarking federal rating (higher is better) against actual carbon intensity.")
            
            with st.expander("🔍 Show Insights: ENERGY STAR Benchmark"):
                if len(df.dropna(subset=[C_SCORE, C_INTENSITY])) > 2:
                    avg_score = df[C_SCORE].mean()
                    low_score_bldgs = len(df[df[C_SCORE] < 50])
                    st.info(f"""
                    * 📈 **Average Benchmark:** The filtered portfolio averages a score of **{avg_score:.1f}/100**.
                    * ⚠️ **Underperformers:** **{low_score_bldgs} properties** score below the national median of 50.
                    * ✅ **Validation:** As expected, higher scores generally correlate tightly with lower emission intensities.
                    """)
            
    with c8:
        if C_ALERTS in df.columns:
            alerts_series = df[C_ALERTS].dropna().astype(str).str.split(',').explode().str.strip()
            alerts_count = alerts_series.value_counts().reset_index().head(10).sort_values('count', ascending=True)
            alerts_count.columns = ['Alert Type', 'Frequency']
            fig_alerts = plot_horizontal_bar(alerts_count, 'Frequency', 'Alert Type', "Data Quality Issues Detected", COLOR_ORANGE)
            st.plotly_chart(fig_alerts, use_container_width=True)
            st.caption("Identified gaps and anomalies in utility data reporting.")
            
            with st.expander("⚠️ Key Findings: Data Integrity"):
                if len(alerts_count) > 0:
                    top_alert = alerts_count.iloc[-1]
                    st.warning(f"""
                    * ⚠️ **Primary Issue:** **{top_alert['Alert Type']}** is the most common data gap, affecting {top_alert['Frequency']} reports.
                    * 📈 **Reporting Risk:** Poor data quality can lead to inaccurate LL97 penalty assessments and misallocated capital.
                    * 💰 **Action:** Immediate utility meter audits required for flagged properties to correct baseline reporting.
                    """)

# ---------------------------------------------------------
# TAB 2: MITIGATION SCENARIOS
# ---------------------------------------------------------
with tab2:
    st.markdown('<img src="https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=1200&auto=format&fit=crop" class="header-image">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Configure Strategic Interventions")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        eff_pct = st.slider("💡 Energy Efficiency Upgrade (%)", 0, 40, 15, help="Reduces overall baseline emissions portfolio-wide (e.g. LED retrofits, HVAC tuning).") / 100
    with col_s2:
        renew_pct = st.slider("☀️ Renewable Energy Adoption (%)", 0, 100, 30, help="Replaces Grid Electricity with clean, off-site power purchase agreements (PPAs).") / 100
    with col_s3:
        retro_age = st.slider("🏗️ Deep Retrofit Target Age (Years)", 20, 100, 50, help="Targets buildings older than this parameter for deep envelope and system upgrades.")
        retro_pct = 0.40 

    base_emissions = df[C_GHG].sum() if C_GHG in df.columns else 1 
    base_penalty = df[C_PENALTY].sum() if C_PENALTY in df.columns else 0
    
    s1_red_emissions = base_emissions * eff_pct
    s1_bldgs = len(df)
    
    grid_col = "Electricity Use - Grid Purchase (kBtu)"
    grid_ratio = df[grid_col].sum() / df[[c for c in df.columns if "Use (kBtu)" in c]].sum().sum() if grid_col in df.columns else 0.4
    s2_red_emissions = (base_emissions * grid_ratio) * renew_pct
    s2_bldgs = len(df[df[grid_col] > 0]) if grid_col in df.columns else len(df)
    
    if C_AGE in df.columns:
        target_bldgs = df[df[C_AGE] >= retro_age]
        s3_red_emissions = target_bldgs[C_GHG].sum() * retro_pct
        s3_bldgs = len(target_bldgs)
    else:
        s3_red_emissions, s3_bldgs = 0, 0

    comb_remain = base_emissions * (1 - eff_pct)
    comb_remain = comb_remain - (s2_red_emissions * (1 - eff_pct)) 
    comb_remain = comb_remain - (s3_red_emissions * (1 - eff_pct)) 
    comb_red_emissions = base_emissions - comb_remain

    def calc_savings(reduction): return base_penalty * (reduction / base_emissions)

    scenarios = pd.DataFrame({
        "Scenario": ["Baseline", "S1: Efficiency", "S2: Renewables", "S3: Retrofit", "Combined Strategy"],
        "Emissions (tCO₂e)": [base_emissions, base_emissions-s1_red_emissions, base_emissions-s2_red_emissions, base_emissions-s3_red_emissions, comb_remain],
        "Reduction (tCO₂e)": [0, s1_red_emissions, s2_red_emissions, s3_red_emissions, comb_red_emissions],
        "Reduction %": [0, (s1_red_emissions/base_emissions)*100, (s2_red_emissions/base_emissions)*100, (s3_red_emissions/base_emissions)*100, (comb_red_emissions/base_emissions)*100],
        "$ Saved (LL97)": [0, calc_savings(s1_red_emissions), calc_savings(s2_red_emissions), calc_savings(s3_red_emissions), calc_savings(comb_red_emissions)],
        "Bldgs Impacted": [0, s1_bldgs, s2_bldgs, s3_bldgs, bldg_count]
    })

    st.markdown("---")
    
    st.subheader("🎯 Combined Strategy Outcomes", help="Shows the compounded result of applying all three scenarios sequentially to avoid double-counting emissions.")
    co1, co2, co3, co4 = st.columns(4)
    co1.metric("Final Emissions (tCO₂e)", f"{comb_remain:,.0f}", f"-{comb_red_emissions:,.0f} (-{(comb_red_emissions/base_emissions)*100:.1f}%)")
    co2.metric("Total LL97 Penalty Saved", f"${calc_savings(comb_red_emissions):,.0f}", "Projected Annual Savings")
    co3.metric("Buildings Impacted", f"{bldg_count}", "Portfolio Wide")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = (comb_red_emissions/base_emissions)*100,
        title = {'text': "% Portfolio Emissions Reduced", 'font': {'color': '#f8fafc'}},
        number = {'suffix': "%", 'font': {'color': COLOR_GREEN}},
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': COLOR_GREEN},
            'bgcolor': COLOR_CARD,
            'steps': [
                {'range': [0, 20], 'color': COLOR_RED},
                {'range': [20, 50], 'color': COLOR_ORANGE},
                {'range': [50, 100], 'color': "#064e3b"}
            ]}
    ))
    fig_gauge.update_layout(get_layout(), height=250, margin=dict(t=40, b=0, l=20, r=20))
    with co4:
        st.plotly_chart(fig_gauge, use_container_width=True)

    with st.expander("💡 AI Insights: Mitigation Performance"):
        best_single = scenarios.iloc[1:4].loc[scenarios.iloc[1:4]["Reduction (tCO₂e)"].idxmax()]
        st.success(f"""
        * 🌱 **Cumulative Impact:** Executing the combined strategy removes **{comb_red_emissions:,.0f} tCO₂e** from your annual footprint.
        * 💰 **Capital Preservation:** This approach prevents an estimated **${calc_savings(comb_red_emissions):,.0f}** in regulatory fines.
        * ✅ **Most Effective Single Measure:** On its own, **{best_single['Scenario'].replace('S1: ', '').replace('S2: ', '').replace('S3: ', '')}** provides the highest independent return, reducing baseline emissions by {best_single['Reduction %']:.1f}%.
        * 📉 **Residual Liability:** Your portfolio will still generate **{comb_remain:,.0f} tCO₂e**. Further decarbonization or carbon offsets will be required to reach Net Zero.
        """)

    st.markdown("### 📉 Impact Breakdown")
    r2c1, r2c2 = st.columns(2)
    
    with r2c1:
        fig_waterfall = go.Figure(go.Waterfall(
            name="2026 Path", orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=["Baseline", "Efficiency", "Renewables", "Retrofits", "Final Residual"],
            textposition="outside",
            text=[f"{v/1000:.1f}k" for v in [base_emissions, -s1_red_emissions, -s2_red_emissions, -s3_red_emissions, comb_remain]],
            y=[base_emissions, -s1_red_emissions, -s2_red_emissions, -s3_red_emissions, comb_remain],
            decreasing={"marker": {"color": COLOR_GREEN}},
            increasing={"marker": {"color": COLOR_RED}},
            totals={"marker": {"color": COLOR_BLUE}}
        ))
        fig_waterfall.update_layout(get_layout("Emissions Reduction Waterfall (tCO₂e)"))
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.caption("Visualizing the step-by-step reduction from current baseline to the final projected residual footprint.")

    with r2c2:
        categories = ['CO₂ Reduction %', 'Penalty Savings %', 'Bldgs Impacted %']
        fig_radar = go.Figure()
        
        def add_radar_trace(name, red_pct, bldg_count, color):
            fig_radar.add_trace(go.Scatterpolar(
                r=[red_pct, red_pct, (bldg_count/len(df))*100 if len(df)>0 else 0], 
                theta=categories, fill='toself', name=name, marker=dict(color=color)
            ))
            
        add_radar_trace("S1: Efficiency", (s1_red_emissions/base_emissions)*100, s1_bldgs, COLOR_BLUE)
        add_radar_trace("S2: Renewables", (s2_red_emissions/base_emissions)*100, s2_bldgs, COLOR_ORANGE)
        add_radar_trace("S3: Retrofit", (s3_red_emissions/base_emissions)*100, s3_bldgs, COLOR_RED)
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155")),
            showlegend=True,
            **get_layout("Scenario Effectiveness Radar")
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption("Comparing the holistic impact footprint of each independent strategy.")

    r3c1, r3c2 = st.columns(2)
    
    with r3c1:
        plot_df = scenarios.iloc[1:4].melt(id_vars="Scenario", value_vars=["Reduction (tCO₂e)", "$ Saved (LL97)"])
        fig_comp = px.bar(plot_df, x="Scenario", y="value", color="variable", barmode="group",
                          color_discrete_sequence=[COLOR_GREEN, COLOR_BLUE])
        fig_comp.update_layout(get_layout("Individual Scenario Return vs Impact"))
        fig_comp.update_yaxes(showticklabels=False, title="")
        st.plotly_chart(fig_comp, use_container_width=True)
        st.caption("Hover over bars to view exact physical vs financial yield for each scenario.")

    with r3c2:
        df_roadmap = pd.DataFrame([
            dict(Task="Phase 1: Energy Audits & Upgrades", Start='2024-01-01', Finish='2024-12-31', Phase="Short-term"),
            dict(Task="Phase 2: Power Purchase Agreements", Start='2024-06-01', Finish='2025-06-30', Phase="Mid-term"),
            dict(Task="Phase 3: Deep Envelope Retrofits", Start='2025-01-01', Finish='2026-12-31', Phase="Long-term")
        ])
        fig_timeline = px.timeline(df_roadmap, x_start="Start", x_end="Finish", y="Task", color="Phase", 
                                   color_discrete_sequence=[COLOR_BLUE, COLOR_ORANGE, COLOR_GREEN])
        fig_timeline.update_layout(get_layout("Strategic Implementation Roadmap"))
        st.plotly_chart(fig_timeline, use_container_width=True)
        st.caption("A proposed multi-year project timeline to execute the combined strategy.")