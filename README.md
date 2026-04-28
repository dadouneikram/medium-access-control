# Projet de Simulation MAC - Exponential Backoff
**M1 AMIS - 2025-2026**

Ce projet consiste à simuler un protocole de contrôle d'accès au support (MAC) basé sur l'algorithme d'évitement de collision **Exponential Backoff**.

## Binôme
- **Dadoune** (Ikram)
- **Debbihi** (Fatiha)

# Description du projet

Ce projet implémente un simulateur événementiel discret du protocole MAC avec l'algorithme **Exponential Backoff**, utilisé notamment dans Ethernet (CSMA/CD) et Wi-Fi (802.11).

Le simulateur modélise **N stations** partageant un canal unique, avec files d'attente bornées, collisions et repli exponentiel aléatoire.

## Algorithme simulé

- Chaque station dispose d'une file bornée de capacité **K**
- Les inter-arrivées de paquets suivent une loi exponentielle de paramètre **λ**
- En cas de collision, la station en état *i* attend un temps aléatoire `Exp(1 / 2^i × τ)` avant de ré-émettre
- L'état est remis à **1** après toute émission réussie

## Structure du projet>
- `simulation.py` : Contient la logique du simulateur (classe Station et moteur de calcul).
- `main.py` : Interface utilisateur réalisée avec **Streamlit**.
- `requirements.txt` : Liste des bibliothèques nécessaires.

## Installation
Pour installer les dépendances nécessaires, exécutez la commande suivante :
```bash
pip install -r requirements.txt
```


## Lancement

Pour lancer l'interface interactive :

```bash
streamlit run main.py
```
