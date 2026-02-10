import streamlit as st
import pandas as pd
from github import Github
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Turni Volontari Dego", layout="centered", page_icon="🚑")
st.title("🚑 Turni Pubblica Assistenza Dego")

# --- CONNESSIONE GITHUB (Per Scrivere) ---
def save_to_github(new_data):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        contents = repo.get_contents("iscrizioni.csv")
        
        # Scarica il file CSV attuale
        existing_df = pd.read_csv(contents.download_url)
        # Aggiunge la nuova riga
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        
        # Carica il file aggiornato su GitHub
        repo.update_file(
            contents.path, 
            "Nuova iscrizione volontario", 
            updated_df.to_csv(index=False), 
            contents.sha
        )
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio su GitHub: {e}")
        return False

# --- LOGICA APP ---
try:
    # 1. Lettura Turni da Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_master = conn.read(ttl=0)
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)

    # Filtro turni disponibili
    df_disponibili = df_master[df_master['Disp'] > 0]

    if df_disponibili.empty:
        st.warning("Nessun turno disponibile al momento.")
    else:
        st.subheader("Modulo Iscrizione Rapida")
        with st.form("form_iscrizione"):
            nome = st.text_input("Nome e Cognome")
            turno_scelto = st.selectbox("Seleziona il turno", df_disponibili['ID_Turno'].tolist())
            
            if st.form_submit_button("Conferma Iscrizione"):
                if nome:
                    nuova_riga = pd.DataFrame([{
                        "Volontario": nome,
                        "ID_Turno": turno_scelto,
                        "Data_Iscrizione": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    
                    if save_to_github(nuova_riga):
                        st.success(f"✅ Ottimo lavoro {nome}, iscrizione salvata!")
                        st.balloons()
                        st.cache_data.clear() # Forza aggiornamento dati
                else:
                    st.error("Inserisci il tuo nome.")

    # --- TABELLA ISCRITTI (Sola Lettura) ---
    st.divider()
    st.subheader("Riepilogo Volontari Iscritti")
    
    # Leggiamo il CSV pubblico direttamente da GitHub
    url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
    try:
        df_iscritti = pd.read_csv(url_csv)
        if not df_iscritti.empty:
            st.dataframe(df_iscritti, use_container_width=True, hide_index=True)
        else:
            st.info("Nessuno si è ancora iscritto. Sii il primo!")
    except:
        st.info("In attesa delle prime iscrizioni...")

except Exception as e:
    st.error(f"Errore di sistema: {e}")

