import streamlit as st
import pandas as pd

def render_separated_match_tables(df_samples, fav_team='Home', ah_line=-0.50):
    """
    Menampilkan 2 tabel terpisah untuk Half Time (HT) dan Full Time (FT)
    """
    
    # CSS Styling
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
      .ft-badge { background: #1e293b; border: 1px solid #f59e0b; color: #fbbf24; padding: 2px 6px; border-radius: bold; }
      .badge-win { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold; }
      .badge-lose { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold; }
      .pill-yes { background-color: #064e3b; color: #6ee7b7; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
      .pill-no { background-color: #451a03; color: #fdba74; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
    </style>
    """
    
    # ------------------ TABEL 1: HALF TIME (HT) ------------------
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
    for _, r in df_samples.head(20).iterrows():
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

    # ------------------ TABEL 2: FULL TIME (FT) ------------------
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
    for _, r in df_samples.head(20).iterrows():
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

    # Render di Streamlit
    st.markdown(html_ht, unsafe_allow_html=True)
    st.markdown(html_ft, unsafe_allow_html=True)

# Pemanggilan:
# render_separated_match_tables(filtered_df, fav_team=fav_team, ah_line=ah_line)
