import streamlit as st
import pandas as pd
import numpy as np
from simulation import simuler, simuler_multiple

st.set_page_config(page_title="Simulateur MAC - Exponential Backoff", layout="wide")

# ── CSS minimal pour un rendu propre ──────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stMetric { background: #f8f9fa; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

st.title("📡 Simulateur MAC — Exponential Backoff")
st.markdown("""
Simulation d'un réseau de $N$ stations partageant un canal unique avec
l'algorithme de **repli exponentiel** (Ethernet / 802.11).
""")

# ── Barre latérale ────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Paramètres")
N      = st.sidebar.slider("Nombre de stations (N)", 1, 100, 10)
K      = st.sidebar.slider("Capacité des files (K)", 1, 50, 10)
lambd  = st.sidebar.slider("Taux d'arrivée λ", 0.01, 2.0, 0.3, step=0.01)
tau    = st.sidebar.number_input("Paramètre τ (backoff moyen de base)", value=1.0, min_value=0.01)
temps_max = st.sidebar.number_input("Durée de simulation (ut)", value=2000, min_value=100)

st.sidebar.markdown("---")
st.sidebar.markdown("**Études paramétriques**")
nb_pts_lambda = st.sidebar.slider("Points pour courbe en λ", 5, 30, 15)
n_max_etude   = st.sidebar.slider("N max pour courbe en N", 5, 80, 40)
nb_runs_ic    = st.sidebar.slider("Réplications pour IC 95%", 5, 30, 10)

# ══════════════════════════════════════════════════════════════════════════════
# 1. SIMULATION UNIQUE — courbes temporelles
# ══════════════════════════════════════════════════════════════════════════════
st.header("1 — Évolution temporelle (paramètres fixes)")

if st.button("▶ Lancer la simulation", type="primary"):
    with st.spinner("Simulation en cours…"):
        historique, d_final, clients_final, perte_finale = simuler(
            N, K, lambd, tau, temps_max
        )

    df_hist = pd.DataFrame(historique).set_index("t")

    col1, col2, col3 = st.columns(3)
    col1.metric("Débit final  d(N,K,λ,τ)", f"{d_final:.4f} pqt/ut")
    col2.metric("Nb moyen clients  L",      f"{clients_final:.3f}")
    col3.metric("Taux de perte",            f"{perte_finale*100:.2f} %")

    # n(t)/t
    st.subheader("Débit n(t)/t en fonction du temps")
    st.markdown(
        "Cette courbe doit converger vers $d(N,K,\\lambda,\\tau)$ "
        "quand $t \\to \\infty$."
    )
    st.line_chart(df_hist["debit"], use_container_width=True)

    # Nombre moyen de clients
    st.subheader("Nombre moyen de clients en fonction du temps")
    st.line_chart(df_hist["nb_clients"], use_container_width=True)

    # Taux de perte
    st.subheader("Taux de perte en fonction du temps")
    st.line_chart(df_hist["taux_perte"], use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 2. COURBE d(N,K,λ,τ) EN FONCTION DE λ  (N fixé)
# ══════════════════════════════════════════════════════════════════════════════
st.header("2 — Débit en fonction de λ  (N fixé)")

if st.button("📈 Tracer d en fonction de λ"):
    valeurs_lambda = np.linspace(0.05, 2.0, nb_pts_lambda)
    list_debit, list_clients, list_perte = [], [], []

    bar = st.progress(0, text="Calcul…")
    for idx, l in enumerate(valeurs_lambda):
        _, d, c, p = simuler(N, K, l, tau, temps_max)
        list_debit.append(d)
        list_clients.append(c)
        list_perte.append(p)
        bar.progress((idx + 1) / len(valeurs_lambda),
                     text=f"λ = {l:.2f}  →  débit = {d:.4f}")

    bar.empty()

    df_lambda = pd.DataFrame({
        "Débit":         list_debit,
        "Nb clients":    list_clients,
        "Taux de perte": list_perte,
    }, index=pd.Index(np.round(valeurs_lambda, 3), name="λ"))

    st.subheader("Débit d(N,K,λ,τ) vs λ")
    st.line_chart(df_lambda["Débit"], use_container_width=True)

    st.subheader("Nombre moyen de clients vs λ")
    st.line_chart(df_lambda["Nb clients"], use_container_width=True)

    st.subheader("Taux de perte vs λ")
    st.line_chart(df_lambda["Taux de perte"], use_container_width=True)

    st.dataframe(df_lambda.style.format("{:.4f}"), use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 3. COURBE d(N,K,λ,τ) EN FONCTION DE N  (λ fixé)
# ══════════════════════════════════════════════════════════════════════════════
st.header("3 — Débit en fonction de N  (λ fixé)")

if st.button("📈 Tracer d en fonction de N"):
    valeurs_N = list(range(1, n_max_etude + 1))
    list_debit, list_perte = [], []

    bar = st.progress(0, text="Calcul…")
    for idx, n in enumerate(valeurs_N):
        _, d, _, p = simuler(n, K, lambd, tau, temps_max)
        list_debit.append(d)
        list_perte.append(p)
        bar.progress((idx + 1) / len(valeurs_N),
                     text=f"N = {n}  →  débit = {d:.4f}")

    bar.empty()

    df_N = pd.DataFrame({
        "Débit":         list_debit,
        "Taux de perte": list_perte,
    }, index=pd.Index(valeurs_N, name="N"))

    st.subheader("Débit d(N,K,λ,τ) vs N")
    st.line_chart(df_N["Débit"], use_container_width=True)

    st.subheader("Taux de perte vs N")
    st.line_chart(df_N["Taux de perte"], use_container_width=True)

    n_optimal_simple = valeurs_N[int(np.argmax(list_debit))]
    st.success(
        f"N estimé maximisant le débit (sans IC) : **N = {n_optimal_simple}** "
        f"avec débit = {max(list_debit):.4f} pqt/ut"
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 4. N OPTIMAL AVEC INTERVALLE DE CONFIANCE À 95 %
# ══════════════════════════════════════════════════════════════════════════════
st.header("4 — N optimal avec intervalle de confiance à 95 %")
st.markdown(f"""
Pour chaque valeur de N, on lance **{nb_runs_ic} réplications** indépendantes
et on calcule la moyenne du débit ainsi que son intervalle de confiance Student
à 95 %.
""")

if st.button(f"🔬 Calculer N optimal (IC 95%, {nb_runs_ic} runs par N)"):
    valeurs_N = list(range(1, n_max_etude + 1))
    moyennes, demi_ics = [], []

    bar = st.progress(0, text="Réplications en cours…")
    for idx, n in enumerate(valeurs_N):
        m, ic = simuler_multiple(n, K, lambd, tau, temps_max, nb_runs=nb_runs_ic)
        moyennes.append(m)
        demi_ics.append(ic)
        bar.progress((idx + 1) / len(valeurs_N),
                     text=f"N = {n}  →  débit moyen = {m:.4f} ± {ic:.4f}")

    bar.empty()

    moyennes  = np.array(moyennes)
    demi_ics  = np.array(demi_ics)
    borne_sup = moyennes + demi_ics
    borne_inf = moyennes - demi_ics

    df_ic = pd.DataFrame({
        "Débit moyen":  moyennes,
        "Borne inf 95%": borne_inf,
        "Borne sup 95%": borne_sup,
        "Demi-IC":       demi_ics,
    }, index=pd.Index(valeurs_N, name="N"))

    st.subheader("Débit moyen ± IC 95% en fonction de N")
    # On trace les 3 séries pour visualiser l'enveloppe de confiance
    st.line_chart(
        df_ic[["Débit moyen", "Borne inf 95%", "Borne sup 95%"]],
        use_container_width=True
    )

    idx_opt = int(np.argmax(moyennes))
    n_opt   = valeurs_N[idx_opt]
    d_opt   = moyennes[idx_opt]
    ic_opt  = demi_ics[idx_opt]

    st.success(
        f"**N optimal = {n_opt}** — débit moyen = **{d_opt:.4f} ± {ic_opt:.4f}** pqt/ut "
        f"(IC 95%, {nb_runs_ic} réplications)"
    )

    st.dataframe(df_ic.style.format("{:.5f}").highlight_max(
        subset=["Débit moyen"], color="#c6f6d5"
    ), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 5. VALIDATION THÉORIQUE (bonus rapport)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.header("5 — Validation théorique")
st.markdown("""
**Cas N = 1, K grand, λ < 1 :** une seule station, jamais de collision.
Le débit théorique est $d = \\lambda$ : tous les paquets passent sans perte ni collision,
et la station émet exactement au rythme des arrivées.
""")

if st.button("✅ Vérifier le cas N=1 (validation)"):
    lambda_test = lambd
    d_theorique = min(lambda_test, 1.0)  # débit = lambda si lambda < 1 (système stable)

    with st.spinner("Simulation N=1…"):
        _, d_sim, _, _ = simuler(1, 50, lambda_test, tau, max(temps_max, 5000))

    col1, col2, col3 = st.columns(3)
    col1.metric("λ utilisé",            f"{lambda_test:.3f}")
    col2.metric("Débit théorique",      f"{d_theorique:.4f}")
    col3.metric("Débit simulé",         f"{d_sim:.4f}")

    erreur = abs(d_sim - d_theorique) / d_theorique * 100
    if erreur < 5:
        st.success(f"✔ Écart relatif = {erreur:.2f} % — simulation cohérente avec la théorie.")
    else:
        st.warning(f"⚠ Écart relatif = {erreur:.2f} % — vérifier les paramètres ou augmenter temps_max.")