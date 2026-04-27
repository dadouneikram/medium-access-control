import random
import numpy as np

class Station:
    def init(self, id, K):
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
     
        stations_pretes = [s for s in stations if s.file > 0 and s.prochaine_tentative is not None]
        
        if not stations_pretes:
            
            t = min(prochaines_arrivees)
           
            continue

        
        s_prioritaire = min(stations_pretes, key=lambda s: s.prochaine_tentative)
        t_debut = s_prioritaire.prochaine_tentative
        t_fin = t_debut + 1  
        
        
        en_conflit = [s for s in stations_pretes if s.prochaine_tentative < t_fin]

        if len(en_conflit) == 1:
          
            t = t_fin 
            s_prioritaire.paquets_reussis += 1
            total_reussis += 1
            s_prioritaire.file -= 1
            s_prioritaire.etat = 1
            
            
            if s_prioritaire.file > 0:
                s_prioritaire.prochaine_tentative = t
            else:
                s_prioritaire.prochaine_tentative = None

        else:
            
            t = t_fin 
            for s in en_conflit:
                s.etat += 1 
                s.calculer_backoff(t, tau) 
        
    return total_reussis / t