import streamlit as st
import pandas as pd
from github import Github
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Turni Volontari Dego", layout="centered", page_icon="🚑")
st.title("🚑 Turni Pubblica Assistenza Dego")

# --- FUNZIONE SALVATAGGIO GITHUB ---
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
        st.error(f"Errore GitHub: {e}")
        return False

# --- LOGICA PRINCIPALE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_master = conn.read(ttl=0)
    df_master.columns = df_master.columns.str.strip()
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)

    st.subheader("📅 Seleziona il giorno")
    # CALENDARIO GRAFICO
    data_selezionata = st.date_input("Clicca sulla data per vedere i turni", datetime.now())
    data_str = data_selezionata.strftime("%d/%m/%Y")

    # Filtriamo i turni per la data scelta nel calendario
    # Cerchiamo nel foglio se esiste quella data nella colonna ID_Turno o in una colonna Data
    mask = df_master['ID_Turno'].str.contains(data_str) & (df_master['Disp'] > 0)
    turni_disponibili = df_master[mask].copy()

    if not turni_disponibili.empty:
        # Estraiamo solo l'ora dall'ID_Turno (quello dopo l'underscore)
        turni_disponibili['Ora'] = turni_disponibili['ID_Turno'].str.split('_').str[1]
        
        st.success(f"Turni disponibili per il {data_str}:")
        
        with st.form("iscrizione_veloce"):
            nome = st.text_input("Tuo Nome e Cognome")
            scelta_ora = st.selectbox("Fascia Oraria", turni_disponibili['Ora'].tolist())
            
            submit = st.form_submit_button("Conferma Iscrizione")
            
            if submit:
                if nome:
                    id_finale = f"{data_str}_{scelta_ora}"
                    nuova_riga = pd.DataFrame([{
                        "Volontario": nome,
                        "ID_Turno": id_finale,
                        "Data_Iscrizione": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    
                    if save_to_github(nuova_riga):
                        st.success(f"✅ Iscrizione completata per il {data_str}!")
                        st.balloons()
                        st.cache_data.clear()
                else:
                    st.error("Inserisci il nome!")
    else:
        st.warning(f"Spiacenti, nessun turno inserito o posti esauriti per il {data_str}.")

    # --- LISTA ISCRITTI ---
    st.divider()
    st.subheader("👥 Chi è già in servizio")
    url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
    try:
        df_iscritti = pd.read_csv(url_csv)
        # Filtriamo per mostrare solo quelli della data selezionata per pulizia
        iscritti_oggi = df_iscritti[df_iscritti['ID_Turno'].str.contains(data_str)]
        if not iscritti_oggi.empty:
            st.table(iscritti_oggi[['Volontario', 'ID_Turno']])
        else:
            st.write("Nessun iscritto per questa data.")
    except:
        pass

except Exception as e:
    st.error(f"Configura i dati nel foglio Google: {e}")
