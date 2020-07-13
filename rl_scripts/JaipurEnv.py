import gym
from gym import spaces
from GameEngine import GameEngine

class JaipurEnv(gym.Env):
    
    def __init__(self):
        super().__init__()
        
        # The action space will have k=3 dimensions
        # The first is for the type of action taken (of the 4 options)
        # this first choice is independent
        # Then add a binary (2-choice) option for a maximum hand size of 12
        # (assume 7 goods cards + 5 cameles or 1 good and all 11 camels)
        # Finally add binary options for each of the 5 market cards
        # Note that the irrelevant actions (i.e. market designation when taking
        # the camels) will be ignored
        self.action_space = spaces.MultiDiscrete([4] + [2]*12 + [2]*5)
        
        
        self.observation_space = spaces.MultiDiscrete()
        
        def step(self, action):
            pass
            return observation, reward, done info
        
        def reset(self):
            return observation
        
        def render(self):
            pass
    