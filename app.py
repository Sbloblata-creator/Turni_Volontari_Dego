import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configurazione Pagina
st.set_page_config(page_title="Turni Volontari Dego", layout="centered")
st.title("🚑 Turni Pubblica Assistenza Dego")

# Creazione connessione con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Lettura dati dal foglio Turni_Master
try:
    # Carichiamo il foglio principale
    df_master = conn.read(ttl=0)
    
    # PULIZIA DATI: Trasformiamo la colonna 'Disp' in numeri, gestendo eventuali errori
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)

    # Filtriamo solo i turni con posti disponibili (Disp > 0)
    df_disponibili = df_master[df_master['Disp'] > 0]

    if df_disponibili.empty:
        st.warning("Al momento non ci sono turni con posti disponibili.")
    else:
        st.subheader("Modulo di Iscrizione")
        
        with st.form("form_iscrizione"):
            nome = st.text_input("Nome e Cognome")
            email = st.text_input("Indirizzo Email")
            
            # Creiamo una lista di opzioni chiara per il volontario
            lista_turni = df_disponibili['ID_Turno'].tolist()
            scelta = st.selectbox("Seleziona il turno desiderato", lista_turni)
            
            submit = st.form_submit_button("Conferma Iscrizione")

            if submit:
                if nome.strip() and email.strip():
                    # 1. Carichiamo il foglio Iscrizioni per aggiungere la riga
                    try:
                        iscrizioni_attuali = conn.read(worksheet=1, ttl=0)
                        
                        nuova_riga = pd.DataFrame([{
                            "Volontario": nome,
                            "ID_Turno_Riferimento": scelta,
                            "Email_Volontario": email,
                            "Data_Ora_Iscrizione": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                        }])
                        
                        # 2. Uniamo i dati e carichiamo su Google
                        updated_iscrizioni = pd.concat([iscrizioni_attuali, nuova_riga], ignore_index=True)
                        conn.update(worksheet="Iscrizioni", data=updated_iscrizioni)
                        
                        st.success(f"✅ Grazie {nome}! Iscrizione registrata con successo.")
                        st.balloons()
                        st.info("Puoi chiudere questa pagina o ricaricarla per un'altra iscrizione.")
                    except Exception as e_write:
                        st.error(f"Errore durante la scrittura: {e_write}")
                else:
                    st.error("⚠️ Per favore, inserisci sia il nome che l'email.")

except Exception as e:
    st.error(f"⚠️ Errore Tecnico: {e}")
    st.info("Verifica che il foglio 'Turni_Master' sia compilato correttamente e che i Secret siano salvati.")

