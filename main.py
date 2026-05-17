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

st.title("📡 Simulateur MAC : Exponential Backoff")
st.markdown("""
Simulation d'un réseau de $N$ stations partageant un canal unique avec
l'algorithme de **repli exponentiel** (Ethernet / 802.11).
""")

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

# 1 => courbes temporelles

st.header(f"1 : Évolution temporelle [{mode_label}]")

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

# 2. COURBE d en fonction de λ
st.header(f"2 : Débit en fonction de λ  [{mode_label}, N={N} fixé]")

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

# 3. COURBE d en fonction de N
st.header(f"3 : Débit en fonction de N  [{mode_label}, λ={lambd} fixé]")

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

# 4. N OPTIMAL AVEC IC 95%

st.header(f"4 : N optimal avec intervalle de confiance à 95 % [{mode_label}]")
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
        f"**N optimal [{mode_label}] = {n_opt}** : débit moyen = **{d_opt:.4f} ± {ic_opt:.4f}** pqt/ut "
        f"(IC 95%, {nb_runs_ic} réplications)"
    )

    st.dataframe(df_ic.style.format("{:.5f}").highlight_max(
        subset=["Débit moyen"], color="#c6f6d5"
    ), use_container_width=True)

st.divider()

# 5. VALIDATION THÉORIQUE

st.header("5 : Validation théorique")

st.markdown(r"""
Trois cas permettent de comparer les résultats du simulateur à des valeurs
calculables analytiquement. Les formules proviennent de la théorie des files d'attente.

---

### Cas A : File M/D/1 : débit théorique $d = \lambda$

**Conditions :** $N = 1$, $K$ grand, $\lambda < 1$ (une seule station, aucune collision).

Le système se réduit à une **file M/D/1** (arrivées Poisson, service déterministe de durée 1 ut).

$$d_{\text{théo}} = \lambda \qquad \text{(tous les paquets passent, file stable)}$$


---

### Cas B : ALOHA = CSMA pour $N = 1$

**Conditions :** $N = 1$, mode ALOHA vs CSMA.

Sans concurrent, écouter le canal avant d'émettre ne change rien : les deux protocoles
doivent produire **exactement le même débit** (à la variance de simulation près).

$$d_{\text{ALOHA}}(1, K, \lambda, \tau) \approx d_{\text{CSMA}}(1, K, \lambda, \tau)$$

---

### Cas C : Charge légère : $d \approx N\lambda$ quand $\lambda \to 0$

**Conditions :** $N$ quelconque, $\lambda$ très petit tel que $N\lambda \ll 1$.

Quand le trafic est faible, les collisions sont quasi-inexistantes.
Chaque station émet librement à son propre rythme $\lambda$ :

$$d_{\text{théo}} = N \cdot \lambda \qquad \text{si } N\lambda < 1$$
    
*Source : Wikipedia ["M/D/1 queue"](https://en.wikipedia.org/wiki/M/D/1_queue) 


""")

T_VALID = st.number_input(
    "Durée de simulation pour la validation (ut)",
    value=100000, min_value=2000, step=1000
)

if st.button("✅ Lancer les 3 validations théoriques", type="primary"):

    # Cas A : M/D/1, d = λ 
    st.subheader("Cas A : M/D/1 : débit simulé vs $d_{\\text{théo}} = \\lambda$")

    valeurs_lam = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    rows_a = []
    bar_a = st.progress(0, text="Cas A en cours…")
    for idx, lam in enumerate(valeurs_lam):
        _, d_sim, L_sim, _ = simuler(1, 50, lam, tau, T_VALID, csma=False)
        d_theo = lam
        ecart  = abs(d_sim - d_theo) / d_theo * 100
        rows_a.append({
            "λ": lam,
            "d théorique = λ": round(d_theo, 4),
            "d simulé":         round(d_sim,  4),
            "Écart (%)":        round(ecart,  2),
            "Statut":           "✓ OK" if ecart < 5 else "⚠ Écart"
        })
        bar_a.progress((idx + 1) / len(valeurs_lam), text=f"λ={lam} → d_sim={d_sim:.4f}")
    bar_a.empty()

    df_a = pd.DataFrame(rows_a).set_index("λ")
    st.dataframe(
        df_a.style
            .map(lambda v: "color: green; font-weight: bold" if v == "✓ OK"
                      else ("color: orange; font-weight: bold" if v == "⚠ Écart" else ""),
                      subset=["Statut"])
            .format({"d théorique = λ": "{:.4f}", "d simulé": "{:.4f}", "Écart (%)": "{:.2f}"}),
        use_container_width=True
    )
    max_ecart_a = max(r["Écart (%)"] for r in rows_a)
    if max_ecart_a < 5:
        st.success(f"✔ Écart maximal = {max_ecart_a:.2f} % < 5 % : simulation cohérente avec la théorie M/D/1.")
    else:
        st.warning(f"⚠ Écart maximal = {max_ecart_a:.2f} % : augmenter la durée de simulation.")

    

    st.divider()

    # Cas B : ALOHA = CSMA pour N=1 
    st.subheader("Cas B : ALOHA = CSMA pour $N = 1$")

    valeurs_lam_b = [0.1, 0.3, 0.5, 0.8]
    rows_b = []
    bar_b = st.progress(0, text="Cas B en cours…")
    for idx, lam in enumerate(valeurs_lam_b):
        _, da, _, _ = simuler(1, 50, lam, tau, T_VALID, csma=False)
        _, dc, _, _ = simuler(1, 50, lam, tau, T_VALID, csma=True)
        diff = abs(da - dc)
        rows_b.append({
            "λ": lam,
            "d ALOHA":  round(da,   4),
            "d CSMA":   round(dc,   4),
            "|diff|":   round(diff, 4),
            "Statut":   "✓ OK" if diff < 0.02 else "⚠ Diff"
        })
        bar_b.progress((idx + 1) / len(valeurs_lam_b),
                       text=f"λ={lam} → ALOHA={da:.4f}, CSMA={dc:.4f}")
    bar_b.empty()

    df_b = pd.DataFrame(rows_b).set_index("λ")
    st.dataframe(
        df_b.style
            .map(lambda v: "color: green; font-weight: bold" if v == "✓ OK"
                      else ("color: orange; font-weight: bold" if v == "⚠ Diff" else ""),
                      subset=["Statut"])
            .format({"d ALOHA": "{:.4f}", "d CSMA": "{:.4f}", "|diff|": "{:.4f}"}),
        use_container_width=True
    )
    max_diff_b = max(r["|diff|"] for r in rows_b)
    if max_diff_b < 0.02:
        st.success(f"✔ Différence maximale = {max_diff_b:.4f} ≈ 0 : pas de biais systématique entre ALOHA et CSMA pour N=1.")
    else:
        st.warning(f"⚠ Différence = {max_diff_b:.4f} : vérifier l'implémentation CSMA.")


    st.divider()

    # Cas C : charge légère, d ≈ N·λ
    st.subheader("Cas C : Charge légère : $d \\approx N \\cdot \\lambda$")

    configs_c = [(2, 0.05), (5, 0.02), (10, 0.01), (20, 0.005), (3, 0.10)]
    rows_c = []
    bar_c = st.progress(0, text="Cas C en cours…")
    for idx, (n, lam) in enumerate(configs_c):
        _, d_sim, _, _ = simuler(n, 20, lam, tau, T_VALID, csma=csma_mode)
        d_theo = n * lam
        ecart  = abs(d_sim - d_theo) / d_theo * 100
        rows_c.append({
            "N": n,
            "λ": lam,
            "N·λ (théo)": round(d_theo, 4),
            "d simulé":   round(d_sim,  4),
            "Écart (%)":  round(ecart,  2),
            "Statut":     "✓ OK" if ecart < 8 else "⚠ Écart"
        })
        bar_c.progress((idx + 1) / len(configs_c),
                       text=f"N={n}, λ={lam} → d_sim={d_sim:.4f}, théo={d_theo:.4f}")
    bar_c.empty()

    df_c = pd.DataFrame(rows_c).set_index("N")
    st.dataframe(
        df_c.style
            .map(lambda v: "color: green; font-weight: bold" if v == "✓ OK"
                      else ("color: orange; font-weight: bold" if v == "⚠ Écart" else ""),
                      subset=["Statut"])
            .format({"λ": "{:.3f}", "N·λ (théo)": "{:.4f}",
                     "d simulé": "{:.4f}", "Écart (%)": "{:.2f}"}),
        use_container_width=True
    )
    max_ecart_c = max(r["Écart (%)"] for r in rows_c)
    if max_ecart_c < 8:
        st.success(f"✔ Écart maximal = {max_ecart_c:.2f} % : débit converge bien vers N·λ en charge légère.")
    else:
        st.warning(f"⚠ Écart maximal = {max_ecart_c:.2f} % : augmenter la durée de simulation.")


    st.divider()

    st.subheader("📋 Récapitulatif de la validation")

    ok_a = max(r["Écart (%)"] for r in rows_a) < 5
    ok_b = max(r["|diff|"]   for r in rows_b) < 0.02
    ok_c = max(r["Écart (%)"] for r in rows_c) < 8

    col1, col2, col3 = st.columns(3)
    col1.metric("Cas A : M/D/1 (d=λ)",
                f"Écart max {max(r['Écart (%)'] for r in rows_a):.2f}%",
                delta="✓ Validé" if ok_a else "⚠ À revoir")
    col2.metric("Cas B : ALOHA=CSMA (N=1)",
                f"Diff max {max(r['|diff|'] for r in rows_b):.4f}",
                delta="✓ Validé" if ok_b else "⚠ À revoir")
    col3.metric("Cas C : Charge légère (d≈Nλ)",
                f"Écart max {max(r['Écart (%)'] for r in rows_c):.2f}%",
                delta="✓ Validé" if ok_c else "⚠ À revoir")

    if ok_a and ok_b and ok_c:
        st.success(
            "✅ Les trois validations théoriques sont concluantes. "
            "Le simulateur est cohérent avec la théorie des files d'attente "
            "sur tous les cas testables analytiquement."
        )
    else:
        st.warning("Certaines validations présentent des écarts. Augmenter la durée de simulation.")

    st.markdown("""
    **Sources utilisées pour la validation :**
    - Wikipedia, *M/D/1 queue* : https://en.wikipedia.org/wiki/M/D/1_queue
    """)