import argparse
import random
import simpy
from simpy.util import start_delayed
from collections import deque

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--elevators", type=int, help="Specify elevators number", default=1)
parser.add_argument("-c", "--capacity", type=int, help="Specify elevator capacity", default=1)
parser.add_argument("-a", "--algorithm", type=str, help="Specify elevator algorithm", default="FCFS")
args = parser.parse_args()

FLOORS = [1,2,3,4,5,6,7]
SPEED = 10
CAPACITY = args.capacity
ELEVATORS = args.elevators

USERS_WAITING = deque([])
USERS_WORKING = deque([])
USERS_LEFT = []

def getListAttr(list):
    result = []
    for item in list:
        result.append(item.id)
    return result

class Individual:
    def __init__(self, env, id):
        self.id = id
        self.is_waiting = True
        self.is_working = False
        self.is_leaving = False
        self.working_time = random.choice(range(50,70))
        self.arrival_time = env.now
        self.waiting_time_up = 0 #Contient le temps d'attente pour monter dans l'ascenceur + temps perdu a attendre que les autres passagers s'arretent a leurs arrêts
        self.waiting_time_down = 0
        self.leaving_time_call = 0
        self.leaving_time = 0
        self.current_floor = 1
        self.expected_floor = random.randint(FLOORS[1], FLOORS[6])
        self.action = env.process(self.run(env))

    def run(self, env):
        while True:
            yield env.timeout(1)
            if(self.is_working == True):
                self.waiting_time_up = self.waiting_time_up + (env.now - self.waiting_time_up)
                print("Individu %d est arrivé à son bureau" % self.id)
                yield env.timeout(self.working_time)
                print("Individu %d a terminé de travailler" % self.id)
                self.is_working = False
                self.is_waiting = True
                self.is_leaving = True
                self.leaving_time_call = env.now
                USERS_WAITING.append(self) #Travail terminé le user se rajoute dans la liste USER_WAITING
                USERS_WORKING.remove(self) #Travail terminé le user se retire de la liste USER_WORKING

                #print("Individu %d is_working : %s ; Waiting elevator : %s "%(self.id, self.is_working, self.is_waiting))
            if self.leaving_time != 0:
                self.leaving_time = env.now
                print("Individu %d quitte le pavillon"%self.id)
                print("Individu %d est arrivé a %d a attendu ascenceur pour monter %d, a attendu ascenceur pour descendre %d, est definitivement sorti du batiment a  %d" %(self.id, self.arrival_time, (self.waiting_time_up - self.arrival_time), (self.waiting_time_down - self.leaving_time_call), self.leaving_time))
                break

class Building:
    def __init__(self, env):
        self.floors = FLOORS
        self.action = env.process(self.run(env))
  
    def run(self, env):
        print("Welcome to le pavillon, we are now open")
        for x in range(ELEVATORS):
            Elevator(env, (x+1))   # Genere X elevator dans le batiment  
        id = 1
        while True:
            yield env.timeout(10) #Attend 120 sec pour generer un nouvel Individual
            if env._now < 100 : 
                a = Individual(env, id)
                USERS_WAITING.append(a)
                print("Individu %d attend au rdc a %d" % (a.id, env.now))
            id += 1
 
class Elevator:
    def __init__(self,env, id):
        self.id = id
        self.speed = SPEED
        self.capacity = CAPACITY
        self.action = env.process(self.run(env))
        self.e_current_floor = 1
        self.users_inside = deque([])
        

    def move(self, env, user):
        eta_out = abs((user.expected_floor - self.e_current_floor)*self.speed) #Temps pour que l'ascenceur depose l'individu au bon etage
        print("time : %d - move : L'ascenceur %d prend en charge l'individu %d" % (env.now, self.id, user.id))
        yield env.timeout(eta_out) #On bloque l'ascenceur tant qu'il n'a pas deposé l'individu   
        self.e_current_floor = user.expected_floor #definir le nouvel etage ou se trouve l'ascenceur       
        print("time : %d - move : L'ascenceur %d depose individu %d a l'etage |%d|  eta_out : %d" %(env.now,self.id, user.id, self.e_current_floor,  eta_out))
        self.users_inside.remove(user) # Le user arrive a son etage on le retire de la liste          
        if user.is_leaving is True :
            user.leaving_time = env.now
            USERS_LEFT.append(user)
        else : 
            user.is_working = True
            user.current_floor = self.e_current_floor
            user.expected_floor = 1
            USERS_WORKING.append(user) # On rajoute le user a la liste working

    
    def fcfs_handle_users(self, env):   
        while len(self.users_inside) != 0 : 
            for user in list(self.users_inside) :
                yield env.process(self.move(env, user))
           
        
    def FCFS(self, env):
        """First Come First Serve with capacity"""
        if(len(USERS_WAITING) != 0):  
            selected_user = USERS_WAITING.popleft() #On defile le premier individu en attente
            self.users_inside.append(selected_user) #On enfile le premier individu dans notre cage d'ascenceur
            eta_in = abs((self.e_current_floor - selected_user.current_floor)*self.speed) #Temps pour que l'ascenceur rejoigne l'individu au bon etage
            print("time : %d - move : L'individu %d appel ascenceur %d pour venir le cherche a |%d| -> |%d| , l'ascenceur est a |%d| " % (env.now, selected_user.id, self.id, selected_user.current_floor, selected_user.expected_floor ,self.e_current_floor))
            yield env.timeout(eta_in) #On bloque l'ascenceur tant qu'il n'a pas atteint l'individu
            if selected_user.is_leaving is True:
                selected_user.waiting_time_down = env.now
            elif selected_user.is_leaving is False:
                selected_user.waiting_time_up = env.now            
            
            self.e_current_floor = selected_user.current_floor            
            for user in list(USERS_WAITING):        
                if user.current_floor == selected_user.current_floor:  
                    if user.is_leaving is True:
                        user.waiting_time_down = env.now
                    elif user.is_leaving is False:
                        user.waiting_time_up = env.now

                    self.users_inside.append(user)
                    USERS_WAITING.remove(user)
            cage = getListAttr(self.users_inside)
            print(cage, " entrent dans l'ascenseur %d" % self.id)
         
            yield env.process(self.fcfs_handle_users(env))  
        
            
# A revoir suite a quelques changements inopinés
    # def SSTF(self, env):
    #     """Shortest Seek Time First"""
    #     tmp = 100
    #     if(len(USERS_WAITING) != 0):
    #         for x in USERS_WAITING:
    #             if USERS_WAITING[x].is_waiting == True:
    #                 if(abs(self.e_current_floor - x.expected_floor) < tmp):
    #                     tmp = abs(self.e_current_floor - x.expected_floor)
    #                     selected = x
    #         yield env.process(self.handle_user(env, selected))
        
    def run(self, env):
        """Elevator behavior"""
        print("Our elevator %d is ready to welcome passengers" % self.id)
        while True :

            yield env.timeout(1)

            if(args.algorithm == "FCFS"):  
                yield env.process(self.FCFS(env))
            elif(args.algorithm == "SSTF"):
                yield env.timeout(1)
                # yield env.process(self.SSTF(env))
                
              
env = simpy.Environment()

pavillon = Building(env)

env.run(until=400)
