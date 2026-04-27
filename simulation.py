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
      t += 0.1 
        
    return total_reussis / t