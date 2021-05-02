import simpy
from simpy.util import start_delayed
import random

FLOORS = [1,2,3,4,5,6,7]
SPEED = 10
CAPACITY = 1

class Elevator():
    def __init__(self, env):
        self.floors = []
        for _ in range(0,len(FLOORS)): # Fill floors with empty lists
            self.floors.append([])
        self.speed = SPEED
        self.available = simpy.Resource(env, 1)
        self.capacity = simpy.Resource(env, CAPACITY)
        self.current = 1
        self.called = []
        self.call = env.event()
        self.action = env.process(self.run(env))


    def move(self, env):
        """ Move the current elevator to the floor and consume the duration """
        floor = self.called.pop()
        duration = abs(self.current - floor) * SPEED
        print('Elevator    |%d|->|%d| at %d' % (self.current , floor, env.now))
        yield env.timeout(duration)
        self.current = floor
        print('Elevator    |%d|->|%d| at %d' % (self.current , floor, env.now))

    def run(self, env):
        """ Represents elevator behavior """
        while True:
            print("Elevator idle")
            yield self.call #passif
            print("Elevator activated")
            yield start_delayed(env, self.move(env), 5) # Elevator wait for more passengers
            #yield env.process(self.move(env))


class Passenger():
    def __init__(self, env, id, elevator):
        self.id = id
        self.current = 1
        self.expected = random.choice(FLOORS)
        self.time_to_spend = random.choice(range(50,70))
        self.elevator = elevator
        self.action = env.process(self.run(env))

    def goto_office(self, env):
        print('Passenger %d |%d|->|%d| goto_office at %d' % (self.id, self.current, self.expected, env.now))
        self.elevator.call.succeed() # wake the elevator
        self.elevator.call = env.event() # re-init event
        self.elevator.called.append(self.current)
        self.elevator.called.append(self.expected)
        while self.elevator.current != self.expected:
            yield env.timeout(1)
        self.current = self.expected
        yield env.timeout(self.time_to_spend)
        print('Passenger %d spent %d its %d' % (self.id, self.time_to_spend, env.now))


    def goto_home(self, env):
        self.expected = 1
        print('Passenger %d |%d|->|%d| goto_home' % (self.id, self.current, self.expected))
        self.elevator.call.succeed() # wake the elevator
        self.elevator.call = env.event() # re-init event
        self.elevator.called.append(self.current)
        self.elevator.called.append(self.expected)
        while self.elevator.current != self.expected:
            yield env.timeout(1)
        print('Passenger %d leave at %d' % (self.id, env.now))


    def run(self, env):
        while True:
            with self.elevator.available.request() as availability:
                yield availability                
                yield env.process(self.goto_office(env))
                yield env.process(self.goto_home(env))
                break



def passenger_generator(env, elevator):
    id = 1
    while True:
        yield env.timeout(20)
        Passenger(env, id, elevator)
        id += 1


env = simpy.Environment()
elevator = Elevator(env)
env.process(passenger_generator(env,elevator))
env.run(until=300)