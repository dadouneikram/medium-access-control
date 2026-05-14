import random
import numpy as np
from scipy import stats

ETAT_MAX = 10  # Plafond pour éviter des backoffs astronomiques (2^10 * tau max)


class Station:
    def __init__(self, id, K):
        self.id = id
        self.K = K
        self.file = 0
        self.etat = 1
        self.prochaine_tentative = None

        self.paquets_perdus = 0
        self.paquets_reussis = 0

    def ajouter_paquet(self, t_arrivee):
        if self.file < self.K:
            self.file += 1
            if self.prochaine_tentative is None:
                self.prochaine_tentative = t_arrivee
            return True
        else:
            self.paquets_perdus += 1
            return False

    def calculer_backoff(self, t_actuel, tau):
        etat_effectif = min(self.etat, ETAT_MAX)
        moyenne = (2 ** etat_effectif) * tau
        delai = random.expovariate(1.0 / moyenne)
        self.prochaine_tentative = t_actuel + delai


def simuler(N, K, lambd, tau, temps_max, nb_snapshots=500, csma=False):
    t = 0
    stations = [Station(i, K) for i in range(N)]
    prochaines_arrivees = [random.expovariate(lambd) for _ in range(N)]

    total_reussis = 0
    total_perdus_file = 0
    somme_clients_temps = 0.0
    canal_libre_a = 0.0  # Instant auquel le canal redevient disponible

    historique = []
    intervalle_snapshot = temps_max / nb_snapshots
    prochain_snapshot = intervalle_snapshot

    while t < temps_max:
        nb_clients_actuels = sum(s.file for s in stations)

        stations_pretes = [
            s for s in stations
            if s.file > 0 and s.prochaine_tentative is not None
        ]

        t_prochaine_arrivee = min(prochaines_arrivees)

        if not stations_pretes:
            t_event = t_prochaine_arrivee
            somme_clients_temps += nb_clients_actuels * (t_event - t)

            while prochain_snapshot <= t_event and prochain_snapshot <= temps_max:
                total_gen = total_reussis + total_perdus_file
                historique.append({
                    't': prochain_snapshot,
                    'debit': total_reussis / prochain_snapshot if prochain_snapshot > 0 else 0,
                    'nb_clients': somme_clients_temps / prochain_snapshot if prochain_snapshot > 0 else 0,
                    'taux_perte': total_perdus_file / total_gen if total_gen > 0 else 0
                })
                prochain_snapshot += intervalle_snapshot

            t = t_event
            id_s = prochaines_arrivees.index(t_event)
            stations[id_s].ajouter_paquet(t)
            prochaines_arrivees[id_s] = t + random.expovariate(lambd)
            continue

        s_prioritaire = min(stations_pretes, key=lambda s: s.prochaine_tentative)
        t_voulu = s_prioritaire.prochaine_tentative

        # ── CSMA (Carrier Sense Multiple Access) ─────────────────────────────
        # La station écoute le canal avant d'émettre.
        # Si le canal est occupé au moment t_voulu, elle attend sa libération
        # et émet dès qu'il devient libre (CSMA 1-persistant).
        #
        # CORRECTION BUG 1 : on NE modifie PAS prochaine_tentative ici.
        # On calcule uniquement t_debut_emission. Sans cette correction,
        # prochaine_tentative est sans cesse repoussée et le débit CSMA tend vers 0.
        if csma:
            t_debut_emission = max(t_voulu, canal_libre_a)
        else:
            # ALOHA pur : émission au moment prévu, sans écouter le canal
            t_debut_emission = t_voulu
        # ─────────────────────────────────────────────────────────────────────

        t_fin_emission = t_debut_emission + 1
        canal_libre_a = t_fin_emission  # Canal occupé jusqu'à la fin de cette émission

        somme_clients_temps += nb_clients_actuels * (t_fin_emission - t)

        while prochain_snapshot <= t_fin_emission and prochain_snapshot <= temps_max:
            total_gen = total_reussis + total_perdus_file
            historique.append({
                't': prochain_snapshot,
                'debit': total_reussis / prochain_snapshot if prochain_snapshot > 0 else 0,
                'nb_clients': somme_clients_temps / prochain_snapshot if prochain_snapshot > 0 else 0,
                'taux_perte': total_perdus_file / total_gen if total_gen > 0 else 0
            })
            prochain_snapshot += intervalle_snapshot

        t = t_fin_emission

        # ── Détection des conflits ────────────────────────────────────────────
        # CORRECTION BUG 2 : la fenêtre de collision diffère entre ALOHA et CSMA.
        #
        # CSMA : toute station dont la tentative <= t_debut_emission a entendu
        #        le canal libre au même instant et va émettre simultanément => conflit.
        #        (propagation supposée instantanée : fenêtre de vulnérabilité nulle)
        #
        # ALOHA : conflit si la tentative tombe dans la fenêtre [t_debut, t_fin).
        if csma:
            en_conflit = [
                s for s in stations_pretes
                if s.prochaine_tentative <= t_debut_emission
            ]
        else:
            en_conflit = [
                s for s in stations_pretes
                if s.prochaine_tentative >= t_debut_emission
                and s.prochaine_tentative < t_fin_emission
            ]

        if len(en_conflit) == 1:
            s = en_conflit[0]
            s.paquets_reussis += 1
            total_reussis += 1
            s.file -= 1
            s.etat = 1
            if s.file > 0:
                s.prochaine_tentative = t
            else:
                s.prochaine_tentative = None
        else:
            for s in en_conflit:
                s.etat += 1
                s.calculer_backoff(t, tau)

        for i in range(N):
            while prochaines_arrivees[i] < t:
                perdu = not stations[i].ajouter_paquet(prochaines_arrivees[i])
                if perdu:
                    total_perdus_file += 1
                prochaines_arrivees[i] += random.expovariate(lambd)

    debit_final = total_reussis / t if t > 0 else 0
    nb_moyen_clients = somme_clients_temps / t if t > 0 else 0
    total_gen = total_reussis + total_perdus_file
    taux_perte = total_perdus_file / total_gen if total_gen > 0 else 0

    return historique, debit_final, nb_moyen_clients, taux_perte

#monte-carlo => ON FAIT PLUSIEURS SIMULATIONS POUR AVOIR UNE ESTIMATION PLUS FIABLE DU DÉBIT MOYEN
def simuler_multiple(N, K, lambd, tau, temps_max, nb_runs=15, csma=False):
    debits = []
    for _ in range(nb_runs):
        _, d, _, _ = simuler(N, K, lambd, tau, temps_max, csma=csma)
        debits.append(d)

    moyenne = np.mean(debits)
    if len(debits) > 1:
        #(la Loi de Student) et pas la loi Normale ?=>psq on a un petit échantillon de données (15 runs, c'est $< 30$)
        #et on ne connaît pas l'écart-type réel
        ic = stats.t.interval(
            0.95,
            df=len(debits) - 1,
            loc=moyenne,
            scale=stats.sem(debits) #l'écart-type de l'échantillon divisé par la racine carrée du nombre de runs
        )
        demi_ic = (ic[1] - ic[0]) / 2
    else:
        demi_ic = 0.0

    return moyenne, demi_ic