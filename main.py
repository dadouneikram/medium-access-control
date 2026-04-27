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
        # --- MISE À JOUR : On récupère les 3 valeurs ---
        debit_final, moyen_clients, perte = simuler(N, K, lambd, tau, temps_max)
        
        st.header("📈 Résultats de la simulation")
        
        # Affichage des 3 métriques demandées
        col1, col2, col3 = st.columns(3)
        col1.metric("Débit Final (d)", f"{debit_final:.4f} pqt/ut")
        col2.metric("Nb moyen clients (L)", f"{moyen_clients:.2f}")
        col3.metric("Taux de Perte (%)", f"{perte*100:.2f} %")

        st.info(f"Pour N={N} et λ={lambd}, le système a réussi à transmettre {int(debit_final * temps_max)} paquets.")

st.divider()
st.subheader("📝 Études demandées")

# --- BOUTON POUR TRACER TOUTES LES COURBES ---
if st.button("Tracer les courbes de performance en fonction de λ"):
    st.write("Calcul en cours pour λ variant de 0.1 à 2.0...")
    
    valeurs_lambda = np.linspace(0.1, 2.0, 15)
    list_debit = []
    list_clients = []
    list_perte = []
    
    for l in valeurs_lambda:
        # On récupère les 3 infos à chaque fois
        d, c, p = simuler(N, K, l, tau, temps_max)
        list_debit.append(d)
        list_clients.append(c)
        list_perte.append(p)
    
    # Préparation des données pour les graphiques
    df_results = pd.DataFrame({
        'Lambda (λ)': valeurs_lambda,
        'Débit': list_debit,
        'Nb Clients': list_clients,
        'Taux de Perte': list_perte
    }).set_index('Lambda (λ)')

    # Affichage des graphiques l'un en dessous de l'autre
    st.write("### Évolution du Débit")
    st.line_chart(df_results['Débit'])
    
    st.write("### Évolution du Nombre de Clients")
    st.line_chart(df_results['Nb Clients'])
    
    st.write("### Évolution du Taux de Perte")
    st.line_chart(df_results['Taux de Perte'])