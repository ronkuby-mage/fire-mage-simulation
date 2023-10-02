import numpy as np

_LOG_SIM = -1 # set to -1 for no log

class Constant():
    
    def __init__(self, double_dip, sim_size=1000):
       
        self._FIREBALL_RANK = 12
        self._FROSTBOLT_TALENTED = False
        self._FROSTBOLT_RANK = 11
        self._INCINERATE = True
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
        
        ## constants, do not change
        self._GLOBAL_COOLDOWN = 1.5
        
        self._IGNITE_TIME = 4.0
        self._IGNITE_TICK = 2.0
        self._IGNITE_STACK = 5

        self._SCORCH_TIME = 30.0
        self._SCORCH_STACK = 5

        self._COE_MULTIPLIER = 1.1
        self._SCORCH_MULTIPLIER = 0.03
        
        self._FIRE_BLAST_COOLDOWN = 7.0 # two talent points

        self._CAST_SCORCH = 0
        self._CAST_PYROBLAST = 1
        self._CAST_FIREBALL = 2
        self._CAST_FIRE_BLAST = 3
        self._CAST_FROSTBOLT = 4
        self._CAST_GCD = 5 # placeholder for extra time due to GCD
        # below this line are instant/external source casts
        self._CAST_COMBUSTION = 6
        self._CAST_SAPP = 7
        self._CAST_TOEP = 8
        self._CAST_ZHC = 9
        self._CAST_MQG = 10
        self._CAST_POWER_INFUSION = 11
        self._CASTS = 12

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
        self._CAST_TIME = np.array([1.5, 6.0, 3.0, 0.0, 3.0, self._GLOBAL_COOLDOWN])
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

        self._BUFF_SAPP = 0
        self._BUFF_TOEP = 1
        self._BUFF_ZHC = 2
        self._BUFF_MQG = 3
        self._BUFF_POWER_INFUSION = 4
        self._BUFFS = 5
        self._DAMAGE_BUFFS = 3

        self._BUFF_DURATION = np.array([20.0, 15.0, 20.0, 20.0, 15.0])
        self._BUFF_CAST_TYPE = np.array([self._CAST_SAPP, self._CAST_TOEP, self._CAST_ZHC, self._CAST_MQG, self._CAST_POWER_INFUSION])
        self._BUFF_COOLDOWN = np.array([120.0, 90.0, 120.0, 300.0, 180.0])
        self._BUFF_DAMAGE = np.array([130.0, 175.0, 204.0])
        self._BUFF_PER_TICK = np.array([0.0, 0.0, -17.0])

        self._DEBUFFS = 0

        self._NORMAL_BUFF = double_dip
        self._CRIT_BUFF = 1.0
        self._IGNITE_BUFF = double_dip

        self._NORMAL_BUFF_C = double_dip*1.02
        self._CRIT_BUFF_C = 1.02
        self._IGNITE_BUFF_C = double_dip*1.02

        self._IGNITE_DAMAGE = 0.2
        self._ICRIT_DAMAGE = 0.5
        self._CRIT_DAMAGE = 1.0 if self._FROSTBOLT_TALENTED else 0.5

        self._COMBUSTIONS = 3
        self._PER_COMBUSTION = 0.1
        self._COMBUSTION_COOLDOWN = 180.0
        
        self._LONG_TIME = 999*self._DURATION_AVERAGE

        ## decision making
        self._SCORCHES = np.array([9000, 6, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1])
        self._DECIDE = {
            "scorch": self._CAST_SCORCH,
            "pyroblast": self._CAST_PYROBLAST,
            "fireball": self._CAST_FIREBALL,
            "fire_blast": self._CAST_FIRE_BLAST,
            "frostbolt": self._CAST_FROSTBOLT,
            "gcd": self._CAST_GCD,
            "combustion": self._CAST_COMBUSTION,
            "sapp": self._CAST_SAPP,
            "toep": self._CAST_TOEP,
            "zhc": self._CAST_ZHC,
            "mqg": self._CAST_MQG,
            "pi": self._CAST_POWER_INFUSION}
        self._BUFF_LOOKUP = {
            "sapp": self._BUFF_SAPP,
            "toep": self._BUFF_TOEP,
            "zhc": self._BUFF_ZHC,
            "mqg": self._BUFF_MQG,
            "pi": self._BUFF_POWER_INFUSION}
        
        ## debugging
        self._LOG_SPELL = ['scorch    ', 'pyroblast ', 'fireball  ', 'fire blast', 'frostbolt ', 'gcd       ', 'combustion',  'sapp      ', 'toep      ', 'zhc       ', 'mqg       ', 'power inf ']
        self._LOG_SIM = _LOG_SIM
        
        self._RES_AMOUNT = [1.0, 0.75, 0.5, 0.25]
        self._RES_THRESH = [0.0, 0.8303, 0.9415, 0.9905]
        self._RES_THRESH_UL = [0.8303, 0.9415, 0.9905, 1.0]
        #self._RESISTANCE_MODIFIER = 0.966975
        self._RESISTANCE_MODIFIER = 0.940997
        
        self._DECISION_POINT = 2.0
        
        self._DRAGONLING_DURATION = 60.0
        self._DRAGONLING_BUFF = 300
        
        self._NIGHTFALL_PROB = 0.15
        self._NIGHTFALL_BUFF = 0.15
        self._NIGHTFALL_DURATION = 5.0

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
                array += entry['var']*np.random.randn(size)
            if 'clip' in entry:
                array = np.maximum(entry['clip'][0], array)
                array = np.minimum(entry['clip'][1], array)
        elif 'value' in entry:
            array = np.tile(entry['fixed'][None, :], (size[0], 1))

        return array
        
    def run(self, C, dur_dist):
        sim_size = self._params['sim_size']
        num_mages = self._params['configuration']['num_mages']
        arrays = {
            'global': {
                'total_damage': [[] for dummy in range(sim_size)] if dur_dist else np.zeros(sim_size),
                'running_time': np.zeros(sim_size),
                'decision': np.zeros(sim_size).astype(bool),
                'ignite': [[] for dummy in range(sim_size)] if dur_dist else np.zeros(sim_size),
                'crit': np.zeros(sim_size),
                'player': np.zeros(sim_size)},
            'boss': {
                'ignite_timer': np.zeros(sim_size),
                'ignite_count': np.zeros(sim_size).astype(np.int32),
                'ignite_value': np.zeros(sim_size),
                'ignite_multiplier': np.ones(sim_size),
                'tick_timer': C._LONG_TIME*np.ones(sim_size),
                'scorch_timer': np.zeros(sim_size),
                'scorch_count': np.zeros(sim_size).astype(np.int32),
                'debuff_timer': [np.zeros(sim_size) for aa in range(C._DEBUFFS)],
                'debuff_avail': [np.zeros(sim_size).astype(np.int32) for aa in range(C._DEBUFFS)],
                'dragonling': -C._DRAGONLING_DURATION,
                'spell_vulnerability': np.zeros((sim_size))},
            'player': {
                'cast_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'spell_timer': C._LONG_TIME*np.ones((sim_size, num_mages)),
                'spell_type': C._CAST_GCD*np.ones((sim_size, num_mages)).astype(np.int32),
                'comb_stack': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_left': np.zeros((sim_size, num_mages)).astype(np.int32),
                'comb_avail': np.ones((sim_size, num_mages)).astype(np.int32),
                'comb_cooldown': np.inf*np.ones((sim_size, num_mages)).astype(np.int32),
                'cast_number': -np.ones((sim_size, num_mages)).astype(np.int32),
                'buff_timer': [np.zeros((sim_size, num_mages)) for aa in range(C._BUFFS)],
                'buff_cooldown': [np.inf*np.ones((sim_size, num_mages)) for aa in range(C._BUFFS)],
                'buff_ticks': [np.zeros((sim_size, num_mages)).astype(np.int32) for aa in range(C._DAMAGE_BUFFS)],
                'fb_cooldown': np.zeros((sim_size, num_mages)),
                'crit_too_late': np.zeros((sim_size, num_mages)).astype(bool),
                'nightfall': np.inf*np.ones((sim_size)).reshape(sim_size, 1),
                'gcd': np.zeros((sim_size, num_mages))
            }
        }
            
        arrays['global']['duration'] = self._distribution(self._params['timing']['duration'], sim_size)
        arrays['player']['cast_timer'] = np.abs(self._params['timing']['delay']*np.random.randn(sim_size, num_mages))
        
        arrays["player"]["spell_power"] = np.tile(np.array(self._params["stats"]["spell_power"])[None, :], (sim_size, 1))
        arrays["player"]["spell_power"] += 35*("greater_arcane_elixir" in self._params["buffs"]["consumes"])
        arrays["player"]["spell_power"] += 40*("elixir_of_greater_firepower" in self._params["buffs"]["consumes"])
        arrays["player"]["spell_power"] += 150*("flask_of_supreme_power" in self._params["buffs"]["consumes"])
        arrays["player"]["spell_power"] += 60*("blessed_wizard_oil" in self._params["buffs"]["consumes"])
        arrays["player"]["spell_power"] += 36*("brilliant_wizard_oil" in self._params["buffs"]["consumes"])
        arrays["player"]["spell_power"] += 23*("very_berry_cream" in self._params["buffs"]["consumes"])
        
        intellect = np.tile(np.array(self._params["stats"]["intellect"], dtype=np.float32)[None, :], (sim_size, 1))
        intellect += 31.0*float("arcane_intellect" in self._params["buffs"]["raid"])
        intellect += 1.35*12.0*float("improved_mark" in self._params["buffs"]["raid"])
        intellect += 30.0*float("stormwind_gift_of_friendship" in self._params["buffs"]["consumes"])
        intellect += 25.0*float("infallible_mind" in self._params["buffs"]["consumes"])
        intellect += 10.0*float("runn_tum_tuber_surprise" in self._params["buffs"]["consumes"])

        intellect *= (1 + 0.1*float("blessing_of_kings" in self._params["buffs"]["raid"]))*(1 + 0.15*float("spirit_of_zandalar" in self._params["buffs"]["world"]))
        racial = np.array([1.05 if rac == "gnome" else 1.0 for rac in self._params["buffs"]["racial"]])
        intellect *= racial

        # 0.062 = 6% talents + 0.2% base
        arrays["player"]["crit_chance"] = 0.062 + np.tile(np.array(self._params["stats"]["crit_chance"])[None, :], (sim_size, 1))
        arrays["player"]["crit_chance"] += 0.01*float("brilliant_wizard_oil" in self._params["buffs"]["consumes"])
        arrays["player"]["crit_chance"] += 0.1*float("rallying_cry_of_the_dragonslayer" in self._params["buffs"]["world"])
        arrays["player"]["crit_chance"] += 0.03*float("moonkin_aura" in self._params["buffs"]["raid"])
        arrays["player"]["crit_chance"] += 0.05*float("songflower_serenade" in self._params["buffs"]["world"])
        arrays["player"]["crit_chance"] += 0.03*float("dire_maul_tribute" in self._params["buffs"]["world"])
        arrays["player"]["crit_chance"] += intellect/5950
        arrays["player"]["crit_chance"] += 0.60*float(self._params["buffs"]["boss"] == "loatheb")
        arrays["player"]["crit_chance"] = np.minimum(1.00, arrays["player"]["crit_chance"])
        
        arrays["player"]["hit_chance"] = 0.89 + np.tile(np.array(self._params["stats"]["hit_chance"])[None, :], (sim_size, 1))
        arrays["player"]["hit_chance"] = np.minimum(0.99, arrays["player"]["hit_chance"])
        
        if False:
            for index in self._params["configuration"]["target"]:
                print(f'Spell Power = {arrays["player"]["spell_power"][0][index]:.0f}  Crit Chance = {100*arrays["player"]["crit_chance"][0][index]:.2f}  Int = {intellect[0][index]:.1f}')
            dwplwd()
        
        for key, val in C._BUFF_LOOKUP.items():
            for index in self._params["configuration"][key]:
                arrays["player"]["buff_cooldown"][val][:, index] = 0.0
        
        arrays["player"]["cleaner"] = np.array(self._params["configuration"]["udc"]).reshape(1, len(self._params["configuration"]["udc"]))
        arrays["player"]["pi"] = np.array(self._params["configuration"]["pi"]).reshape(1, len(self._params["configuration"]["pi"]))
        arrays["player"]["target"] = np.array(self._params["configuration"]["target"]).reshape(1, len(self._params["configuration"]["target"]))

        if "proc" in self._params["buffs"]:
            if "dragonling" in self._params["buffs"]["proc"]:
                arrays["boss"]["dragonling"] = self._params["buffs"]["proc"]["dragonling"]
            if "nightfall" in self._params["buffs"]["proc"]:
                nightfall = []
                for period in self._params["buffs"]["proc"]["nightfall"]:
                    nightfall.append(period*np.ones((sim_size)))
                arrays["player"]["nightfall"] = np.stack(nightfall, axis=1)
                arrays["player"]["nightfall_period"] = np.array(self._params["buffs"]["proc"]["nightfall"])

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

