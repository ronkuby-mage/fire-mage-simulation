import numpy as np

_LOG_SIM = 99273 # set to -1 for no log

class Constant():
    
    def __init__(self, sim_size=10000):
        self._FIREBALL_RANK = 12
        self._FROSTBOLT_TALENTED = False
        self._FROSTBOLT_RANK = 11
        self._INCINERATE = False
        self._DMF = False
        self._SIMPLE_SPELL = False
        
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

        self._DURATION_AVERAGE = 45.0
        self._DURATION_SIGMA = 6.0

        ## strategy/performance variables
        # maximum seconds before scorch expires for designated mage to start casting scorch
        self._MAX_SCORCH_REMAIN = 5.0

        # cast initial/response time variation
        self._INITIAL_SIGMA = 1.0
        self._CONTINUING_SIGMA = 0.05
        
        self._SCORCHES = np.array([9000, 5, 4, 2, 2, 1, 1, 1, 1, 1])

        ## constants, do not change
        self._GLOBAL_COOLDOWN = 1.5
        
        self._IGNITE_TIME = 4.0
        self._IGNITE_TICK = 2.0
        self._IGNITE_STACK = 5

        self._SCORCH_TIME = 30.0
        self._SCORCH_STACK = 5

        self._COE_MULTIPLIER = 1.1
        self._SCORCH_MULTIPLIER = 0.03

        self._CAST_SCORCH = 0
        self._CAST_PYROBLAST = 1
        self._CAST_FIREBALL = 2
        self._CAST_FIRE_BLAST = 3
        self._CAST_FROSTBOLT = 4
        self._CAST_GCD = 5 # placeholder for extra time due to GCD
        # below this line are instant/external source casts
        self._CAST_COMBUSTION = 6
        self._CAST_MQG = 7
        self._CAST_POWER_INFUSION = 8
        self._CASTS = 9

        self._SP_MULTIPLIER = np.array([0.428571429, 1.0, 1.0, 0.428571429, 0.814285714])
        self._DAMAGE_MULTIPLIER = np.array([1.1, 1.1, 1.1, 1.1, 1.0]) # fire power
        if self._SIMPLE_SPELL:
            self._SPELL_BASE = np.array([250, 900, 750, 500, 500])
            self._SPELL_RANGE = np.array([0, 0, 0, 0, 0])
        else:
            self._SPELL_BASE = np.array([237, 716, 596, 446, 515])
            self._SPELL_RANGE = np.array([43, 174, 164, 78, 40])
        self._IS_SCORCH = np.array([True, False, False, False, False])
        self._IS_FIRE = np.array([1.0, 1.0, 1.0, 1.0, 0.0])
        self._INCIN_BONUS = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        self._CAST_TIME = np.array([1.5, 6.0, 3.0, 0.0, 3.0, 3.0])
        self._SPELL_TIME = np.array([0.0, 0.875, 0.875, 0.0, 0.75])

        if self._FIREBALL_RANK == 11:
            self._SPELL_BASE[self._CAST_FIREBALL] = 561.0
            self._SPELL_RANGE[self._CAST_FIREBALL] = 154.0

        if self._FROSTBOLT_RANK == 10:
            self._SPELL_BASE[self._CAST_FIREBALL] = 440.0
            self._SPELL_RANGE[self._CAST_FIREBALL] = 75.0

        if self._FROSTBOLT_TALENTED:
            self._DAMAGE_MULTIPLIER[self._CAST_FROSTBOLT] = 1.06
            self._CAST_TIME[self._CAST_FROSTBOLT] = 2.5
            self._FROSTBOLT_CRIT_DAMAGE = 1.0
            self._FROSTBOLT_OVERALL = 1.1*1.06

        if self._INCINERATE:
            self._INCIN_BONUS = np.array([0.04, 0.0, 0.0, 0.04, 0.0])

        # BUFFs have simple mechanics: limited use and a timer
        self._POWER_INFUSION = 0.2
        self._MQG = 0.33

        self._BUFF_MQG = 0
        self._BUFF_POWER_INFUSION = 1
        self._BUFFS = 2

        self._BUFF_DURATION = np.array([20.0, 15.0])
        self._BUFF_CAST_TYPE = np.array([self._CAST_MQG, self._CAST_POWER_INFUSION])

        self._DEBUFFS = 0

        self._DMF_BUFF = 1.0 if not self._DMF else 1.1

        self._IGNITE_DAMAGE = 0.2
        self._ICRIT_DAMAGE = 0.5
        self._CRIT_DAMAGE = 1.0 if self._FROSTBOLT_TALENTED else 0.5

        self._COMBUSTIONS = 3
        self._PER_COMBUSTION = 0.1
        
        self._LONG_TIME = 999*self._DURATION_AVERAGE

        ## debugging
        self._LOG_SPELL = ['scorch    ', 'pyroblast ', 'fireball  ', 'fire blast', 'frostbolt ', 'gcd       ', 'combustion', 'mqg       ', 'power inf ']
        self._LOG_SIM = _LOG_SIM
        
def init_const_arrays(C, sp, hit, crit, num_mages, response):
    sim_size = C._SIM_SIZE
    return {
            'global': {
                'total_damage': np.zeros(sim_size),
                'running_time': np.zeros(sim_size),
                'duration': C._DURATION_AVERAGE + C._DURATION_SIGMA*np.random.randn(sim_size),
                'decision': np.zeros(sim_size).astype(np.bool)},
            'boss': {
                'ignite_timer': np.zeros(sim_size),
                'ignite_count': np.zeros(sim_size).astype(np.int32),
                'ignite_value': np.zeros(sim_size),
                'ignite_multiplier': np.zeros(sim_size),
                'tick_timer': C._LONG_TIME*np.ones(sim_size),
                'scorch_timer': np.zeros(sim_size),
                'scorch_count': np.zeros(sim_size).astype(np.int32),
                'debuff_timer': [np.zeros(sim_size) for aa in range(C._DEBUFFS)],
                'debuff_avail': [np.zeros(sim_size).astype(np.int) for aa in range(C._DEBUFFS)]},
            'player': {
                'cast_timer': np.abs(response*np.random.randn(sim_size, num_mages)),
                'cast_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'spell_timer': C._LONG_TIME*np.ones((sim_size, num_mages)),
                'spell_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'comb_stack': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_left': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_avail': np.ones((sim_size, num_mages)).astype(np.int32),
                'cast_number': np.zeros((sim_size, num_mages)).astype(np.int32),
                'buff_timer': [np.zeros((sim_size, num_mages)) for aa in range(C._BUFFS)],
                'buff_avail': [np.zeros((sim_size, num_mages)).astype(np.int) for aa in range(C._BUFFS)],
                'spell_power': sp*np.ones((sim_size, num_mages)),
                'hit_chance': hit*np.ones((sim_size, num_mages)),
                'crit_chance': crit*np.ones((sim_size, num_mages)),
                'gcd': np.zeros((sim_size, num_mages))}
            }
            

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

