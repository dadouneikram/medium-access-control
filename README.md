# Simulateur MAC (Exponential Backoff)

**Projet de Simulation: Medium Access Control**  
**Auteurs :** Dadoune Ikram & Debbihi Fatiha  
**Année universitaire :** 2025–2026

---

## Description

Ce simulateur modélise un réseau de **N stations** partageant un canal unique selon le protocole
**Exponential Backoff** (utilisé dans Ethernet / IEEE 802.11). Il permet d'étudier :

- l'évolution temporelle du débit, du nombre moyen de clients et du taux de perte ;
- la sensibilité du débit aux paramètres λ et N ;
- la détermination du N optimal avec intervalle de confiance à 95 % ;
- la comparaison entre deux modes d'accès : **ALOHA pur** et **CSMA 1-persistant** ;
- la validation par rapport à des résultats théoriques issus de la théorie des files d'attente.

---

## Structure du projet

```
DADOUNE_DEBBIHI/
├── simulation.py      # Moteur de simulation (événements discrets) + Monte-Carlo
├── main.py            # Interface utilisateur Streamlit (5 sections)
├── requirements.txt   # Dépendances Python
├── README.md          # Ce fichier
└── rapport.pdf        # Rapport complet du projet
```

### `simulation.py`  (Moteur de simulation)

Contient deux fonctions principales :

| Fonction | Rôle |
|---|---|
| `simuler(N, K, λ, τ, T, csma)` | Simulation événementielle unique, retourne l'historique temporel et les métriques finales |
| `simuler_multiple(N, K, λ, τ, T, nb_runs, csma)` | Monte-Carlo : moyenne et demi-IC Student à 95 % sur `nb_runs` réplications |

**Classe `Station`** : représente une station avec sa file d'attente (capacité K), son état de backoff, et ses compteurs de paquets réussis/perdus.

### `main.py` (Interface Streamlit)

L'application est organisée en **5 sections** :

| Section | Contenu |
|---|---|
| 1 | Évolution temporelle (débit, nb clients, taux de perte) |
| 2 | Courbe d(N, K, λ, τ) en fonction de λ |
| 3 | Courbe d(N, K, λ, τ) en fonction de N (avec comparaison ALOHA/CSMA) |
| 4 | N optimal avec IC 95 % (méthode Monte-Carlo + loi de Student) |
| 5 | Validation théorique sur 3 cas analytiques |

---

## Installation

### Prérequis

- Python ≥ 3.9
- pip

### Installer les dépendances

```bash
pip install -r requirements.txt
```

Contenu de `requirements.txt` :
```
streamlit
pandas
numpy
matplotlib
scipy
jinja2
```

### Lancer l'application

```bash
streamlit run main.py
```

L'interface s'ouvre automatiquement dans le navigateur à l'adresse `http://localhost:8501`.

---

## Paramètres de la simulation

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| **N** | Nombre de stations | 10 |
| **K** | Capacité de la file d'attente par station | 10 |
| **λ** | Taux d'arrivée des paquets (par station) | 0.3 |
| **τ** | Paramètre de backoff de base (moyenne du 1er délai) | 1.0 |
| **T** | Durée de la simulation (unités de temps) | 2000 |
| **Mode** | ALOHA pur ou CSMA 1-persistant | ALOHA |

Tous les paramètres sont ajustables via la **barre latérale** de l'interface Streamlit.

---

## Modèle de simulation

### Événements traités

1. **Arrivée d'un paquet** sur une station (loi exponentielle de paramètre λ)
2. **Tentative d'émission** d'un paquet (instant `prochaine_tentative`)
3. **Succès** : un seul émetteur → débit incrémenté, état remis à 1
4. **Collision** : plusieurs émetteurs simultanés → backoff exponentiel, état i → i+1

### Algorithme de backoff

Quand une station en état `i` subit une collision, elle tire un délai aléatoire :

```
délai ~ Exp(1 / (2^i × τ))
```

L'état est plafonné à `ETAT_MAX = 10` pour éviter des délais astronomiques.

### Différence ALOHA / CSMA

- **ALOHA** : émission sans écoute du canal : collision si deux tentatives se recouvrent dans la fenêtre `[t_début, t_fin)`.
- **CSMA 1-persistant** : la station attend que le canal soit libre avant d'émettre (`t_début = max(t_voulu, canal_libre_à)`) : collision si plusieurs stations ont entendu le canal libre au même instant.

---

## Validation théorique

Trois cas permettent de confronter le simulateur à la théorie :

| Cas | Conditions | Attendu théorique |
|---|---|---|
| **A** — M/D/1 | N=1, K grand, λ < 1 | d = λ (Pollaczek-Khinchine) |
| **B** — ALOHA = CSMA | N=1 | d_ALOHA ≈ d_CSMA |
| **C** — Charge légère | Nλ ≪ 1 | d ≈ N·λ |

---

## Méthode statistique

Pour l'estimation du N optimal (section 4), on utilise la **méthode de Monte-Carlo** avec **intervalle de confiance Student à 95 %** :

- La loi de Student est préférée à la loi Normale car l'échantillon est petit (< 30 runs).
- Le demi-IC est calculé via `scipy.stats.t.interval` avec l'erreur standard `scipy.stats.sem`.

---

## Références

- Wikipedia, *M/D/1 queue* : https://en.wikipedia.org/wiki/M/D/1_queue  
- Wikipedia, *Pollaczek–Khinchine formula* : https://en.wikipedia.org/wiki/Pollaczek%E2%80%93Khinchine_formula  
- Wikipedia, *M/G/1 queue* : https://en.wikipedia.org/wiki/M/G/1_queue  
- Sztrik J., *Basic Queueing Theory*, Université de Debrecen, 2021