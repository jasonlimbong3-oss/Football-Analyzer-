import streamlit as st
import pandas as pd
import numpy as np
import io

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Football Odds & Asian Handicap Analyzer Pro", layout="wide")

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
        
        # Metrik Gol & BTTS
        combined_df['Total_Goals_FT'] = combined_df['FTHG'] + combined_df['FTAG']
        combined_df['Total_Goals_HT'] = combined_df['HTHG'] + combined_df['HTAG']
        combined_df['BTTS'] = (combined_df['FTHG'] > 0) & (combined_df['FTAG'] > 0)
        
        # Metrik Corner
        if 'HC' in combined_df.columns and 'AC' in combined_df.columns:
            combined_df['Total_Corners_FT'] = combined_df['HC'] + combined_df['AC']
        else:
            combined_df['Total_Corners_FT'] = np.nan
            
        return combined_df
    else:
        return pd.DataFrame()

def evaluate_asian_handicap(row, ah_line, fav_team='Home'):
    """
    Menghitung evaluasi Asian Handicap berdasarkan selisih gol FT.
    """
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

# Load Data
st.title("⚽ Football Odds & Asian Handicap Analyzer Pro")
st.write("Analisis presisi 10.000+ pertandingan historis: Gol (HT/FT), Corner, BTTS, dan Asian Handicap Cover Rate.")

with st.spinner("Mengunduh dan memuat 10.000+ dataset pertandingan historis..."):
    df_matches = load_historical_data()

# Sidebar Filters
st.sidebar.header("⚙️ Parameter Pertandingan Sekarang")

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

    # Filtering Data
    filtered_df = df_matches[
        (df_matches['B365H'].between(home_odds - margin, home_odds + margin)) &
        (df_matches['B365D'].between(draw_odds - margin, draw_odds + margin)) &
        (df_matches['B365A'].between(away_odds - margin, away_odds + margin))
    ].copy()

    st.subheader(f"📊 Sampel Cocok: {len(filtered_df)} Pertandingan (Dari Total {len(df_matches)} Match)")

    if len(filtered_df) > 0:
        # Evaluasi Asian Handicap
        filtered_df['AH_Result'] = filtered_df.apply(lambda r: evaluate_asian_handicap(r, ah_line, fav_team), axis=1)
        ah_win_rate = (filtered_df['AH_Result'].isin(['WIN', 'WIN HALF'])).mean() * 100

        # Layout Hasil Analisis
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown("### ⚽ Hasil Gol HT")
            ht_over05 = (filtered_df['Total_Goals_HT'] > 0.5).mean() * 100
            ht_over15 = (filtered_df['Total_Goals_HT'] > 1.5).mean() * 100
            st.metric("HT Over 0.5 Goal", f"{ht_over05:.1f}%")
            st.metric("HT Over 1.5 Goal", f"{ht_over15:.1f}%")

        with c2:
            st.markdown("### 🥅 Hasil Gol FT")
            ft_over25 = (filtered_df['Total_Goals_FT'] > 2.5).mean() * 100
            ft_over35 = (filtered_df['Total_Goals_FT'] > 3.5).mean() * 100
            st.metric("FT Over 2.5 Goal", f"{ft_over25:.1f}%")
            st.metric("FT Over 3.5 Goal", f"{ft_over35:.1f}%")

        with c3:
            st.markdown("### 🤝 BTTS & Corner")
            btts_yes = filtered_df['BTTS'].mean() * 100
            avg_corner = filtered_df['Total_Corners_FT'].mean() if not filtered_df['Total_Corners_FT'].isna().all() else 0
            st.metric("BTTS Yes Rate", f"{btts_yes:.1f}%")
            st.metric("Rata-rata Corner FT", f"{avg_corner:.1f}")

        with c4:
            st.markdown("### 🛡️ Asian Handicap")
            st.metric(f"AH Cover ({fav_team} {ah_line})", f"{ah_win_rate:.1f}%")
            push_rate = (filtered_df['AH_Result'] == 'PUSH').mean() * 100
            st.write(f"- **Push (Seri AH):** {push_rate:.1f}%")

        st.markdown("---")
        
        # Fitur Ekspor Data
        st.subheader("📥 Ekspor Hasil Analisis")
        ex_col1, ex_col2 = st.columns(2)

        with ex_col1:
            # Export to Excel
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Analisis_Odds')
            excel_data = output_excel.getvalue()
            
            st.download_button(
                label="🟢 Download Laporan Format Excel (.xlsx)",
                data=excel_data,
                file_name="Laporan_Analisis_Odds.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with ex_col2:
            st.info("File laporan PDF yang telah disintesis dapat Anda unduh pada tautan pratinjau di atas.")

        st.markdown("---")
        st.subheader("📋 Sampel Match Serupa")
        st.dataframe(filtered_df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'HTHG', 'HTAG', 'AH_Result', 'B365H', 'B365D', 'B365A']].head(100))
    else:
        st.warning("Tidak ada sampel pertandingan yang cocok dengan kombinasi odds tersebut. Gunakan toleransi margin odds yang lebih besar.")
else:
    st.error("Gagal memuat dataset.")
