import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configurazione Pagina
st.set_page_config(page_title="Turni Volontari Dego", layout="centered")
st.title("🚑 Turni Pubblica Assistenza Dego")

# Creazione connessione con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. LETTURA DATI DAL FOGLIO TURNI_MASTER
try:
    df_master = conn.read(worksheet="Turni_Master", ttl=0)
    
    # Pulizia dati per evitare errori di calcolo
    df_master['Disp'] = pd.to_numeric(df_master['Disp'], errors='coerce').fillna(0)

    # Filtriamo solo i turni con posti disponibili
    df_disponibili = df_master[df_master['Disp'] > 0]

    if df_disponibili.empty:
        st.warning("Al momento non ci sono turni con posti disponibili.")
    else:
        st.subheader("Modulo di Iscrizione")
        
        with st.form("form_iscrizione"):
            nome = st.text_input("Nome e Cognome")
            email = st.text_input("Indirizzo Email")
            
            lista_turni = df_disponibili['ID_Turno'].tolist()
            scelta = st.selectbox("Seleziona il turno desiderato", lista_turni)
            
            submit = st.form_submit_button("Conferma Iscrizione")

            if submit:
                if nome.strip() and email.strip():
                    try:
                        # Prepariamo la nuova riga
                        nuova_riga = pd.DataFrame([{
                            "Volontario": nome,
                            "ID_Turno_Riferimento": scelta,
                            "Email_Volontario": email,
                            "Data_Ora_Iscrizione": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                        }])
                        
                        # Proviamo a leggere il foglio Iscrizioni
                        try:
                            # Se il foglio esiste ed è popolato
                            iscrizioni_attuali = conn.read(worksheet="Iscrizioni", ttl=0)
                            # Se il foglio è totalmente vuoto, conn.read potrebbe restituire un DF senza colonne
                            if iscrizioni_attuali.empty or len(iscrizioni_attuali.columns) < 2:
                                updated_iscrizioni = nuova_riga
                            else:
                                updated_iscrizioni = pd.concat([iscrizioni_attuali, nuova_riga], ignore_index=True)
                        except:
                            # Se il foglio non è accessibile o non esiste, partiamo dalla nuova riga
                            updated_iscrizioni = nuova_riga
                        
                        # SCRITTURA: Invio dati al foglio Iscrizioni
                        conn.update(worksheet="Iscrizioni", data=updated_iscrizioni)
                        
                        st.success(f"✅ Grazie {nome}! Iscrizione registrata con successo nel foglio Iscrizioni.")
                        st.balloons()
                        st.info("Aggiorna la pagina se vuoi inserire un nuovo turno.")
                        
                    except Exception as e_write:
                        st.error(f"Errore durante l'invio dei dati: {e_write}")
                        st.info("Verifica che nel Google Sheet esista una linguetta chiamata esattamente: Iscrizioni")
                else:
                    st.error("⚠️ Inserisci sia il nome che l'email.")

except Exception as e:
    st.error(f"⚠️ Errore Tecnico in lettura: {e}")
