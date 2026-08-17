import streamlit as st
import pandas as pd
import numpy as np
import io

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Football Odds & Handicap Analyzer", layout="wide")

@st.cache_data
def load_historical_data():
    """
    Mengunduh dan menggabungkan data pertandingan dari liga-liga utama Eropa
    secara otomatis hingga 10.000+ match.
    """
    seasons = ['2324', '2223', '2122', '2021', '1920', '1819']
    leagues = ['E0', 'SP1', 'I1', 'D1', 'F1']  # EPL, La Liga, Serie A, Bundesliga, Ligue 1
    
    all_matches = []
    for season in seasons:
        for league in leagues:
            url = f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
            try:
                df = pd.read_csv(url)
                cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG', 
                        'HC', 'AC', 'B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']
                existing_cols = [c for c in cols if c in df.columns]
                df_filtered = df[existing_cols].copy()
                all_matches.append(df_filtered)
            except Exception:
                continue
                
    if all_matches:
        combined_df = pd.concat(all_matches, ignore_index=True)
        combined_df.dropna(subset=['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A'], inplace=True)
        
        combined_df['Total_Goals_FT'] = combined_df['FTHG'] + combined_df['FTAG']
        combined_df['Total_Goals_HT'] = combined_df['HTHG'] + combined_df['HTAG']
        combined_df['BTTS'] = (combined_df['FTHG'] > 0) & (combined_df['FTAG'] > 0)
        
        if 'HC' in combined_df.columns and 'AC' in combined_df.columns:
            combined_df['Total_Corners_FT'] = combined_df['HC'] + combined_df['AC']
        else:
            combined_df['Total_Corners_FT'] = np.nan
            
        return combined_df
    else:
        return pd.DataFrame()

def evaluate_asian_handicap(row, ah_line, fav_team='Home'):
    diff = row['FTHG'] - row['FTAG'] if fav_team == 'Home' else row['FTAG'] - row['FTHG']
    effective_diff = diff + ah_line
    
    if effective_diff > 0.25:
        return 'WIN'
    elif effective_diff == 0.25:
        return 'WIN HALF'
    elif effective_diff == 0:
        return 'PUSH'
    elif effective_diff == -0.25:
        return 'LOSE HALF'
    else:
        return 'LOSE'

# Tampilan Utama
st.title("⚽ Football Odds & Asian Handicap Analyzer Pro")
st.write("Analisis presisi 10.000+ pertandingan historis: Matriks Skor Half Time (HT), Full Time (FT), dan Asian Handicap.")

with st.spinner("Mengunduh dataset pertandingan historis..."):
    df_matches = load_historical_data()

# Sidebar Filters
st.sidebar.header("⚙️ Parameter Pertandingan")

if not df_matches.empty:
    st.sidebar.subheader("1. Match Odds (1X2)")
    home_odds = st.sidebar.number_input("Home Odds (1)", min_value=1.0, max_value=20.0, value=1.95, step=0.05)
    draw_odds = st.sidebar.number_input("Draw Odds (X)", min_value=1.0, max_value=20.0, value=3.40, step=0.05)
    away_odds = st.sidebar.number_input("Away Odds (2)", min_value=1.0, max_value=20.0, value=3.80, step=0.05)
    margin = st.sidebar.slider("Toleransi Range Odds (+/-)", 0.05, 0.50, 0.15, step=0.05)

    st.sidebar.subheader("2. Model Asian Handicap (AH)")
    fav_team = st.sidebar.radio("Tim Favorit (Voor):", ['Home', 'Away'])
    ah_line = st.sidebar.selectbox("Garis Handicap (Lines):", 
                                   [0.0, -0.25, -0.50, -0.75, -1.0, -1.25, -1.50, -1.75, -2.0],
                                   index=2)

    # Filter Data
    filtered_df = df_matches[
        (df_matches['B365H'].between(home_odds - margin, home_odds + margin)) &
        (df_matches['B365D'].between(draw_odds - margin, draw_odds + margin)) &
        (df_matches['B365A'].between(away_odds - margin, away_odds + margin))
    ].copy()

    st.subheader(f"📊 Sampel Cocok: {len(filtered_df)} Pertandingan (Dari Total {len(df_matches)} Match)")

    if len(filtered_df) > 0:
        filtered_df['AH_Result'] = filtered_df.apply(lambda r: evaluate_asian_handicap(r, ah_line, fav_team), axis=1)
        ah_win_rate = (filtered_df['AH_Result'].isin(['WIN', 'WIN HALF'])).mean() * 100

        # Card Statistik Utama
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("HT Over 0.5 Goal", f"{(filtered_df['Total_Goals_HT'] > 0.5).mean() * 100:.1f}%")
        with c2:
            st.metric("FT Over 2.5 Goal", f"{(filtered_df['Total_Goals_FT'] > 2.5).mean() * 100:.1f}%")
        with c3:
            st.metric("BTTS Yes Rate", f"{filtered_df['BTTS'].mean() * 100:.1f}%")
        with c4:
            st.metric(f"AH Cover ({fav_team} {ah_line})", f"{ah_win_rate:.1f}%")

        # Tombol Download Excel
        st.markdown("---")
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Analisis_Odds')
        
        st.download_button(
            label="🟢 Download Laporan Analisis (.xlsx)",
            data=output_excel.getvalue(),
            file_name="Laporan_Analisis_Odds.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("---")

        # RENDER 2 TABEL TERPISAH (HT & FT) VIA ST.MARKDOWN
        css_style = """
        <style>
          .table-box { background-color: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 20px; border: 1px solid #1e293b; }
          .section-title { color: #38bdf8; font-weight: bold; font-size: 15px; margin-bottom: 10px; border-left: 4px solid #38bdf8; padding-left: 8px; }
          table.tbl-separate { width: 100%; border-collapse: collapse; color: #e2e8f0; font-size: 13px; }
          table.tbl-separate th { background-color: #1e293b; color: #94a3b8; font-size: 11px; text-transform: uppercase; padding: 8px; border-bottom: 2px solid #334155; }
          table.tbl-separate td { padding: 9px 8px; border-bottom: 1px solid #1e293b; text-align: center; }
          table.tbl-separate tr:nth-child(even) { background-color: #141e33; }
          .team-col { text-align: left !important; font-weight: 600; color: #f8fafc; }
          .ht-badge { background: #1e293b; border: 1px solid #38bdf8; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
          .ft-badge { background: #1e293b; border: 1px solid #f59e0b; color: #fbbf24; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
          .badge-win { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold; }
          .badge-lose { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold; }
          .pill-yes { background-color: #064e3b; color: #6ee7b7; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
          .pill-no { background-color: #451a03; color: #fdba74; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
        </style>
        """
        
        # TABEL 1: HALF TIME (HT)
        html_ht = css_style + """
        <div class="table-box">
          <div class="section-title">⏱️ TABEL 1: ANALISIS SKOR & KINERJA HALF TIME (HT)</div>
          <table class="tbl-separate">
            <thead>
              <tr>
                <th style="text-align:left; padding-left:10px;">Tanggal & Match</th>
                <th>Skor HT</th>
                <th>Total Gol HT</th>
                <th>Status Gol HT</th>
                <th>Pemenang HT</th>
              </tr>
            </thead>
            <tbody>
        """
        for _, r in filtered_df.head(25).iterrows():
            ht_goals = int(r['Total_Goals_HT'])
            ht_status = "<span class='pill-yes'>OVER 0.5 HT</span>" if ht_goals > 0.5 else "<span class='pill-no'>UNDER 0.5 HT</span>"
            if r['HTHG'] > r['HTAG']:
                ht_winner = "<span class='badge-win'>HOME WIN</span>"
            elif r['HTHG'] < r['HTAG']:
                ht_winner = "<span class='badge-lose'>AWAY WIN</span>"
            else:
                ht_winner = "<span style='color:#94a3b8;'>DRAW</span>"

            html_ht += f"""
            <tr>
              <td class="team-col" style="padding-left:10px;">
                <span style="font-size:10px; color:#64748b;">{r.get('Date', '')}</span><br>
                {r['HomeTeam']} <span style="color:#64748b; font-size:11px;">vs</span> {r['AwayTeam']}
              </td>
              <td><span class="ht-badge">{int(r['HTHG'])} - {int(r['HTAG'])}</span></td>
              <td><strong>{ht_goals} Gol</strong></td>
              <td>{ht_status}</td>
              <td>{ht_winner}</td>
            </tr>
            """
        html_ht += "</tbody></table></div>"

        # TABEL 2: FULL TIME (FT)
        html_ft = """
        <div class="table-box">
          <div class="section-title">🏁 TABEL 2: ANALISIS SKOR & KINERJA FULL TIME (FT) & HANDICAP</div>
          <table class="tbl-separate">
            <thead>
              <tr>
                <th style="text-align:left; padding-left:10px;">Tanggal & Match</th>
                <th>Skor FT</th>
                <th>Total Gol FT</th>
                <th>BTTS FT</th>
                <th>Corner FT (H-A)</th>
                <th>Hasil Asian Handicap</th>
              </tr>
            </thead>
            <tbody>
        """
        for _, r in filtered_df.head(25).iterrows():
            ft_goals = int(r['Total_Goals_FT'])
            ou_tag = "<span style='color:#4ade80; font-size:10px;'>(O 2.5)</span>" if ft_goals > 2.5 else "<span style='color:#64748b; font-size:10px;'>(U 2.5)</span>"
            btts_tag = "<span class='pill-yes'>YES</span>" if r['BTTS'] else "<span class='pill-no'>NO</span>"
            
            ah_res = r['AH_Result']
            ah_badge = f"<span class='badge-win'>✅ {ah_res}</span>" if ah_res in ['WIN', 'WIN HALF'] else f"<span class='badge-lose'>❌ {ah_res}</span>"
            
            hc = int(r['HC']) if 'HC' in r and pd.notnull(r['HC']) else 0
            ac = int(r['AC']) if 'AC' in r and pd.notnull(r['AC']) else 0

            html_ft += f"""
            <tr>
              <td class="team-col" style="padding-left:10px;">
                <span style="font-size:10px; color:#64748b;">{r.get('Date', '')}</span><br>
                {r['HomeTeam']} <span style="color:#64748b; font-size:11px;">vs</span> {r['AwayTeam']}
              </td>
              <td><span class="ft-badge">{int(r['FTHG'])} - {int(r['FTAG'])}</span></td>
              <td><strong>{ft_goals} Gol</strong> {ou_tag}</td>
              <td>{btts_tag}</td>
              <td><span style="color:#38bdf8; font-weight:bold;">{hc+ac}</span> <span style="font-size:10px; color:#64748b;">({hc}-{ac})</span></td>
              <td>{ah_badge}</td>
            </tr>
            """
        html_ft += "</tbody></table></div>"

        st.markdown(html_ht, unsafe_allow_html=True)
        st.markdown(html_ft, unsafe_allow_html=True)
    else:
        st.warning("Tidak ada pertandingan yang cocok dengan rentang odds tersebut.")
else:
    st.error("Gagal memuat dataset.")
