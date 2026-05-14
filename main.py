import streamlit as st
import pandas as pd
import numpy as np
from simulation import simuler, simuler_multiple

st.set_page_config(page_title="Simulateur MAC - Exponential Backoff", layout="wide")

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
N         = st.sidebar.slider("Nombre de stations (N)", 1, 100, 10)
K         = st.sidebar.slider("Capacité des files (K)", 1, 50, 10)
lambd     = st.sidebar.slider("Taux d'arrivée λ", 0.01, 2.0, 0.3, step=0.01)
tau       = st.sidebar.number_input("Paramètre τ (backoff moyen de base)", value=1.0, min_value=0.01)
temps_max = st.sidebar.number_input("Durée de simulation (ut)", value=2000, min_value=100)

st.sidebar.markdown("---")
st.sidebar.markdown("**Hypothèse d'accès au canal**")
csma_mode = st.sidebar.toggle(
    "Activer CSMA (écoute avant émission)",
    value=False,
    help="CSMA : la station vérifie si le canal est libre avant d'émettre. "
         "Si désactivé : ALOHA pur (émission sans vérification)."
)
mode_label = "CSMA" if csma_mode else "ALOHA"
st.sidebar.info(f"Mode actif : **{mode_label}**")

st.sidebar.markdown("---")
st.sidebar.markdown("**Études paramétriques**")
nb_pts_lambda = st.sidebar.slider("Points pour courbe en λ", 5, 30, 15)
n_max_etude   = st.sidebar.slider("N max pour courbe en N", 5, 80, 40)
nb_runs_ic    = st.sidebar.slider("Réplications pour IC 95%", 5, 30, 10)

# ══════════════════════════════════════════════════════════════════════════════
# 1. SIMULATION UNIQUE — courbes temporelles
# ══════════════════════════════════════════════════════════════════════════════
st.header(f"1 — Évolution temporelle [{mode_label}]")

if st.button("▶ Lancer la simulation", type="primary"):
    with st.spinner("Simulation en cours…"):
        historique, d_final, clients_final, perte_finale = simuler(
            N, K, lambd, tau, temps_max, csma=csma_mode
        )

    df_hist = pd.DataFrame(historique).set_index("t")

    col1, col2, col3 = st.columns(3)
    col1.metric("Débit final  d(N,K,λ,τ)", f"{d_final:.4f} pqt/ut")
    col2.metric("Nb moyen clients  L",      f"{clients_final:.3f}")
    col3.metric("Taux de perte",            f"{perte_finale*100:.2f} %")

    st.subheader("Débit n(t)/t en fonction du temps")
    st.markdown("Cette courbe doit converger vers $d(N,K,\\lambda,\\tau)$ quand $t \\to \\infty$.")
    st.line_chart(df_hist["debit"], use_container_width=True)

    st.subheader("Nombre moyen de clients en fonction du temps")
    st.line_chart(df_hist["nb_clients"], use_container_width=True)

    st.subheader("Taux de perte en fonction du temps")
    st.line_chart(df_hist["taux_perte"], use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 2. COURBE d en fonction de λ
# ══════════════════════════════════════════════════════════════════════════════
st.header(f"2 — Débit en fonction de λ  [{mode_label}, N={N} fixé]")

if st.button("📈 Tracer d en fonction de λ"):
    valeurs_lambda = np.linspace(0.05, 2.0, nb_pts_lambda)
    list_debit, list_clients, list_perte = [], [], []

    bar = st.progress(0, text="Calcul…")
    for idx, l in enumerate(valeurs_lambda):
        _, d, c, p = simuler(N, K, l, tau, temps_max, csma=csma_mode)
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
# 3. COURBE d en fonction de N
# ══════════════════════════════════════════════════════════════════════════════
st.header(f"3 — Débit en fonction de N  [{mode_label}, λ={lambd} fixé]")

compare_csma = st.checkbox("Afficher aussi la courbe de l'autre mode pour comparaison", value=True)

if st.button("📈 Tracer d en fonction de N"):
    valeurs_N = list(range(1, n_max_etude + 1))
    list_debit, list_perte = [], []
    list_debit_comp, list_perte_comp = [], []

    bar = st.progress(0, text="Calcul…")
    for idx, n in enumerate(valeurs_N):
        _, d, _, p = simuler(n, K, lambd, tau, temps_max, csma=csma_mode)
        list_debit.append(d)
        list_perte.append(p)
        if compare_csma:
            _, d2, _, p2 = simuler(n, K, lambd, tau, temps_max, csma=not csma_mode)
            list_debit_comp.append(d2)
            list_perte_comp.append(p2)
        bar.progress((idx + 1) / len(valeurs_N),
                     text=f"N = {n}  →  débit = {d:.4f}")
    bar.empty()

    mode_comp = "CSMA" if not csma_mode else "ALOHA"
    df_N = pd.DataFrame(
        {f"Débit [{mode_label}]": list_debit,
         f"Taux de perte [{mode_label}]": list_perte},
        index=pd.Index(valeurs_N, name="N")
    )
    if compare_csma:
        df_N[f"Débit [{mode_comp}]"] = list_debit_comp
        df_N[f"Taux de perte [{mode_comp}]"] = list_perte_comp

    st.subheader("Débit d(N,K,λ,τ) vs N")
    cols_debit = [c for c in df_N.columns if "Débit" in c]
    st.line_chart(df_N[cols_debit], use_container_width=True)

    st.subheader("Taux de perte vs N")
    cols_perte = [c for c in df_N.columns if "perte" in c]
    st.line_chart(df_N[cols_perte], use_container_width=True)

    n_optimal_simple = valeurs_N[int(np.argmax(list_debit))]
    st.success(
        f"N estimé maximisant le débit [{mode_label}] (sans IC) : **N = {n_optimal_simple}** "
        f"avec débit = {max(list_debit):.4f} pqt/ut"
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 4. N OPTIMAL AVEC IC 95%
# ══════════════════════════════════════════════════════════════════════════════
st.header(f"4 — N optimal avec intervalle de confiance à 95 % [{mode_label}]")
st.markdown(f"""
Pour chaque valeur de N, on lance **{nb_runs_ic} réplications** indépendantes
et on calcule la moyenne du débit ainsi que son intervalle de confiance Student à 95 %.
""")

if st.button(f"🔬 Calculer N optimal (IC 95%, {nb_runs_ic} runs par N)"):
    valeurs_N = list(range(1, n_max_etude + 1))
    moyennes, demi_ics = [], []

    bar = st.progress(0, text="Réplications en cours…")
    for idx, n in enumerate(valeurs_N):
        m, ic = simuler_multiple(n, K, lambd, tau, temps_max,
                                 nb_runs=nb_runs_ic, csma=csma_mode)
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
        "Débit moyen":   moyennes,
        "Borne inf 95%": borne_inf,
        "Borne sup 95%": borne_sup,
        "Demi-IC":       demi_ics,
    }, index=pd.Index(valeurs_N, name="N"))

    st.subheader("Débit moyen ± IC 95% en fonction de N")
    st.line_chart(
        df_ic[["Débit moyen", "Borne inf 95%", "Borne sup 95%"]],
        use_container_width=True
    )

    idx_opt = int(np.argmax(moyennes))
    n_opt   = valeurs_N[idx_opt]
    d_opt   = moyennes[idx_opt]
    ic_opt  = demi_ics[idx_opt]

    st.success(
        f"**N optimal [{mode_label}] = {n_opt}** — débit moyen = **{d_opt:.4f} ± {ic_opt:.4f}** pqt/ut "
        f"(IC 95%, {nb_runs_ic} réplications)"
    )

    st.dataframe(df_ic.style.format("{:.5f}").highlight_max(
        subset=["Débit moyen"], color="#c6f6d5"
    ), use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 5. VALIDATION THÉORIQUE
# ══════════════════════════════════════════════════════════════════════════════
st.header("5 — Validation théorique")
st.markdown("""
**Cas N = 1, K grand, λ < 1 :** une seule station, jamais de collision.
Le débit théorique est $d = \\lambda$ (tous les paquets passent, régime stable).
Ce cas est identique en ALOHA et en CSMA (pas de concurrent).
""")

if st.button("✅ Vérifier le cas N=1 (validation)"):
    lambda_test = lambd
    d_theorique = min(lambda_test, 1.0)

    with st.spinner("Simulation N=1…"):
        _, d_sim, _, _ = simuler(1, 50, lambda_test, tau, max(temps_max, 5000), csma=csma_mode)

    col1, col2, col3 = st.columns(3)
    col1.metric("λ utilisé",       f"{lambda_test:.3f}")
    col2.metric("Débit théorique", f"{d_theorique:.4f}")
    col3.metric("Débit simulé",    f"{d_sim:.4f}")

    erreur = abs(d_sim - d_theorique) / d_theorique * 100
    if erreur < 5:
        st.success(f"✔ Écart relatif = {erreur:.2f} % — simulation cohérente avec la théorie.")
    else:
        st.warning(f"⚠ Écart relatif = {erreur:.2f} % — augmenter temps_max pour plus de précision.")