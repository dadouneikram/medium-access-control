import random
import numpy as np

class Station:
    def __init__(self, id, K):
        self.id = id
        self.K = K              
        self.file = 0           
        self.etat = 1           
        self.prochaine_tentative = None 
        
        self.paquets_perdus = 0
        self.paquets_reussis = 0

    def ajouter_paquet(self):
        if self.file < self.K:
            self.file += 1
            return True
        else:
            self.paquets_perdus += 1
            return False

    def calculer_backoff(self, t_actuel, tau):
        moyenne = (2**self.etat) * tau
        delai = random.expovariate(1.0 / moyenne)
        self.prochaine_tentative = t_actuel + delai

def simuler(N, K, lambd, tau, temps_max):
    t = 0
    stations = [Station(i, K) for i in range(N)]
    prochaines_arrivees = [random.expovariate(lambd) for _ in range(N)]
    
    total_reussis = 0
    somme_clients_temps = 0  

    while t < temps_max:
        # 0. Calcul du nombre de clients avant de sauter dans le temps
        nb_clients_actuels = sum(s.file for s in stations)
        t_debut_etape = t

        # 1. Identification des stations prêtes
        stations_pretes = [s for s in stations if s.file > 0 and s.prochaine_tentative is not None]
        
        if not stations_pretes:
            # --- CAS : PERSONNE NE VEUT PARLER ---
            t_evenement = min(prochaines_arrivees)
            id_s = prochaines_arrivees.index(t_evenement)
            
            # Mise à jour de la surface (nb_clients * durée du vide)
            somme_clients_temps += nb_clients_actuels * (t_evenement - t_debut_etape)
            
            t = t_evenement
            stations[id_s].ajouter_paquet()
            stations[id_s].prochaine_tentative = t
            prochaines_arrivees[id_s] = t + random.expovariate(lambd)
            continue

        # 2. Identification du premier qui parle
        s_prioritaire = min(stations_pretes, key=lambda s: s.prochaine_tentative)
        t_debut_emission = s_prioritaire.prochaine_tentative
        t_fin = t_debut_emission + 1  
        
        # Mise à jour de la surface jusqu'à la fin de l'émission
        somme_clients_temps += nb_clients_actuels * (t_fin - t_debut_etape)
        
        t = t_fin
        
        # 3. GESTION DES COLLISIONS
        en_conflit = [s for s in stations_pretes if s.prochaine_tentative < t_fin]

        if len(en_conflit) == 1:
            # --- SUCCÈS ---
            s_prioritaire.paquets_reussis += 1
            total_reussis += 1
            s_prioritaire.file -= 1
            s_prioritaire.etat = 1 
            
            if s_prioritaire.file > 0:
                s_prioritaire.prochaine_tentative = t
            else:
                s_prioritaire.prochaine_tentative = None
        else:
            # --- COLLISION ---
            for s in en_conflit:
                s.etat += 1
                s.calculer_backoff(t, tau) 

        # 4. MISE À JOUR DES ARRIVÉES (pendant que le canal était occupé)
        for i in range(N):
            while prochaines_arrivees[i] < t:
                stations[i].ajouter_paquet()
                if stations[i].file == 1 and stations[i].prochaine_tentative is None:
                    stations[i].prochaine_tentative = prochaines_arrivees[i]
                prochaines_arrivees[i] += random.expovariate(lambd)
        
    # --- CALCULS FINAUX ---
    debit = total_reussis / t
    nb_moyen_clients = somme_clients_temps / t
    
    total_perdus = sum(s.paquets_perdus for s in stations)
    total_generes = total_reussis + total_perdus
    taux_perte = total_perdus / total_generes if total_generes > 0 else 0
            
    return debit, nb_moyen_clients, taux_perte