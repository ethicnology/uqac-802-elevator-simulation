import simpy
from simpy.util import start_delayed
from collections import deque
import random

FLOORS = [1,2,3,4,5,6,7]
SPEED = 10
CAPACITY = 2
ELEVATOR = 1

class Elevator():
    def __init__(self, env):
        self.speed = SPEED
        self.available = simpy.Resource(env, ELEVATOR)
        self.capacity = simpy.Resource(env, CAPACITY)
        self.current = 1
        self.memory = deque([])
        self.Used = False
        self.Moving = False
        self.call = env.event()
        self.action = env.process(self.run(env))

    def move(self, env):
        """ Move the current elevator to the floor and consume the duration """
        self.Moving = True
        floor = self.memory.popleft()
        duration = abs(self.current - floor) * SPEED
        print('Elevator  ▲ |%d|->|%d| at %d' % (self.current , floor, env.now))
        yield env.timeout(duration)
        print('Elevator  ► |%d|->|%d| at %d' % (self.current , floor, env.now))
        self.current = floor
        self.Moving = False


    def run(self, env):
        """ Represents elevator behavior """
        while True:
            print("Elevator idle")
            yield self.call #passif
            print("Elevator activated")
            yield env.process(self.move(env))
            yield start_delayed(env, self.move(env), 5) # Elevator wait for more passengers

class Passenger():
    def __init__(self, env, id, elevator):
        self.id = id
        self.expected = random.randint(FLOORS[1], FLOORS[6]) # Choose a floor between 2 and 7
        self.time_to_spend = random.choice(range(50,70))
        self.elevator = elevator
        self.action = env.process(self.run(env))

    def goto_office(self, env):
        self.current = 1
        print('Passenger %d |%d|->|%d| goto_office at %d' % (self.id, self.current, self.expected, env.now))
        yield env.process(self.call_elevator(env))
        #yield env.process(self.use_elevator(env))
        print('Passenger %d arrived to floor %d at %d' % (self.id, self.current, env.now))
        yield env.timeout(self.time_to_spend)
        print('Passenger %d spent %d its %d' % (self.id, self.time_to_spend, env.now))
        
    def goto_home(self, env):
        self.expected = 1
        print('Passenger %d |%d|->|%d| goto_home at %d' % (self.id, self.current, self.expected, env.now))
        yield env.process(self.call_elevator(env))
        #yield env.process(self.use_elevator(env))
        print('Passenger %d leave at %d' % (self.id, env.now))

    def call_elevator(self, env):
        while self.elevator.Moving == True:
            yield env.timeout(1)
        with self.elevator.available.request() as availability:
            yield availability
            self.elevator.call.succeed() # wake the elevator
            self.elevator.call = env.event() # re-init event
            self.elevator.memory.append(self.current)
            print(self.elevator.memory)
            while self.elevator.current != self.current: 
                yield env.timeout(1)
            yield env.process(self.use_elevator(env))

    def use_elevator(self, env):
        self.elevator.call.succeed() # wake the elevator
        self.elevator.call = env.event() # re-init event
        self.elevator.memory.append(self.expected)
        print(self.elevator.memory)
        while self.elevator.current != self.expected:
            yield env.timeout(1)
        self.current = self.expected

    def run(self, env):
        while True:
            yield env.process(self.goto_office(env))
            yield env.process(self.goto_home(env))
            break


def passenger_generator(env, elevator):
    id = 1
    while True:
        yield env.timeout(120)
        Passenger(env, id, elevator)
        id += 1

env = simpy.Environment()
elevator = Elevator(env)
env.process(passenger_generator(env,elevator))
env.run(until=500)