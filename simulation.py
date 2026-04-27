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
    historique_debit = []

    while t < temps_max:
        # 1. On identifie les stations qui ont des paquets à envoyer
        stations_pretes = [s for s in stations if s.file > 0 and s.prochaine_tentative is not None]
        
        if not stations_pretes:
            # Si personne n'est prêt, on saute au prochain paquet qui arrive
            t = min(prochaines_arrivees)
            # ... (logique pour ajouter le paquet à la station correspondante)
            continue

        # 2. On trouve la station qui veut parler en premier
        s_prioritaire = min(stations_pretes, key=lambda s: s.prochaine_tentative)
        t_debut = s_prioritaire.prochaine_tentative
        t_fin = t_debut + 1  # L'émission dure 1 unité
        
        # 3. ON CHERCHE LES COLLISIONS
        # Existe-t-il d'autres stations qui tentent de parler avant que t_fin ne soit atteint ?
        en_conflit = [s for s in stations_pretes if s.prochaine_tentative < t_fin]

        if len(en_conflit) == 1:
            # --- SUCCÈS ---
            t = t_fin # On avance le temps à la fin de l'émission
            s_prioritaire.paquets_reussis += 1
            total_reussis += 1
            s_prioritaire.file -= 1
            s_prioritaire.etat = 1 # Retour à l'état initial
            
            # Si la station a encore des paquets, elle tentera de renvoyer direct après
            if s_prioritaire.file > 0:
                s_prioritaire.prochaine_tentative = t
            else:
                s_prioritaire.prochaine_tentative = None

        else:
            # --- COLLISION ---
            t = t_fin # Le canal est occupé par le bruit de la collision
            for s in en_conflit:
                s.etat += 1 # On augmente l'état de backoff
                s.calculer_backoff(t, tau) # On reprogramme un essai plus tard
        
    return total_reussis / t