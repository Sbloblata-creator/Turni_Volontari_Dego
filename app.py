import streamlit as st
import pandas as pd
from github import Github
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Turni Volontari Dego", layout="centered", page_icon="🚑")
st.title("🚑 Turni Pubblica Assistenza Dego")

# --- CONNESSIONE GITHUB ---
def save_to_github(new_data):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        contents = repo.get_contents("iscrizioni.csv")
        existing_df = pd.read_csv(contents.download_url)
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        repo.update_file(contents.path, "Nuova iscrizione", updated_df.to_csv(index=False), contents.sha)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

# --- LOGICA APP ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_master = conn.read(ttl=0)
    df_master.columns = df_master.columns.str.strip()
    
    # Pulizia e conversione
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)
    df_disponibili = df_master[df_master['Disp'] > 0].copy()

    if df_disponibili.empty:
        st.warning("Nessun turno disponibile.")
    else:
        # --- SELEZIONE DOPPIA (DATA E TURNO) ---
        # Dividiamo la colonna ID_Turno (es: 10/02/2026_00-08) in due parti
        # Se la tua colonna 'Data' nel foglio è già separata, possiamo usare quella direttamente.
        # Qui simuliamo la divisione dalla stringa ID_Turno per sicurezza.
        df_disponibili[['Data_Solo', 'Ora_Solo']] = df_disponibili['ID_Turno'].str.split('_', expand=True)

        st.subheader("Modulo Iscrizione")
        
        with st.form("form_iscrizione"):
            nome = st.text_input("Nome e Cognome")
            
            # 1. Selezione Data
            date_disponibili = df_disponibili['Data_Solo'].unique()
            data_scelta = st.selectbox("Seleziona la Data", date_disponibili)
            
            # 2. Selezione Turno (mostra solo le ore di quella data)
            turni_per_data = df_disponibili[df_disponibili['Data_Solo'] == data_scelta]['Ora_Solo'].unique()
            turno_scelto_ora = st.selectbox("Seleziona la Fascia Oraria", turni_per_data)
            
            # Ricostruiamo l'ID originale per il database
            id_finale = f"{data_scelta}_{turno_scelto_ora}"
            
            if st.form_submit_button("Conferma Iscrizione"):
                if nome:
                    nuova_riga = pd.DataFrame([{
                        "Volontario": nome,
                        "ID_Turno": id_finale,
                        "Data_Iscrizione": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    if save_to_github(nuova_riga):
                        st.success(f"Iscrizione registrata per il {data_scelta} ({turno_scelto_ora})")
                        st.balloons()
                        st.cache_data.clear()
                else:
                    st.error("Inserisci il nome.")

    # --- TABELLA RIASSUNTIVA ---
    st.divider()
    st.subheader("Volontari già iscritti")
    url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
    try:
        df_iscritti = pd.read_csv(url_csv)
        if not df_iscritti.empty:
            # Mostriamo la tabella più leggibile
            st.dataframe(df_iscritti, use_container_width=True, hide_index=True)
    except:
        st.info("Nessuna iscrizione presente.")

except Exception as e:
    st.error(f"Errore: {e}")
