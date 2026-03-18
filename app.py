"""
JAKT Bracket Intelligence — March Madness 2026
"""
import streamlit as st
import pandas as pd
import json, os

st.set_page_config(page_title="JAKT Bracket Intelligence", page_icon="🏀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@300;400;600;700&display=swap');

    .stApp { background-color: #f8f9fa; }

    .main-title {
        font-family: 'Bebas Neue', sans-serif; font-size: 2.8rem; letter-spacing: 3px;
        color: #1a1a2e; text-align: center; margin-bottom: 0;
    }
    .subtitle {
        font-family: 'Source Sans 3', sans-serif; font-size: 1rem; color: #6c757d;
        text-align: center; margin-top: -6px; margin-bottom: 24px;
    }
    .team-header {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; letter-spacing: 2px;
        color: #1a1a2e; margin-bottom: 2px;
    }
    .team-sub { font-family: 'Source Sans 3', sans-serif; font-size: 0.9rem; color: #6c757d; }
    .vs-badge { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: #c0392b; text-align: center; }

    /* Report card */
    .rc-row {
        display: flex; align-items: center; padding: 10px 14px; margin: 4px 0;
        border-radius: 8px; background: #fff; border: 1px solid #e9ecef;
    }
    .rc-grade {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem; width: 48px;
        text-align: center; border-radius: 6px; padding: 2px 0; margin-right: 14px;
        color: #fff; font-weight: 700; line-height: 1.2;
    }
    .rc-grade-A { background: #27ae60; }
    .rc-grade-B { background: #2980b9; }
    .rc-grade-C { background: #f39c12; }
    .rc-grade-D { background: #e74c3c; }
    .rc-grade-F { background: #95a5a6; }
    .rc-metric { font-family: 'Source Sans 3', sans-serif; font-weight: 600; font-size: 0.95rem; color: #2c3e50; }
    .rc-detail { font-family: 'Source Sans 3', sans-serif; font-size: 0.82rem; color: #7f8c8d; margin-top: 1px; }
    .rc-confirm { font-family: 'Source Sans 3', sans-serif; font-size: 0.78rem; color: #95a5a6; font-style: italic; margin-top: 1px; }
    .rc-champ { background: #27ae60; color: #fff; font-size: 0.7rem; padding: 1px 6px; border-radius: 4px; font-weight: 600; margin-left: 8px; }

    .gpa-box {
        background: #fff; border: 2px solid #1a1a2e; border-radius: 12px;
        padding: 16px; text-align: center; margin: 8px 0;
    }
    .gpa-val { font-family: 'Bebas Neue', sans-serif; font-size: 2.8rem; color: #1a1a2e; line-height: 1; }
    .gpa-label { font-family: 'Source Sans 3', sans-serif; font-size: 0.8rem; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }

    .edge-banner {
        background: #eafaf1; border-left: 4px solid #27ae60;
        padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0;
    }
    .edge-text { font-family: 'Source Sans 3', sans-serif; font-size: 1.1rem; font-weight: 600; color: #1a1a2e; }

    .injury-row {
        display: flex; align-items: center; padding: 8px 14px; margin: 4px 0;
        border-radius: 8px; background: #fff8e1; border: 1px solid #f39c12;
        font-family: 'Source Sans 3', sans-serif; font-size: 0.85rem; color: #7f6c00;
    }

    section[data-testid="stSidebar"] { background-color: #fff; }
    .stTabs [data-baseweb="tab"] { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1.5px; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)

# ── Data ──
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(DATA_DIR, "teams_full_2026.json")) as f:
    TEAMS = json.load(f)
SCHED_PATH = os.path.join(DATA_DIR, "schedules_2026.json")
SCHEDULES = json.load(open(SCHED_PATH)) if os.path.exists(SCHED_PATH) else {}

def ht_display(inches):
    if not inches or inches == 0: return "N/A"
    return f"{int(inches)//12}'{int(inches)%12}\""

METRIC_NAMES = {
    "m1": "Roster Maturity",
    "m2": "Two-Way Balance",
    "m3": "Offensive Consistency",
    "m4": "PG Ball Security",
    "m5": "Tempo Control",
    "m6": "3PT Reliability",
}
METRIC_PILLAR = {
    "m1": "Your pillar: senior-heavy, 6'3\"+ starters win in March",
    "m2": "History: 23 of 24 champs top-21 off AND top-37 def",
    "m3": "Your pillar: offense must sustain across all opponent tiers",
    "m4": "Your pillar: PG controls tempo under tournament pressure",
    "m5": "Your pillar: teams that control pace win in March regardless of opponent",
    "m6": "Your pillar: live by the 3, die by the 3 — low variance + high volume = reliable",
}

def fetch_team_news(api_key, team_name):
    """Use Claude with web search to find recent injuries/news for a team."""
    import requests as req
    try:
        resp = req.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": api_key,
                     "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-sonnet-4-20250514", "max_tokens": 500,
                "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
                "messages": [{"role": "user", "content":
                    f"Search for the latest injury updates and important news for {team_name} "
                    f"men's basketball in the last 7 days (March 2026 NCAA tournament). "
                    f"Return ONLY a bullet list of injuries/key news. Each bullet: "
                    f"'Player — status (detail)'. If no injuries or news found, return 'No recent injury updates.'"}]
            }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
        return None
    except Exception:
        return None

def get_metrics(d):
    return d.get("five_metrics", {})

def render_report_card(team_name, d, news=None):
    fm = get_metrics(d)
    if not fm:
        st.warning(f"No metrics for {team_name}")
        return

    # Header
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:8px;">
        <div>
            <div class="team-header">{team_name.upper()}</div>
            <div class="team-sub">({d['seed']}) {d['region']} Region · {d['record']} · {d.get('conf','')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # GPA box + grades
    col_gpa, col_grades = st.columns([1, 3])

    with col_gpa:
        gpa = fm.get("gpa", 0)
        champ = "✓ CHAMP CRITERIA" if fm.get("meets_champ_criteria") else ""
        st.markdown(f"""
        <div class="gpa-box">
            <div class="gpa-val">{gpa:.2f}</div>
            <div class="gpa-label">GPA</div>
            {"<div style='margin-top:6px;'><span class='rc-champ'>" + champ + "</span></div>" if champ else ""}
        </div>
        """, unsafe_allow_html=True)

    with col_grades:
        for key in ["m1", "m2", "m3", "m4", "m5", "m6"]:
            g = fm.get(f"{key}_grade", "F")
            detail = fm.get(f"{key}_detail", "")
            pillar = METRIC_PILLAR[key]
            st.markdown(f"""
            <div class="rc-row">
                <div class="rc-grade rc-grade-{g}">{g}</div>
                <div>
                    <div class="rc-metric">{METRIC_NAMES[key]}</div>
                    <div class="rc-detail">{detail}</div>
                    <div class="rc-confirm">{pillar}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Live injury/news from web search
        if news and "no recent" not in news.lower():
            st.markdown(f'<div class="injury-row">&#9888;&#65039; <strong>Latest News</strong><br>{news}</div>', unsafe_allow_html=True)

    # Roster expander
    with st.expander(f"Full Roster — Top 8 by Minutes"):
        roster_df = pd.DataFrame([{
            "Player": s["name"], "Class": s["class"], "Ht": s["height"],
            "Pos": s["position"], "PPG": s["ppg"], "ORtg": s["ortg"],
            "eFG%": s["efg"], "3PT%": s["three_pct"],
            "AST%": s["ast_pct"], "TO%": s["to_pct"], "Min%": s["min_pct"]
        } for s in d.get("starters", [])])
        if not roster_df.empty:
            st.dataframe(roster_df, use_container_width=True, hide_index=True)


def call_anthropic_api(api_key, t1_name, t1, t2_name, t2, news1=None, news2=None):
    import requests as req
    def build(name, d, news=None):
        fm = get_metrics(d)
        ratio = d.get("pg_ast_pct",0) / max(d.get("pg_to_pct",1),0.1)
        strs = "\n".join(f"  - {s['name']} ({s['class']}, {s['height']}, {s['position']}) PPG:{s['ppg']}, ORtg:{s['ortg']}" for s in d.get("starters", [])[:7])
        ts = d.get("tier_splits") or {}
        t1d = ts.get("Tier1", {})
        base = f"""{name} ({d['seed']}-seed, {d['region']}, {d['record']})
Report Card: M1={fm.get('m1_grade','?')} M2={fm.get('m2_grade','?')} M3={fm.get('m3_grade','?')} M4={fm.get('m4_grade','?')} M5={fm.get('m5_grade','?')} M6={fm.get('m6_grade','?')} GPA={fm.get('gpa','?')}
Meets Championship Criteria: {fm.get('meets_champ_criteria', False)}
KenPom: #{d.get('kenpom_rank','?')} (Off #{d.get('kenpom_off_rank','?')}, Def #{d.get('kenpom_def_rank','?')})
Starter avg ht: {ht_display(d.get('avg_starter_height_in',0))} | Exp: {d.get('avg_starter_exp_yrs',0):.1f}yr
T1 record: {t1d.get('wins',0)}-{t1d.get('losses',0)}, {t1d.get('avg_margin',0):+.1f} margin, {ts.get('consistency_pct',0):.0f}% retention
PG: {d.get('pg_name','?')} (AST%: {d.get('pg_ast_pct','?')}, TO%: {d.get('pg_to_pct','?')}, Ratio: {ratio:.2f})
Rotation:\n{strs}"""
        if news and "no recent" not in news.lower():
            base += f"\nLATEST NEWS/INJURIES:\n{news}"
        return base

    prompt = f"""You are an elite college basketball analyst helping someone win their bracket pool. 

Grade each team on these 6 metrics (A/B/C/D/F):
1. ROSTER MATURITY: height + experience. Senior-heavy 6'3"+ starters win in March.
2. TWO-WAY BALANCE: KenPom off+def. 23 of 24 champs were top-21 off AND top-37 def.
3. OFFENSIVE CONSISTENCY: Does scoring hold up across T1/T2/T3 tiers? Teams that only score vs cupcakes get exposed.
4. PG BALL SECURITY: AST%/TO% ratio. Tournament pressure amplifies turnovers.
5. TEMPO CONTROL: How stable is win margin (60%) and scoring (40%) across tiers? Teams that control pace win in March.
6. 3PT RELIABILITY: Low game-to-game 3PT% variance + high volume = reliable shooting. Live by the 3, die by the 3.

Here are two teams with REAL Barttorvik + KenPom data:

{build(t1_name, t1, news1)}

VS

{build(t2_name, t2, news2)}

For each metric, state which team wins that metric and why (cite specific data).
Then give your PICK, confidence (1-10), and a one-sentence "why they win" and "why they lose" for each team.
Keep it tight and data-driven."""

    try:
        resp = req.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        return resp.json()["content"][0]["text"] if resp.status_code == 200 else f"Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Error: {e}"


# ── Layout ──
st.markdown('<div class="main-title">🏀 JAKT BRACKET INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">March Madness 2026 · {len(TEAMS)} Teams · 6-Metric Report Card</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Settings")
    api_key = st.text_input("Anthropic API Key", type="password", help="Powers the AI matchup analysis")
    st.markdown("---")
    st.markdown("### The 5 Metrics")
    st.markdown("""
**M1 · Roster Maturity**
Height + experience composite

**M2 · Two-Way Balance**
KenPom off + def rank sum

**M3 · Offensive Consistency**
Scoring stability across T1/T2/T3 tiers

**M4 · PG Ball Security**
AST% / TO% ratio

**M5 · Tempo Control**
Win margin + scoring stability across tiers

**M6 · 3PT Reliability**
3PT% variance + volume per game
""")
    st.markdown("---")
    st.markdown("**Grading:** A (elite) → F (fail)")
    st.markdown("**GPA:** 4.0 scale across all 6")
    st.markdown("**Champ Criteria:** Top-21 off AND top-37 def")
    st.markdown("---")
    st.caption("Data: Barttorvik API · KenPom via BetMGM · ESPN Schedule API · CBS Sports · March 17 2026")

tab1, tab2 = st.tabs(["⚔️  HEAD-TO-HEAD", "📊  FULL RANKINGS"])

# ── Tab 1: Head to Head ──
with tab1:
    tl = sorted(TEAMS.keys())
    ca, cv, cb = st.columns([5, 1, 5])
    with ca:
        team1 = st.selectbox("Team A", tl, index=tl.index("Duke") if "Duke" in tl else 0)
    with cv:
        st.markdown('<div class="vs-badge" style="margin-top:28px;">VS</div>', unsafe_allow_html=True)
    with cb:
        team2 = st.selectbox("Team B", tl, index=tl.index("Michigan") if "Michigan" in tl else 1)

    if team1 and team2 and team1 != team2:
        d1, d2 = TEAMS[team1], TEAMS[team2]
        fm1, fm2 = get_metrics(d1), get_metrics(d2)

        # Fetch live news/injuries for both teams
        news1, news2 = None, None
        if api_key:
            cache_key = f"news_{team1}_{team2}"
            if cache_key not in st.session_state:
                with st.spinner("Searching latest news & injuries..."):
                    st.session_state[cache_key] = (
                        fetch_team_news(api_key, team1),
                        fetch_team_news(api_key, team2),
                    )
            news1, news2 = st.session_state[cache_key]

        col1, col2 = st.columns(2)
        with col1:
            render_report_card(team1, d1, news=news1)
        with col2:
            render_report_card(team2, d2, news=news2)

        # Edge banner
        gpa1, gpa2 = fm1.get("gpa", 0), fm2.get("gpa", 0)
        if gpa1 != gpa2:
            winner = team1 if gpa1 > gpa2 else team2
            loser = team2 if gpa1 > gpa2 else team1
            diff = abs(gpa1 - gpa2)
            strength = "Slight" if diff < 0.4 else ("Clear" if diff < 0.8 else "Strong")
            # Count metric wins
            wins_1 = sum(1 for k in ["m1","m2","m3","m4","m5","m6"]
                        if ord(fm1.get(f"{k}_grade","F")) < ord(fm2.get(f"{k}_grade","F")))
            wins_2 = sum(1 for k in ["m1","m2","m3","m4","m5","m6"]
                        if ord(fm2.get(f"{k}_grade","F")) < ord(fm1.get(f"{k}_grade","F")))
            st.markdown(f"""
            <div class="edge-banner">
                <div class="edge-text">📌 JAKT Edge: {winner.upper()} — {strength} advantage ({winner} wins {max(wins_1,wins_2)} of 6 metrics, GPA {max(gpa1,gpa2):.2f} vs {min(gpa1,gpa2):.2f})</div>
            </div>
            """, unsafe_allow_html=True)

        # Common Opponents
        s1 = SCHEDULES.get(team1, [])
        s2 = SCHEDULES.get(team2, [])
        if s1 and s2:
            ids1 = {g["opp_id"]: g["opp"] for g in s1}
            ids2 = {g["opp_id"]: g["opp"] for g in s2}
            common_ids = set(ids1) & set(ids2)
            if common_ids:
                st.markdown("---")
                st.markdown("#### Common Opponents")
                rows = []
                for oid in common_ids:
                    opp_name = ids1[oid]
                    for g1 in [g for g in s1 if g["opp_id"] == oid]:
                        g2_list = [g for g in s2 if g["opp_id"] == oid]
                        for g2 in g2_list:
                            rows.append({
                                "Opponent": opp_name,
                                f"{team1}": f"{'W' if g1['win'] else 'L'} {g1['pts']}-{g1['opp_pts']}",
                                f"{team2}": f"{'W' if g2['win'] else 'L'} {g2['pts']}-{g2['opp_pts']}",
                            })
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("No common opponents found.")
            else:
                st.markdown("---")
                st.caption("No common opponents this season.")

        # AI Analysis
        st.markdown("---")
        if api_key:
            if st.button("Run AI Matchup Analysis", use_container_width=True, type="primary"):
                with st.spinner("Claude is analyzing this matchup..."):
                    result = call_anthropic_api(api_key, team1, d1, team2, d2, news1, news2)
                    st.markdown(result)
        else:
            st.info("Add your Anthropic API key in the sidebar to unlock AI matchup analysis.")

    elif team1 == team2:
        st.warning("Pick two different teams.")


# ── Tab 2: Full Rankings ──
with tab2:
    rows_list = []
    for n, d in TEAMS.items():
        fm = get_metrics(d)
        ts = d.get("tier_splits") or {}
        t1s = ts.get("Tier1", {})
        rows_list.append({
            "GPA": fm.get("gpa", 0),
            "Team": n,
            "Seed": d["seed"],
            "Region": d["region"],
            "M1": fm.get("m1_grade", ""),
            "M2": fm.get("m2_grade", ""),
            "M3": fm.get("m3_grade", ""),
            "M4": fm.get("m4_grade", ""),
            "M5": fm.get("m5_grade", ""),
            "M6": fm.get("m6_grade", ""),
            "Champ?": "✓" if fm.get("meets_champ_criteria") else "",
            "Record": d["record"],
            "KenPom": d.get("kenpom_rank"),
            "Off Rk": d.get("kenpom_off_rank"),
            "Def Rk": d.get("kenpom_def_rank"),
            "T1 Rec": f"{t1s.get('wins',0)}-{t1s.get('losses',0)}" if t1s.get("games",0) > 0 else "—",
            "T1 Mrg": round(t1s.get("avg_margin", 0), 1) if t1s.get("games",0) > 0 else "—",
            "Consist%": round(ts.get("consistency_pct", 0), 1) if ts.get("consistency_pct", 0) > 0 else "—",
            "Ht": ht_display(d.get("avg_starter_height_in", 0)),
            "Exp": d.get("avg_starter_exp_yrs"),
            "PG": d.get("pg_name", ""),
        })

    df = pd.DataFrame(rows_list).sort_values("GPA", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "#"

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        rf = st.multiselect("Region", ["East", "West", "Midwest", "South"])
    with f2:
        sf = st.slider("Max Seed", 1, 16, 16)
    with f3:
        mg = st.slider("Min GPA", 0.0, 4.0, 0.0, 0.2)
    with f4:
        cc = st.checkbox("Champ Criteria Only")

    fd = df.copy()
    if rf:
        fd = fd[fd["Region"].isin(rf)]
    fd = fd[(fd["Seed"] <= sf) & (fd["GPA"] >= mg)]
    if cc:
        fd = fd[fd["Champ?"] == "✓"]

    st.dataframe(fd, use_container_width=True, height=700)


# Footer
st.markdown("---")
st.caption("JAKT Bracket Intelligence © 2026 · Data: Barttorvik API (4,979 players), KenPom, ESPN, CBS Sports")
