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
    
    # CALENDARIO CON FORMATO ITALIANO
    data_selezionata = st.date_input(
        "Clicca sulla data per vedere i turni", 
        value=datetime.now(),
        format="DD/MM/YYYY"  # <--- Forza il formato italiano nel widget
    )
    
    # Trasformiamo la data in stringa GG/MM/AAAA per cercare nel foglio Google
    data_str = data_selezionata.strftime("%d/%m/%Y")

    # Filtriamo i turni per la data scelta
    mask = df_master['ID_Turno'].str.contains(data_str) & (df_master['Disp'] > 0)
    turni_disponibili = df_master[mask].copy()

    if not turni_disponibili.empty:
        # Estraiamo l'ora e ordiniamo i turni
        turni_disponibili['Ora'] = turni_disponibili['ID_Turno'].str.split('_').str[1]
        turni_disponibili = turni_disponibili.sort_values(by='Ora')
        
        st.info(f"Turni disponibili per il **{data_str}**:")
        
        with st.form("iscrizione_veloce"):
            nome = st.text_input("Tuo Nome e Cognome")
            scelta_ora = st.selectbox("Fascia Oraria", turni_disponibili['Ora'].tolist())
            
            submit = st.form_submit_button("Conferma Iscrizione")
            
            if submit:
                if nome.strip():
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
                    st.error("⚠️ Inserisci il nome!")
    else:
        st.warning(f"Nessun turno disponibile o posti esauriti per il {data_str}.")

    # --- LISTA ISCRITTI ---
    st.divider()
    st.subheader(f"👥 Iscritti del {data_str}")
    url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
    try:
        df_iscritti = pd.read_csv(url_csv)
        # Filtriamo per la data selezionata
        iscritti_oggi = df_iscritti[df_iscritti['ID_Turno'].str.contains(data_str)].copy()
        
        if not iscritti_oggi.empty:
            # Puliamo la visualizzazione togliendo la data dall'ID_Turno per la tabella
            iscritti_oggi['Orario'] = iscritti_oggi['ID_Turno'].str.split('_').str[1]
            st.table(iscritti_oggi[['Volontario', 'Orario']])
        else:
            st.write("_Ancora nessun iscritto per questa data._")
    except:
        st.info("Inizia a iscriverti per vedere qui l'elenco!")

except Exception as e:
    st.error(f"Errore: {e}")
