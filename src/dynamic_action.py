import gym
import numpy as np

#You could also inherit from Discrete or Box here and just override the shape(), sample() and contains() methods
class DynamicSpace(gym.Space.Discrete):
"""x where x in available actions {0,1,3,5,...,n-1}
Example usage:
self.action_space = spaces.Dynamic(max_space=2)
"""

    def __init__(self, max_space):
        super(DynamicSpace, self).__init__((), max_space)

        #initially all actions are available
        self.available_actions = set(range(max_space))

    def set_actions(self, actions):
        """ You would call this method inside your environment to enable actions"""
        self.available_actions = actions

    def sample(self):
        return np.random.choice(np.array(list(self.available_actions)))

    def contains(self, x):
        return x in self.available_actions

    @property
    def shape(self):
        """Return the new shape here"""
        return tuple(len(self.available_actions))

    def __repr__(self):
        return "Dynamic {" + [str(aa) + ', ' for aa in self.available_actions]

    def __eq__(self, other):
        if not isinstance(other, DynamicSpace):
            return False
        return self.available_actions == other.available_actions
