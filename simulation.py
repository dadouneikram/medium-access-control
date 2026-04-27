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
        
        # Loi exponentielle de paramètre 1 / (2^i * tau)
        delai = random.expovariate(1 / (pow(2, self.etat) * tau))
        self.prochaine_tentative = t_actuel + delai