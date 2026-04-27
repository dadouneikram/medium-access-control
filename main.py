import streamlit as st
import pandas as pd
import numpy as np
from simulation import simuler 


st.set_page_config(page_title="Simulateur MAC - Dadoune & Debbihi", layout="wide")

st.title("📊 Simulateur de protocole MAC (Exponential Backoff)")
st.markdown("""
Ce tableau de bord permet de simuler et d'analyser les performances d'un réseau de $N$ stations 
utilisant l'algorithme de repli exponentiel.
""")


st.sidebar.header("Configuration de la Simulation")

N = st.sidebar.slider("Nombre de stations (N)", 1, 100, 10)
K = st.sidebar.slider("Capacité des files (K)", 1, 50, 10)
lambd = st.sidebar.slider("Taux d'arrivée (λ)", 0.01, 2.0, 0.5)
tau = st.sidebar.number_input("Paramètre de temps moyen (τ)", value=1.0)
temps_max = st.sidebar.number_input("Durée de simulation (unités de temps)", value=1000)


if st.sidebar.button("Lancer la Simulation"):
    with st.spinner('Simulation en cours...'):
       
        debit_final = simuler(N, K, lambd, tau, temps_max)
        
        
        st.header("📈 Résultats de la simulation")
        
       
        col1, col2, col3 = st.columns(3)
        col1.metric("Débit Final (d)", f"{debit_final:.4f} pqt/ut")
        col2.metric("Charge du réseau (N * λ)", f"{N * lambd:.2f}")
        col3.metric("Efficacité", f"{(debit_final/1)*100:.1f} %")

      
        st.info(f"Pour N={N} et λ={lambd}, le système a réussi à transmettre {int(debit_final * temps_max)} paquets.")


st.divider()
st.subheader("📝 Études demandées")
st.write("Utilisez les options ci-dessous pour générer les courbes de performance requises par le sujet.")

if st.button("Tracer le débit en fonction de λ"):
    st.write("Calcul en cours pour λ variant de 0.1 à 2.0...")
    
    valeurs_lambda = np.linspace(0.1, 2.0, 10)
    resultats_debit = []
    
    for l in valeurs_lambda:
        d = simuler(N, K, l, tau, temps_max)
        resultats_debit.append(d)
    
   
    df_chart = pd.DataFrame({
        'Lambda (λ)': valeurs_lambda,
        'Débit (d)': resultats_debit
    })
    st.line_chart(df_chart.set_index('Lambda (λ)'))