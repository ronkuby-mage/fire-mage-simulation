import numpy as np

_LOG_SIM = -1 # set to -1 for no log

class Constant():
    
    def __init__(self, sim_size=10000):
        ## rotation strategies
        self._PYROBLAST = 0
        self._FROSTBOLT = 1
        self._FIRE_BLAST = 2

        self._ADAPT_ROTATION = False
        self._DEFAULT_ROTATION = self._FIRE_BLAST
        
        self._ROTATION_SIMSIZE = 3000
        self._CRIT_SIMSIZE = 50000
        self._HIT_SIMSIZE = 100000
        
        ## adapt variables
        self._LOW_MAGE_EXTRA_SCORCH = True
       
        ## scenario variables
        self._NUM_MAGES = 6
        self._HIT_CHANCE = 0.99
        self._DAMAGE = 700

        self._SP_START = 300
        self._SP_END = 900
        self._SP_STEP = 50

        self._HIT_START = 0.89
        self._HIT_END = 0.99
        self._HIT_STEP = 0.02

        self._CRIT_START = 0.10
        self._CRIT_END = 0.70
        self._CRIT_STEP = 0.05

        self._MAGES_START = 1
        self._MAGES_END = 9

        self._SIM_SIZE = sim_size

        self._DURATION_AVERAGE = 120.0
        self._DURATION_SIGMA = 12.0

        # curse of the elements and firepower (improved scorch handled on-the-fly)
        self._DAMAGE_MULTIPLIER = 1.1*1.1

        ## strategy/performance variables
        # maximum seconds before scorch expires for designated mage to start casting scorch
        self._MAX_SCORCH_REMAIN = 5.0

        # cast initial/response time variation
        self._INITIAL_SIGMA = 1.0
        self._CONTINUING_SIGMA = 0.05

        
        self._EXTRA_SCORCHES = [9000, 4, 3, 2, 2, 0, 0, 0, 0, 0]

        ## constants, do not change
        self._GLOBAL_COOLDOWN = 1.5
        
        self._IGNITE_TIME = 4.0
        self._IGNITE_TICK = 2.0
        self._IGNITE_STACK = 5

        self._SCORCH_TIME = 30.0
        self._SCORCH_STACK = 5

        self._CAST_SCORCH = 0
        self._CAST_PYROBLAST = 1
        self._CAST_FIREBALL = 2
        self._CAST_FIRE_BLAST = 3
        self._CASTS = 4

        self._MULTIPLIER = [0.428571429, 1.0, 1.0, 0.428571429]
        self._SPELL_BASE = [237, 716, 596, 446]
        self._SPELL_RANGE = [43, 174, 164, 78]
        self._IS_SCORCH = [True, False, False, False]
        self._SPELL_TIME = np.array([0.0, 0.875, 0.875, 0.0])

        self._FIREBALL_RANK = 12
        if self._FIREBALL_RANK == 11:
            self._SPELL_BASE[self._CAST_FIREBALL] = 561.0
            self._SPELL_RANGE[self._CAST_FIREBALL] = 154.0

        self._IGNITE_DAMAGE = 0.2*1.1
        self._CRIT_DAMAGE = 1.5

        self._COMBUSTIONS = 3
        self._PER_COMBUSTION = 0.1

        self._SCORCH_CASTTIME = 1.5
        self._PYROBLAST_CASTTIME = 6.0
        self._FIREBALL_CASTTIME = 3.0
        self._FIRE_BLAST_CASTTIME = 0.0

        self._FROSTBOLT_TALENTED = False
        self._FROSTBOLT_DAMAGE = 535
        self._FROSTBOLT_MODIFIER = 0.814285714
        self._FROSTBOLT_CRIT_MOD = 0.06
        self._FROSTBOLT_PLUS = 50.0

        if self._FROSTBOLT_TALENTED:
            self._FROSTBOLT_CASTTIME = 2.5
            self._FROSTBOLT_CRIT_DAMAGE = 1.0
            self._FROSTBOLT_OVERALL = 1.1*1.06
        else:
            self._FROSTBOLT_CASTTIME = 3.0
            self._FROSTBOLT_CRIT_DAMAGE = 0.5
            self._FROSTBOLT_OVERALL = 1.1

        ## debugging
        self._LOG_SPELL = ['scorch    ', 'pyroblast ', 'fireball  ', 'fire blast']
        self._LOG_SIM = _LOG_SIM
        
def init_arrays(C, num_mages, response):
    sim_size = C._SIM_SIZE
    return {
            'total_damage': np.zeros((sim_size, 1)),
            'ignite_count': np.zeros((sim_size, 1)).astype(np.int32),
            'ignite_time': np.zeros((sim_size, 1)),
            'ignite_tick': np.zeros((sim_size, 1)),
            'ignite_value': np.zeros((sim_size, 1)),
            'scorch_count': np.zeros((sim_size, 1)).astype(np.int32),
            'scorch_time': np.zeros((sim_size, 1)),
            'running_time': np.zeros((sim_size, 1)),
            'cast_timer': np.abs(response*np.random.randn(sim_size, num_mages)),
            'cast_type': C._CAST_SCORCH*np.ones((sim_size, num_mages)).astype(np.int32),
            'comb_stack': np.zeros((sim_size, num_mages)).astype(np.int32),
            'comb_left': np.zeros((sim_size, num_mages)).astype(np.int32),
            'spell_timer': C._DURATION_AVERAGE*np.ones((sim_size, num_mages)),
            'spell_type': C._CAST_SCORCH*np.ones((sim_size, num_mages)).astype(np.int32),
            'cast_number': np.zeros((sim_size, num_mages)).astype(np.int32),
            'duration': C._DURATION_AVERAGE + C._DURATION_SIGMA*np.random.randn(sim_size, 1)}

def log_message(sp, hit, crit):
    message = 'log for spell power = {:3.0f}, hit chance = {:2.0f}%, crit chance = {:2.0f}%:'
    message = message.format(sp, hit*100.0, crit*100.0)
    print(message)
    print('    KEY:')
    print('      ic = ignite stack size')
    print('      it = ignite time remaining')
    print('      in = time to next ignite tick')
    print('      ic = ignite damage per tick')
    print('      sc = scorch stack size')
    print('      st = scorch time remaining')
    print('      cs = combustion stack size (ignore if cl is 0)')
    print('      cl = combustion remaining crits')

