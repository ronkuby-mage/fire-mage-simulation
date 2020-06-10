import numpy as np

_LOG_SIM = -1 # set to -1 for no log

class Constant():
    
    def __init__(self, sim_size=1000):
        self._FIREBALL_RANK = 12
        self._FROSTBOLT_TALENTED = False
        self._FROSTBOLT_RANK = 11
        self._INCINERATE = True
        self._DMF = False
        self._SIMPLE_SPELL = False
        self._GCD = 1.0 # global cooldown "cast time"
        
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
        self._CAST_TIME = np.array([1.5, 6.0, 3.0, 0.0, 3.0, self._GCD])
        self._SPELL_TIME = np.array([0.0, 0.875, 0.875, 0.0, 0.75])

        if self._FIREBALL_RANK == 11:
            self._SPELL_BASE[self._CAST_FIREBALL] = 561.0
            self._SPELL_RANGE[self._CAST_FIREBALL] = 154.0

        if self._FROSTBOLT_RANK == 10:
            self._SPELL_BASE[self._CAST_FROSTBOLT] = 440.0
            self._SPELL_RANGE[self._CAST_FROSTBOLT] = 75.0
        elif self._FROSTBOLT_RANK == 1:
            self._SPELL_BASE[self._CAST_FROSTBOLT] = 20.0
            self._SPELL_RANGE[self._CAST_FROSTBOLT] = 2.0
            self._CAST_TIME[self._CAST_FROSTBOLT] = 1.5
            self._SP_MULTIPLIER[self._CAST_FROSTBOLT] = 0.407142857

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

        ## decision making
        self._SCORCHES = np.array([9000, 6, 3, 2, 2, 2, 1, 1, 1, 1])
        self._DECIDE = {
            "scorch": self._CAST_SCORCH,
            "pyroblast": self._CAST_PYROBLAST,
            "fireball": self._CAST_FIREBALL,
            "fire_blast": self._CAST_FIRE_BLAST,
            "frostbolt": self._CAST_FROSTBOLT,
            "gcd": self._CAST_GCD,
            "combustion": self._CAST_COMBUSTION,
            "mqg": self._CAST_MQG,
            "pi": self._CAST_POWER_INFUSION}
        self._AVAIL = {
            "mqg": self._BUFF_MQG,
            "pi": self._BUFF_POWER_INFUSION}
        
        ## debugging
        self._LOG_SPELL = ['scorch    ', 'pyroblast ', 'fireball  ', 'fire blast', 'frostbolt ', 'gcd       ', 'combustion', 'mqg       ', 'power inf ']
        self._LOG_SIM = _LOG_SIM

class ArrayGenerator():

    def __init__(self, params):
        self._params = params

    @staticmethod
    def _distribution(entry, size):
        array = None
        if isinstance(entry, float):
            array = entry*np.ones(size)
        elif 'mean' in entry:
            array = entry['mean']*np.ones(size)
            if 'var' in entry:
                array += entry['var']*np.random.randn(*size)
            if 'clip' in entry:
                array = np.maximum(entry['clip'][0], array)
                array = np.minimum(entry['clip'][1], array)
        elif 'fixed' in entry:
            array = np.tile(entry['fixed'][None, :], (size[0], 1))

        return array
        
    def run(self, C):
        sim_size = self._params['sim_size']
        num_mages = self._params['num_mages']['num_mages']
        arrays = {
            'global': {
                'total_damage': np.zeros(sim_size),
                'running_time': np.zeros(sim_size),
                'decision': np.zeros(sim_size).astype(np.bool)},
            'boss': {
                'ignite_timer': np.zeros(sim_size),
                'ignite_count': np.zeros(sim_size).astype(np.int32),
                'ignite_value': np.zeros(sim_size),
                'ignite_multiplier': np.ones(sim_size),
                'tick_timer': C._LONG_TIME*np.ones(sim_size),
                'scorch_timer': np.zeros(sim_size),
                'scorch_count': np.zeros(sim_size).astype(np.int32),
                'debuff_timer': [np.zeros(sim_size) for aa in range(C._DEBUFFS)],
                'debuff_avail': [np.zeros(sim_size).astype(np.int32) for aa in range(C._DEBUFFS)]},
            'player': {
                'cast_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'spell_timer': C._LONG_TIME*np.ones((sim_size, num_mages)),
                'spell_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'comb_stack': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_left': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_avail': np.ones((sim_size, num_mages)).astype(np.int32),
                'cast_number': -np.ones((sim_size, num_mages)).astype(np.int32),
                'buff_timer': [np.zeros((sim_size, num_mages)) for aa in range(C._BUFFS)],
                'buff_avail': [np.zeros((sim_size, num_mages)).astype(np.int32) for aa in range(C._BUFFS)],
                'gcd': np.zeros((sim_size, num_mages))
            }
        }
        if self._params["mc"]:
            arrays['global']['ignite'] = np.zeros(sim_size)
        if 'duration' in self._params:
            arrays['global']['duration'] = self._params['duration']
        else:
            arrays['global']['duration'] = self._distribution(self._params['timing']['duration'],
                                                              sim_size)
        arrays['player']['cast_timer'] = np.abs(self._params['delay']*np.random.randn(sim_size,
                                                                                      num_mages))
        if self._params["mc"]:
            if "correlated_fraction" in self._params["mc"]:
                if np.random.rand() < self._params["mc"]["correlated_fraction"]:
                    for name in ['spell_power', 'hit_chance', 'crit_chance']:
                        value = np.random.rand()
                        entry = {'mean': self._params[name]['fixed'][0]*(1 - value) +\
                                         self._params[name]['fixed'][1]*value,
                                 'var': self._params["mc"]["correlated_std"]*(self._params[name]['fixed'][1] - self._params[name]['fixed'][0]),
                                 'clip': self._params[name]['fixed']}
                        self._params[name] = entry
                    
        for name in ['spell_power', 'hit_chance', 'crit_chance']:
            arrays['player'][name] = self._distribution(self._params[name],
                                                        (sim_size, num_mages))
            if "chance" in name:
                arrays['player'][name] = (100*arrays['player'][name]).astype(np.int32)
                arrays['player'][name] = arrays['player'][name].astype(np.float)/100.0
            
        arrays['player']['spell_power'].sort(axis=1)
        if 'single' in self._params:
            name = [k for k, v in self._params['stats'].items() if 'single' in v][0]
            arrays['player'][name][np.arange(sim_size),
            self._params['stats'][name]['single']['slot']] = self._params['single']
        config = [config for config in self._params['configuration'] if config['num_mages'] == num_mages][0]
        arrays['player']['buff_avail'][C._BUFF_MQG][:, (num_mages - config['num_mqg']):] = 1
        arrays['player']['buff_avail'][C._BUFF_POWER_INFUSION][:, (num_mages - config['num_pi']):] = 1
        
        return arrays
            
def log_message():
    print('LOG:')
    print('    KEY:')
    print('      ic = ignite stack size')
    print('      it = ignite time remaining')
    print('      in = time to next ignite tick')
    print('      ic = ignite damage per tick')
    print('      sc = scorch stack size')
    print('      st = scorch time remaining')
    print('      cs = combustion stack size (ignore if cl is 0)')
    print('      cl = combustion remaining crits')

