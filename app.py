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
    
    # Pulizia dati: rendiamo la colonna Disp numerica e ID_Turno stringa
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)
    df_master['ID_Turno'] = df_master['ID_Turno'].astype(str).str.strip()

    st.subheader("📅 Seleziona il giorno")
    data_selezionata = st.date_input("Scegli la data", value=datetime.now(), format="DD/MM/YYYY")
    
    # Formati di ricerca
    data_str_con_zero = data_selezionata.strftime("%d/%m/%Y")
    data_str_senza_zero = f"{data_selezionata.day}/{data_selezionata.month}/{data_selezionata.year}"

    # Filtro turni disponibili (6 posti max definiti nel foglio)
    mask = (df_master['ID_Turno'].str.contains(data_str_con_zero) | 
            df_master['ID_Turno'].str.contains(data_str_senza_zero)) & (df_master['Disp'] > 0)
    
    turni_disponibili = df_master[mask].copy()

    if not turni_disponibili.empty:
        # Estraiamo l'orario (la parte dopo il _)
        turni_disponibili['Ora'] = turni_disponibili['ID_Turno'].str.split('_').str[1]
        
        # Ordiniamo i turni secondo la tua sequenza specifica
        ordine_turni = {"00-08": 1, "08-14": 2, "14-18": 3, "18-21": 4, "21-24": 5}
        turni_disponibili['Ordine'] = turni_disponibili['Ora'].map(ordine_turni)
        turni_disponibili = turni_disponibili.sort_values('Ordine')

        st.info(f"Turni per il {data_str_con_zero} (Posti disponibili: 6 per turno)")
        
        with st.form("iscrizione"):
            nome = st.text_input("Tuo Nome e Cognome")
            scelta_ora = st.selectbox("Seleziona Fascia Oraria", turni_disponibili['Ora'].tolist())
            
            if st.form_submit_button("Conferma Iscrizione"):
                if nome.strip():
                    nuova_riga = pd.DataFrame([{
                        "Volontario": nome,
                        "ID_Turno": f"{data_str_con_zero}_{scelta_ora}",
                        "Data_Iscrizione": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    if save_to_github(nuova_riga):
                        st.success(f"✅ Iscrizione salvata per il turno {scelta_ora}")
                        st.balloons()
                        st.cache_data.clear()
                else:
                    st.error("Inserisci il tuo nome!")
    else:
        st.warning(f"Nessun turno trovato per il {data_str_con_zero}. Verifica il foglio Google.")

    # --- TABELLA ISCRITTI ---
    st.divider()
    st.subheader(f"👥 Iscritti del {data_str_con_zero}")
    try:
        url_csv = f"https://raw.githubusercontent.com/{st.secrets['REPO_NAME']}/main/iscrizioni.csv"
        df_iscritti = pd.read_csv(url_csv)
        iscritti_oggi = df_iscritti[df_iscritti['ID_Turno'].str.contains(data_str_con_zero)].copy()
        if not iscritti_oggi.empty:
            iscritti_oggi['Orario'] = iscritti_oggi['ID_Turno'].str.split('_').str[1]
            st.table(iscritti_oggi[['Volontario', 'Orario']])
        else:
            st.write("_Nessun iscritto._")
    except:
        pass

except Exception as e:
    st.error(f"Errore: {e}")
