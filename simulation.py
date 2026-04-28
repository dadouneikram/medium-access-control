import random
import numpy as np
from scipy import stats

ETAT_MAX = 10 

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
        moyenne = (2**etat_effectif) * tau
        delai = random.expovariate(1.0 / moyenne)
        self.prochaine_tentative = t_actuel + delai

def simuler(N, K, lambd, tau, temps_max, nb_snapshots=500):
    t = 0
    stations = [Station(i, K) for i in range(N)]
    prochaines_arrivees = [random.expovariate(lambd) for _ in range(N)]
    
    total_reussis = 0
    total_perdus_file = 0
    somme_clients_temps = 0.0

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
        t_debut_emission = s_prioritaire.prochaine_tentative
        t_fin_emission = t_debut_emission + 1  
 
        
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
 
        
        en_conflit = [
            s for s in stations_pretes
            if s.prochaine_tentative >= t_debut_emission
            and s.prochaine_tentative < t_fin_emission
        ]
 
        if len(en_conflit) == 1:
            # Succès
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
            # Collision : tous les conflictuels font un backoff
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
 
 
def simuler_multiple(N, K, lambd, tau, temps_max, nb_runs=15):
    """
    Lance nb_runs réplications et retourne moyenne + IC 95% du débit.
    Utilisé pour trouver le N optimal avec niveau de confiance.
    """
    debits = []
    for _ in range(nb_runs):
        _, d, _, _ = simuler(N, K, lambd, tau, temps_max)
        debits.append(d)
 
    moyenne = np.mean(debits)
    if len(debits) > 1:
        ic = stats.t.interval(
            0.95,
            df=len(debits) - 1,
            loc=moyenne,
            scale=stats.sem(debits)
        )
        demi_ic = (ic[1] - ic[0]) / 2
    else:
        demi_ic = 0.0
 
    return moyenne, demi_ic