import argparse
import csv
import time
import random
import simpy
from simpy.util import start_delayed
from collections import deque


parser = argparse.ArgumentParser()
parser.add_argument("-e", "--elevators", type=int, help="Specify elevators number", default=1)
parser.add_argument("-c", "--capacity", type=int, help="Specify elevator capacity", default=1)
parser.add_argument("-a", "--algorithm", type=str, help="Specify elevator algorithm", default="FCFS")
parser.add_argument("-i", "--idle", type=bool, help="Specify if the elevator go idle or not", default=False)
args = parser.parse_args()

FLOORS = [1,2,3,4,5,6,7]
SPEED = 10
CAPACITY = args.capacity
ELEVATORS = args.elevators

WAITING = deque([])
WORKING = deque([])
LEFT = []

def getListAttr(list):
    result = []
    for item in list:
        result.append(item.id)
    return result

def getAllResult():
    #(user.waiting_time_up ), (user.waiting_time_down - user.leaving_time_call), user.leaving_time)
    for user in LEFT:
        print("Individu ", user.id ," inside building at :", user.arrival_time ," wait_up", (user.waiting_time_up - user.arrival_time)," wait down :", (user.waiting_time_down - user.leaving_time_call) ," exited building at :",  user.leaving_time)


class Building:
    def __init__(self, env):
        self.floors = FLOORS
        self.action = env.process(self.run(env))
  
    def run(self, env):
        print(env.now, " : Le pavillon is open")
        for x in range(ELEVATORS):
            Elevator(env, (x+1))   # Genere X elevator dans le batiment  
        id = 1
        while True:
            yield env.timeout(10) #Attend 120 sec pour generer un nouvel Individual
            if env._now < 1000 : #Empeche de nouveau individus de monter pour pouvoir fermer le batiment
                new_user = Individual(env, id)
                WAITING.append(new_user)
                print(env.now, " : Individual ", new_user.id, " waiting in RDC")
            id += 1


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
        self.current = 1
        self.expected = random.randint(FLOORS[1], FLOORS[6])
        self.action = env.process(self.run(env))

    def run(self, env):
        while True:
            yield env.timeout(1)
            if(self.is_working == True):
                print(env.now, " : Individual ", self.id, " arrived to his office and start to work")
                yield env.timeout(self.working_time)
                print(env.now, " : Individual ", self.id, " finished his works")
                self.is_working = False
                self.is_waiting = True
                self.is_leaving = True
                self.leaving_time_call = env.now
                WAITING.append(self) #Travail terminé le user se rajoute dans la liste USER_WAITING
                WORKING.remove(self) #Travail terminé le user se retire de la liste USER_WORKING
            if self.leaving_time != 0:
                self.leaving_time = env.now
                print(env.now, " : Individual ", self.id, " leaves")
                break
 
class Elevator:
    def __init__(self,env, id):
        self.id = id
        self.speed = SPEED
        self.capacity = CAPACITY
        self.action = env.process(self.run(env))
        self.e_current = 1
        self.shaft = deque([])
        
    def move(self, env, user):
        eta_out = abs((user.expected - self.e_current)*self.speed) #Temps pour que l'ascenceur depose l'individu au bon etage
        yield env.timeout(eta_out) #On bloque l'ascenceur tant qu'il n'a pas deposé l'individu   
        self.e_current = user.expected #definir le nouvel etage ou se trouve l'ascenceur       
        print(env.now, " : Elevator ", self.id, " drops Individual ", user.id, " at floor |", self.e_current, "| it takes ", eta_out)
        self.shaft.remove(user) # Le user arrive a son etage on le retire de la liste          
        if user.is_leaving is True :
            user.leaving_time = env.now
            LEFT.append(user)
        else : 
            user.is_working = True
            user.current = self.e_current
            user.expected = 1
            WORKING.append(user) # On rajoute le user a la liste working
    
    def fcfs_handle_users(self, env):   
        while len(self.shaft) != 0 : 
            for user in list(self.shaft) :
                if user.is_leaving is False: #Si individu monte travailler on enregistre le temps d'attente pour pouvoir monter
                    user.waiting_time_up = env.now              
                yield env.process(self.move(env, user))
        
    def FCFS(self, env):
        """First Come First Serve with capacity"""
        if(len(WAITING) != 0):  
            selected_user = WAITING.popleft() #On defile le premier individu en attente
            self.shaft.append(selected_user) #On enfile le premier individu dans notre cage d'ascenceur
            eta_in = abs((self.e_current - selected_user.current)*self.speed) #Temps pour que l'ascenceur rejoigne l'individu au bon etage
            print(env.now, " : Indiviual ", selected_user.id, " call Elevator ", self.id, " from |", selected_user.current, "| to reach |", selected_user.expected, "|")
            yield env.timeout(eta_in) #On bloque l'ascenceur tant qu'il n'a pas atteint l'individu
            self.e_current = selected_user.current            
            print(env.now, " : Elevator ", self.id, " picks Individual ", selected_user.id, "at |",self.e_current,"| it takes ", eta_in)
            if selected_user.is_leaving is True:
                selected_user.waiting_time_down = env.now
            elif selected_user.is_leaving is False:
                selected_user.waiting_time_up = env.now            
            for user in list(WAITING):        
                if user.current == selected_user.current:  
                    if user.is_leaving is True:
                        user.waiting_time_down = env.now
                    elif user.is_leaving is False:
                        user.waiting_time_up = env.now
                    self.shaft.append(user)
                    WAITING.remove(user)
            cage = getListAttr(self.shaft)
            print(env.now, " : Elevator ", self.id, " carrying ", cage)
            yield env.process(self.fcfs_handle_users(env))  
        
            
# A revoir suite a quelques changements inopinés
    # def SSTF(self, env):
    #     """Shortest Seek Time First"""
    #     tmp = 100
    #     if(len(WAITING) != 0):
    #         for x in WAITING:
    #             if WAITING[x].is_waiting == True:
    #                 if(abs(self.e_current - x.expected) < tmp):
    #                     tmp = abs(self.e_current - x.expected)
    #                     selected = x
    #         yield env.process(self.handle_user(env, selected))
        
    def run(self, env):
        print(env.now ," : Elevator ",self.id," is running")
        while True :
            yield env.timeout(1)
            if(args.algorithm == "FCFS"):  
                yield env.process(self.FCFS(env))
            elif(args.algorithm == "SSTF"):
                yield env.timeout(1)
                # yield env.process(self.SSTF(env))
                
              
env = simpy.Environment()
pavillon = Building(env)
env.run(until=2000)

getAllResult() # To Remove


def results_to_csv():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    with open(current_time+"_"+str(args.elevators)+"elevators_"+str(args.capacity)+"capacity_idle="+str(args.idle)+"_"+args.algorithm+".csv", 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["USER","WAITING_TIME_UP", "WAITING_TIME_DOWN", "LEAVING_TIME_CALL", "LEAVING_TIME"])
        for user in LEFT:
            writer.writerow([user.id, (user.waiting_time_up - user.arrival_time), (user.waiting_time_down - user.leaving_time_call), user.leaving_time_call, user.leaving_time])
            
results_to_csv()
