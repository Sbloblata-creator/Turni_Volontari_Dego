import streamlit as st
import pandas as pd
from github import Github
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Turni Volontari Dego", layout="centered", page_icon="🚑")
st.title("🚑 Turni Pubblica Assistenza Dego")

# --- FUNZIONE SALVATAGGIO SU GITHUB ---
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
        st.error(f"Errore tecnico GitHub: {e}")
        return False

# --- LOGICA APPLICATIVO ---
try:
    # Connessione a Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leggiamo solo le prime due colonne (A e B) per evitare confusione con i tuoi appunti
    df_master = conn.read(ttl=0, usecols=[0, 1])
    df_master.columns = ['ID_Turno', 'Disp']
    
    # Pulizia dati
    df_master['ID_Turno'] = df_master['ID_Turno'].astype(str).str.strip()
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)

    # Selezione Data con Calendario Italiano
    st.subheader("📅 Seleziona il giorno del servizio")
    data_selezionata = st.date_input("Scegli una data", value=datetime.now(), format="DD/MM/YYYY")
    data_str = data_selezionata.strftime("%d/%m/%Y")

    # Filtro turni per la data scelta
    mask = (df_master['ID_Turno'].str.contains(data_str)) & (df_master['Disp'] > 0)
    turni_giorno = df_master[mask].copy()

    if not turni_giorno.empty:
        # Estraiamo l'orario (es. 08-14)
        turni_giorno['Ora'] = turni_giorno['ID_Turno'].str.split('_').str[1]
        
        # Ordiniamo i turni secondo la tua sequenza specifica
        ordine_pref = {"00-08": 1, "08-14": 2, "14-18": 3, "18-21": 4, "21-24": 5}
        turni_giorno['Priorita'] = turni_giorno['Ora'].map(ordine_pref)
        turni_giorno = turni_giorno.sort_values('Priorita')

        st.info(f"Posti disponibili per il **{data_str}** (Massimo 6 volontari per fascia)")
        
        with st.form("form_volontario"):
            nome = st.text_input("Inserisci Nome e Cognome")
            ora_scelta = st.selectbox("Seleziona la fascia oraria", turni_giorno['Ora'].tolist())
            
            if st.form_submit_button("CONFERMA ISCRIZIONE"):
                if nome.strip():
                    nuova_iscrizione = pd.DataFrame([{
                        "Volontario": nome.upper(), # Salviamo in maiuscolo per ordine
                        "ID_Turno": f"{data_str}_{ora_scelta}",
                        "Data_Inserimento": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    
                    if save_to_github(nuova_iscrizione):
                        st.success(f"✅ Grazie {nome}! Ti sei iscritto per il turno {ora_scelta}.")
                        st.balloons()
                        st.cache_data.clear()
                else:
                    st.warning("⚠️ Per favore, inserisci il tuo nome prima di confermare.")
    else:
        st.error(f"Nessun turno configurato nel foglio Google per il giorno {data_str}.")

    # --- VISUALIZZAZIONE ISCRITTI ---
    st.divider()
    st.subheader(f"👥 Volontari in servizio il {data_str}")
    
    try:
        url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
        df_iscritti = pd.read_csv(url_csv)
        # Filtro per la data corrente
        iscritti_oggi = df_iscritti[df_iscritti['ID_Turno'].str.contains(data_str)].copy()
        
        if not iscritti_oggi.empty:
            iscritti_oggi['Orario'] = iscritti_oggi['ID_Turno'].str.split('_').str[1]
            # Mostriamo una tabella pulita
            st.table(iscritti_oggi[['Orario', 'Volontario']].sort_values('Orario'))
        else:
            st.write("_Nessun volontario ancora iscritto per questa data._")
    except:
        st.info("Il database iscrizioni è in fase di inizializzazione.")

except Exception as e:
    st.error(f"Errore di connessione ai dati: {e}")
