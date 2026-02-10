import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Turni Volontari Dego", layout="centered")
st.title("🚑 Turni Pubblica Assistenza Dego")

# Creazione connessione con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
# 1. Lettura dati dal foglio Turni_Master
try:
    df_master = conn.read(worksheet="Turni_Master", ttl=0)
    
    # Filtriamo solo i turni con posti disponibili (Disp > 0)
    df_disponibili = df_master[df_master['Disp'] > 0]

    if df_disponibili.empty:
        st.warning("Nessun turno disponibile al momento.")
    else:
        st.subheader("Iscriviti a un turno")
        with st.form("form_iscrizione"):
            nome = st.text_input("Nome e Cognome")
            email = st.text_input("Tua Email")
            # Mostra i turni come: 10/02/2026_00-08 (Posti: 6)
            scelta = st.selectbox("Seleziona il turno", df_disponibili['ID_Turno'])
            
            submit = st.form_submit_button("Conferma Iscrizione")

            if submit:
                if nome and email:
                    # Carichiamo il foglio Iscrizioni per aggiungere la riga
                    iscrizioni_attuali = conn.read(worksheet="Iscrizioni", ttl=0)
                    nuova_riga = pd.DataFrame([{
                        "Volontario": nome,
                        "ID_Turno_Riferimento": scelta,
                        "Email_Volontario": email,
                        "Data_Ora_Iscrizione": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    
                    # Unione e aggiornamento
                    updated_iscrizioni = pd.concat([iscrizioni_attuali, nuova_riga], ignore_index=True)
                    conn.update(worksheet="Iscrizioni", data=updated_iscrizioni)
                    
                    st.success(f"Iscrizione registrata per {nome}!")
                    st.balloons()
                else:
                    st.error("Compila tutti i campi!")

except Exception as e:

    st.error("Configurazione in corso... Collega il database nelle impostazioni di Streamlit.")
