import argparse
import csv
import operator
import time
import random
import simpy
from simpy.util import start_delayed
from collections import deque
import numpy.random as rnd

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--elevators", type=int, help="Specify elevators number", default=1)
parser.add_argument("-c", "--capacity", type=int, help="Specify elevator capacity", default=1)
parser.add_argument("-s", "--speed", type=int, help="Specify elevator speed", default=10)
parser.add_argument("-a", "--algorithm", type=str, help="Specify elevator algorithm", default="FCFS")
parser.add_argument("-i", "--idle", type=bool, help="Specify if the elevator go idle or not", default=False)
parser.add_argument("-l", "--lambd", type=float, help="Specify the lambda value", default=0.5)
parser.add_argument("-d", "--duration", type=int, help="Specify the duration for the simulation", default=10000)

args = parser.parse_args()

FLOORS = [1,2,3,4,5,6,7]
SPEED = args.speed
CAPACITY = args.capacity
ELEVATORS = args.elevators
LAMBDA = args.lambd
SIMU_DURATION = args.duration

WAITING = deque([])
WORKING = deque([])
LEFT = []

def print_by_id(list):
    result = []
    for item in list:
        result.append(item.id)
    return result

def print_by_expected(list):
    result = []
    for item in list:
        result.append(item.expected)
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
        cpt = 0 #Monitor how many user will be created by the simulation
        print(env.now, " : Le pavillon is open")
        for x in range(ELEVATORS):
            Elevator(env, (x+1))   # Genere X elevator dans le batiment  
        id = 1
        while True:
            yield env.timeout(int(rnd.poisson(lam=60/LAMBDA, size =1)))  # Processus d'arrivée de Poisson       
            if env.now < int(SIMU_DURATION / (1.05)) : #Empeche de nouveau individus de monter pour pouvoir fermer le batiment
                new_user = Individual(env, id)
                WAITING.append(new_user)
                print(env.now, " : Individual ", new_user.id, " waiting in RDC")
                cpt += 1
            id += 1
            print("Users created count is :",cpt)


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
        print(env.now, " : Elevator ", self.id, " DROPS Individual ", user.id, " at floor |", self.e_current, "| it takes ", eta_out)
        self.shaft.remove(user) # Le user arrive a son etage on le retire de la liste          
        if user.is_leaving is True :
            user.leaving_time = env.now
            LEFT.append(user)
        else : 
            user.is_working = True
            user.current = self.e_current
            user.expected = 1
            WORKING.append(user) # On rajoute le user a la liste working
        

    def idle(self, env):
        eta_out = abs((3 - self.e_current)*self.speed)
        print(env.now, " : Elevator ",self.id, " IDLE to floor 3, it takes :", eta_out)
        
        yield env.timeout(eta_out)
        self.e_current = 3
    
    def FCFS_handle_users(self, env):   
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
            print(env.now, " : Indiviual ", selected_user.id, " CALL Elevator ", self.id, " from |", selected_user.current, "| to reach |", selected_user.expected, "|")
            yield env.timeout(eta_in) #On bloque l'ascenceur tant qu'il n'a pas atteint l'individu
            self.e_current = selected_user.current            
            print(env.now, " : Elevator ", self.id, " PICKS Individual ", selected_user.id, "at |",self.e_current,"| it takes ", eta_in)
            if selected_user.is_leaving is True:
                selected_user.waiting_time_down = env.now
            elif selected_user.is_leaving is False:
                selected_user.waiting_time_up = env.now            
            for user in list(WAITING):        
                if len(list(self.shaft)) < CAPACITY:
                    if user.current == selected_user.current:  
                        if user.is_leaving is True:
                            user.waiting_time_down = env.now
                        elif user.is_leaving is False:
                            user.waiting_time_up = env.now
                        self.shaft.append(user)
                        WAITING.remove(user)
            cage = print_by_id(self.shaft)
            print(env.now, " : Elevator ", self.id, " CARRY ", cage)
            yield env.process(self.FCFS_handle_users(env))  
        elif (len(WAITING) == 0 and args.idle is True and self.e_current != 3):
            yield env.process(self.idle(env))
        
            
    def SSTF(self, env):
        """Shortest Seek Time First"""
        tmp = 100
        if(len(WAITING) != 0):
            for user in list(WAITING):
                if user.is_waiting == True:
                    if(abs(self.e_current - user.current) < tmp):
                        tmp = abs(self.e_current - user.current)
                        selected_user = user
            
            WAITING.remove(selected_user) #On defile le premier individu en attente
            self.shaft.append(selected_user) #On enfile le premier individu dans notre cage d'ascenceur
            eta_in = abs((self.e_current - selected_user.current)*self.speed) #Temps pour que l'ascenceur rejoigne l'individu au bon etage
            print(env.now, " : Indiviual ", selected_user.id, " CALL Elevator ", self.id, " from |", selected_user.current, "| to reach |", selected_user.expected, "|")
            yield env.timeout(eta_in)
            self.e_current = selected_user.current            
            print(env.now, " : Elevator ", self.id, " PICKS Individual ", selected_user.id, "at |",self.e_current,"| it takes ", eta_in)
            for user in list(WAITING):
                if len(list(self.shaft)) < CAPACITY:
                    if user.current == selected_user.current:
                        self.shaft.append(user)
                        WAITING.remove(user)
            yield env.process(self.SSTF_handle_users(env))
        
        elif (len(WAITING) == 0 and args.idle is True and self.e_current != 3):
            yield env.process(self.idle(env))

    def SSTF_handle_users(self, env):
        for _ in range(len(self.shaft)) :      
            tmp = 100              
            for user in list(self.shaft): 
                if(abs(self.e_current - user.expected) < tmp):
                    tmp = abs(self.e_current - user.expected)
                    chosen_user = user
        
            if chosen_user.is_leaving is True:
                chosen_user.waiting_time_down = env.now
            elif chosen_user.is_leaving is False:
                chosen_user.waiting_time_up = env.now   
                
            print("chosen user is : ", chosen_user.id)
            yield env.process(self.move(env, chosen_user))
        
    def run(self, env):
        print(env.now ," : Elevator ",self.id," is running")
        while True :
            yield env.timeout(1)
            if(args.algorithm == "FCFS"):  
                yield env.process(self.FCFS(env))
            elif(args.algorithm == "SSTF"):
                yield env.process(self.SSTF(env))
                
              
env = simpy.Environment()
pavillon = Building(env)
env.run(until=SIMU_DURATION)

getAllResult() # To Remove


def results_to_csv():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    with open(current_time+"_elevators="+str(args.elevators)+"_capacity="+str(args.capacity)+"_speed="+str(args.speed)+"_idle="+str(args.idle)+"_algorithm="+args.algorithm+"_lambda="+str(args.lambd)+".csv", 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["USER","WAITING_TIME_UP", "WAITING_TIME_DOWN", "LEAVING_TIME_CALL", "LEAVING_TIME"])
        for user in LEFT:
            writer.writerow([user.id, (user.waiting_time_up - user.arrival_time), (user.waiting_time_down - user.leaving_time_call), user.leaving_time_call, user.leaving_time])
            
results_to_csv()
