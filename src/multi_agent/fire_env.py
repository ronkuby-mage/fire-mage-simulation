import sys
import numpy as np
from ray.rllib.env import MultiAgentEnv
from gym import spaces
import constants

class FireMageEnv(MultiAgentEnv):

    def __init__(self, config):
        self._config = config
        self._C = constants.Constant()
        b1 = [int(self._config['num_mages'] - ii <= self._config['mqg'])\
               for ii in range(self._config['num_mages'])]
        b2 = [int(self._config['num_mages'] - ii <= self._config['power_infusion'])\
               for ii in range(self._config['num_mages'])]
        self._numbufs = [a + b for a, b in zip(b1, b2)]

    def _get_reward(self, mage, span=False):
        ctime = min([self._state['global']['running_time'],
                     self._state['global']['duration']])
        l_e = 0.0 if span else self._state['player']['last_eval'][mage] 
        player_damage = sum([d[1] for d in self._state['player']['damage'][mage]\
                             if d[0] >= l_e and d[0] < ctime])
        ignite_damage = sum([d[1] for d in self._state['boss']['ignite_damage']\
                             if d[0] >= l_e and d[0] < ctime])
        self._state['player']['last_eval'][mage] = ctime

        reward = player_damage + ignite_damage/self._config['num_mages']
        reward /= self._state['global']['duration']

        return reward

    def step(self, action_in):
        if isinstance(action_in, dict):
            action = list(action_in.values())[0]
        else:
            action = action_in
        last_hit = np.argmin(self._state['player']['cast_timer'])
        self._apply_decision(action, last_hit)
        while self._advance():
            if self._state['global']['running_time'] < self._state['global']['duration']:
                self._state['global']['total_damage'] += self._state['global']['damage']

        next_hit = np.argmin(self._state['player']['cast_timer'])
        obs = self._get_obs(next_hit)

        # total damage since last cast        
        reward = self._get_reward(next_hit)

        done = self._state['global']['running_time'] >= self._state['global']['duration']
        
        if not done:
            return ({"mage_" + str(next_hit + 1): obs},
                    {"mage_" + str(next_hit + 1): reward/100.0},
                    {"__all__": False},
                    {})
        else:
            obs = []
            rewards = []
            for ii in range(self._config['num_mages']):
                obs.append(("mage_" + str(ii + 1), self._get_obs(ii)))
                rewards.append(("mage_" + str(ii + 1), self._get_reward(ii, span=False)/100.0))
            return dict(obs), dict(rewards), {"__all__": done}, {}
                           

    def reset(self, retain_stats=False):
        num_mages = self._config['num_mages']
        if not retain_stats:
            duration = self._config['duration_average'] +\
                       self._config['duration_sigma']*np.random.randn()
            duration = max([self._config['duration_average']/2.0, duration])
            spell_power = self._config['sp_average'] +\
                          self._config['sp_sigma']*np.random.randn(num_mages)
            spell_power = spell_power.astype(np.int32).astype(np.float)
            # first mage may be scorch mage, last is finisher
            spell_power.sort()
            hit_chance = self._config['hit_average'] +\
                         self._config['hit_sigma']*np.random.randn(num_mages)
            hit_chance = np.minimum(0.99, (hit_chance*100).astype(np.int32).astype(np.float)/100.0)
            hit_chance = np.maximum(0.89, hit_chance)
            crit_chance = self._config['crit_average'] +\
                          self._config['crit_sigma']*np.random.randn(num_mages)
        else:
            duration = self._state['global']['duration']
            spell_power = self._state['player']['spell_power']
            hit_chance = self._state['player']['hit_chance']
            crit_chance = self._state['player']['crit_chance']
        crit_chance = np.maximum(0.0, (crit_chance*100).astype(np.int32).astype(np.float)/100.0)
        cast_timer = np.abs(self._config['response_time']*np.random.randn(num_mages))
        duration += np.min(cast_timer)
        cast_timer -= np.min(cast_timer)
        buff_avail = np.zeros((self._C._BUFFS, num_mages), dtype=np.int32)
        buff_avail[self._C._BUFF_MQG, (num_mages - self._config['mqg']):] = 1
        buff_avail[self._C._BUFF_POWER_INFUSION, (num_mages - self._config['power_infusion']):] = 1
        self._state = {
            'global': {
                'total_damage': 0.0,
                'running_time': 0.0,
                'duration': duration,
                'decision': True
            },
            'boss': {
                'ignite_timer': 0.0,
                'ignite_count': 0,
                'ignite_value': 0.0,
                'ignite_multiplier': 1.0,
                'tick_timer': self._C._LONG_TIME,
                'scorch_timer': 0.0,
                'scorch_count': 0,
                'debuff_timer': [0.0 for aa in range(self._C._DEBUFFS)],
                'debuff_avail': [0 for aa in range(self._C._DEBUFFS)],
                'ignite_damage': []
            },
            'player': {
                'cast_timer': cast_timer,
                'cast_type': self._C._CAST_GCD*np.ones(num_mages).astype(np.int32),
                'spell_timer': self._C._LONG_TIME*np.ones(num_mages),
                'spell_type': self._C._CAST_GCD*np.ones(num_mages).astype(np.int32),
                'comb_stack': np.zeros(num_mages).astype(np.int32),
                'comb_left': np.zeros(num_mages).astype(np.int32),
                'comb_avail': np.ones(num_mages).astype(np.int32),
                'cast_number': np.zeros(num_mages).astype(np.int32),
                'buff_avail': buff_avail,
                'buff_timer': np.zeros((self._C._BUFFS, num_mages)),
                'spell_power': spell_power,
                'hit_chance': hit_chance,
                'crit_chance': crit_chance,
                'gcd': np.zeros(num_mages),
                'damage': [[] for a in range(num_mages)],
                'last_eval': np.zeros(num_mages)
            }
        }
        log1 = 'log for spell power = {:3.0f}, hit chance = {:2.0f}%, crit chance = {:2.0f}%:'
        self._log = [log1.format(self._config['sp_average'],
                                 self._config['hit_average']*100.0,
                                 self._config['crit_average']*100.0),
                     '    KEY:',
                     '      ic = ignite stack size',
                     '      it = ignite time remaining',
                     '      in = time to next ignite tick',
                     '      ic = ignite damage per tick',
                     '      sc = scorch stack size',
                     '      st = scorch time remaining',
                     '      cs = combustion stack size (ignore if cl is 0)',
                     '      cl = combustion remaining crits']
                     
        next_hit = np.argmin(self._state['player']['cast_timer'])
        self._state['player']['cast_number'][next_hit] += 1

        return {"mage_" + str(next_hit + 1): self._get_obs(next_hit)}

    def total(self):
        return self._state['global']['total_damage']
    
    def render(self, mode='human', close=False):
        for log_line in self._log:
            print(log_line)

    @property
    def next_hit(self):
        return np.argmin(self._state['player']['cast_timer'])
            
    def _get_actions(self, next_hit):
        actions = set(range(self._C._CAST_GCD))
        actions.remove(self._C._CAST_FIRE_BLAST) # cooldown not implemented it anyway
        if self._state['player']['comb_avail'][next_hit] > 0:
            actions.add(self._C._CAST_COMBUSTION)
        if self._state['player']['buff_avail'][self._C._BUFF_POWER_INFUSION, next_hit] > 0:
            actions.add(self._C._CAST_POWER_INFUSION)
        if self._state['player']['buff_avail'][self._C._BUFF_MQG, next_hit] > 0:
            actions.add(self._C._CAST_MQG)

        return actions

    def _get_obs(self, next_hit):

        obs = []

        # boss debuffs - 5
        obs.append(self._state['boss']['ignite_timer']/(self._C._IGNITE_TIME + 0.0001))
        if self._state['boss']['ignite_timer'] > 0.0:
            obs.append(self._state['boss']['ignite_count']/self._C._IGNITE_STACK)
            obs.append(self._state['boss']['ignite_value']/5000.0)
        else:
            obs.append(0.0)
            obs.append(0.0)
        obs.append(self._state['boss']['scorch_timer']/self._C._SCORCH_TIME)
        if self._state['boss']['scorch_timer'] > 0.0:
            obs.append(self._state['boss']['scorch_count']/self._C._SCORCH_STACK)
        else:
            obs.append(0.0)
        
        #   casts - 2
        obs.append(self._state['player']['cast_number'][next_hit]/8.0)
        obs.append(self._state['player']['cast_number'][next_hit]/40.0)

        # self buffs - 6
        obs.append(self._state['player']['comb_avail'][next_hit])
        if self._state['player']['comb_avail'][next_hit] > 0:
            obs.append(0.0)
        else:
            obs.append(self._state['player']['comb_left'][next_hit]/3)
        for buff in range(self._numbufs[next_hit]):
            obs.append(self._state['player']['buff_avail'][buff, next_hit])
            if self._state['player']['buff_avail'][buff, next_hit] > 0:
                obs.append(0.0)
            else:
                timer = self._state['player']['buff_timer'][buff, next_hit]
                obs.append(timer/self._C._BUFF_DURATION[buff])
        obs = [max([0.0, min(a, 1.0)]) for a in obs]
        
        return np.array(obs)

    def _subtime(self, add_time):
        self._state['global']['running_time'] += add_time
        self._state['player']['cast_timer'] -= add_time
        self._state['player']['spell_timer'] -= add_time
        self._state['boss']['ignite_timer'] -= add_time
        self._state['boss']['tick_timer'] -= add_time
        self._state['boss']['scorch_timer'] -= add_time
        for buff in range(self._C._BUFFS):
            self._state['player']['buff_timer'][buff] -= add_time
        for debuff in range(self._C._DEBUFFS):
            self._state['boss']['debuff_timer'][debuff] -= add_time

        return

    def _do_cast(self, add_time):
        next_hit = np.argmin(self._state['player']['cast_timer'])
        self._subtime(add_time)

        if self._C._LOG_SIM:
            message = '         ({:6.2f}): player {:d} finished casting {:s}'
            message = message.format(self._state['global']['running_time'],
                                     next_hit + 1,
                                     self._C._LOG_SPELL[self._state['player']['cast_type'][next_hit]])
            self._log.append(message)

        # transfer to spell
        if self._state['player']['cast_type'][next_hit] < self._C._CAST_GCD:
            self._state['player']['spell_type'][next_hit] = self._state['player']['cast_type'][next_hit]
            self._state['player']['spell_timer'][next_hit] = self._C._SPELL_TIME[self._state['player']['cast_type'][next_hit]]

        # apply instant spells
        if self._state['player']['cast_type'][next_hit] == self._C._CAST_COMBUSTION:
            self._state['player']['comb_left'][next_hit] = self._C._COMBUSTIONS
            self._state['player']['comb_stack'][next_hit] = 0
            self._state['player']['comb_avail'][next_hit] -= 1

        for buff in range(self._C._BUFFS):
            if self._state['player']['cast_type'][next_hit] == self._C._BUFF_CAST_TYPE[buff]:
                self._state['player']['buff_timer'][buff, next_hit] = self._C._BUFF_DURATION[buff]
                self._state['player']['buff_avail'][buff, next_hit] -= 1
        
        # push gcd
        if self._state['player']['gcd'][next_hit] > 0.0:
            self._state['player']['cast_type'][next_hit] = self._C._CAST_GCD
            self._state['player']['cast_timer'][next_hit] = self._state['player']['gcd'][next_hit]
            self._state['player']['gcd'][next_hit] = 0.0
        else:
            self._state['global']['decision'] = True
            self._state['player']['cast_number'][next_hit] += 1 # attempt at batching

        return

    def _do_spell(self, add_time):
        epsilon = 1.0e-6
    
        next_hit = np.argmin(self._state['player']['spell_timer'])
        self._subtime(add_time)

        # reset timer
        self._state['player']['spell_timer'][next_hit] = self._C._LONG_TIME

        if self._C._LOG_SIM:
            message = ' ({:6.2f}): player {:d} {:s} landed '
            message = message.format(self._state['global']['running_time'],
                                     next_hit + 1,
                                     self._C._LOG_SPELL[self._state['player']['spell_type'][next_hit]])
            message2 = 'misses         '

        if np.random.rand() < self._state['player']['hit_chance'][next_hit]:
            spell_type = self._state['player']['spell_type'][next_hit]

            spell_damage = self._C._SPELL_BASE[spell_type] + \
                           self._C._SPELL_RANGE[spell_type]*np.random.rand() +\
                           self._C._SP_MULTIPLIER[spell_type]*self._state['player']['spell_power'][next_hit]
            # self._CoE + talents
            spell_damage *= self._C._COE_MULTIPLIER*self._C._DAMAGE_MULTIPLIER[spell_type] 
            scorch = self._C._IS_FIRE[spell_type]*self._C._SCORCH_MULTIPLIER*self._state['boss']['scorch_count']
            spell_damage *= 1.0 + scorch*(self._state['boss']['scorch_timer'] > 0.0).astype(np.float)
            pi = (self._state['player']['buff_timer'][self._C._BUFF_POWER_INFUSION, next_hit] > 0.0).astype(np.float)
            spell_damage *= 1.0 + self._C._POWER_INFUSION*pi
            spell_damage *= self._C._DMF_BUFF
            self._state['global']['damage'] += spell_damage
            # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

            # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MEself._CHANIself._CS **
            comb_crit = self._C._PER_COMBUSTION*self._state['player']['comb_stack'][next_hit]
            comb_crit *= (self._state['player']['comb_left'][next_hit] > 0).astype(np.float)
            comb_crit *= self._C._IS_FIRE[spell_type]
            crit_chance = self._state['player']['crit_chance'][next_hit] + comb_crit + self._C._INCIN_BONUS[spell_type]
            if np.random.rand() < crit_chance:
                if self._C._IS_FIRE[spell_type].astype(np.bool):
                    if self._C._LOG_SIM:
                        message2 = 'crits for {:4.0f} '.format((1.0 + self._C._ICRIT_DAMAGE)*spell_damage)
                    # remove ignite if expired
                    if self._state['boss']['ignite_timer'] <= 0.0:
                        self._state['boss']['ignite_count'] = 0
                        self._state['boss']['ignite_value'] = 0.0
            
                    # refresh ignite to full 4 seconds
                    self._state['boss']['ignite_timer'] = self._C._IGNITE_TIME + epsilon
            
                    # if we dont have a full stack
                    if self._state['boss']['ignite_count'] < self._C._IGNITE_STACK:
                        # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                        self._state['boss']['ignite_value'] += (1.0 + self._C._ICRIT_DAMAGE)*self._C._IGNITE_DAMAGE*spell_damage
                        self._state['boss']['ignite_multiplier'] = self._C._DMF_BUFF*(1.0 + self._C._POWER_INFUSION*pi)

                    # first in stack, set the tick
                    if not self._state['boss']['ignite_count']:
                        self._state['boss']['tick_timer'] = self._C._IGNITE_TICK

                    # increment to max of five (will do nothing if already at 5)
                    self._state['boss']['ignite_count'] = min([self._state['boss']['ignite_count'] + 1,
                                                               self._C._IGNITE_STACK])

                    # add crit to damage
                    self._state['global']['damage'] += self._C._ICRIT_DAMAGE*spell_damage
                    self._state['player']['damage'][next_hit].append((self._state['global']['running_time'],
                                                                      (self._C._ICRIT_DAMAGE + 1.0)*spell_damage))
            
                    # remove from combustion
                    self._state['player']['comb_left'][next_hit] = max([self._state['player']['comb_left'][next_hit] - 1, 0])
                else:
                    if self._C._LOG_SIM:
                        message2 = 'crits for {:4.0f} '.format((1.0 + self._C._CRIT_DAMAGE)*spell_damage)
                    self._state['global']['damage'] += self._C._CRIT_DAMAGE*spell_damage
                    self._state['player']['damage'][next_hit].append((self._state['global']['running_time'],
                                                                      (self._C._CRIT_DAMAGE + 1.0)*spell_damage))
            else:
                if self._C._LOG_SIM:
                    message2 = ' hits for {:4.0f} '.format(spell_damage)
                self._state['player']['damage'][next_hit].append((self._state['global']['running_time'],
                                                                  spell_damage))

            # scorch
            if self._state['boss']['scorch_timer'] <= 0.0:
                self._state['boss']['scorch_count'] = 0
            
            if self._C._IS_SCORCH[spell_type]:
                self._state['boss']['scorch_timer'] = self._C._SCORCH_TIME
                self._state['boss']['scorch_count'] = min([self._state['boss']['scorch_count'] + 1,
                                                           self._C._SCORCH_STACK])
                    
            if self._C._IS_FIRE[spell_type]:
                self._state['player']['comb_stack'][next_hit] += 1

        if self._C._LOG_SIM:
            dam_done = ' {:7.0f}'.format(self._state['global']['total_damage'] + self._state['global']['damage'])
            message = message + message2
            buffs = self._state['player']['buff_timer']
            is_mqg = 'msg' if buffs[self._C._BUFF_MQG, next_hit] > 0.0 else '   '
            is_pi =  'pi' if buffs[self._C._BUFF_POWER_INFUSION, next_hit] > 0.0 else '  '
            status = ' ic {:d} it {:4.2f} in {:s} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d} {:s} {:s}'
            ival = self._state['boss']['tick_timer']
            istat = '{:4.2f}'.format(ival) if ival > 0.0 and ival <= 2.0 else ' off'
            status = status.format(self._state['boss']['ignite_count'],
                                   max([self._state['boss']['ignite_timer'], 0.0]),
                                   istat,
                                   self._state['boss']['ignite_value'],
                                   self._state['boss']['scorch_count'],
                                   max([self._state['boss']['scorch_timer'], 0.0]),
                                   self._state['player']['comb_stack'][next_hit],
                                   self._state['player']['comb_left'][next_hit],
                                   is_mqg,
                                   is_pi)
            self._log.append(dam_done + message + status)

    def _do_tick(self, add_time):
        self._subtime(add_time)
        
        if self._state['boss']['ignite_timer'] <= 0.0:
            self._state['boss']['tick_timer'] = self._C._LONG_TIME

        else:
            self._state['boss']['tick_timer'] = self._C._IGNITE_TICK

            scorch = self._C._SCORCH_MULTIPLIER*self._state['boss']['scorch_count']
            multiplier = self._C._COE_MULTIPLIER*self._state['boss']['ignite_multiplier']
            multiplier *= 1.0 + scorch*float(self._state['boss']['scorch_timer'] > 0.0)
            self._state['global']['damage'] += multiplier*self._state['boss']['ignite_value']
            self._state['boss']['ignite_damage'].append((self._state['global']['running_time'],
                                                         multiplier*self._state['boss']['ignite_value']))
            if self._C._LOG_SIM:
                message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                self._log.append(message.format(self._state['global']['total_damage'] + self._state['global']['damage'],
                                                self._state['global']['running_time'],
                                                multiplier*self._state['boss']['ignite_value']))
        return

    def _advance(self):
        self._state['global']['damage'] = 0.0

        if self._state['global']['running_time'] >= self._state['global']['duration'] or\
           self._state['global']['decision']:
            return False

        # cast finished
        cast_timer = np.min(self._state['player']['cast_timer'])
        spell_timer = np.min(self._state['player']['spell_timer'])
        tick_timer = self._state['boss']['tick_timer']
        if cast_timer < spell_timer and cast_timer < tick_timer:
            self._do_cast(cast_timer)
        elif spell_timer < tick_timer:
            self._do_spell(spell_timer)
        else:
            self._do_tick(tick_timer)
    
        return True

    def _apply_decision(self, cast_type, next_hit):
        if cast_type not in self._get_actions(next_hit):
            react_time = 0.0
            self._state['player']['cast_type'][next_hit] = self._C._CAST_GCD
            self._state['player']['cast_timer'][next_hit] = self._C._CAST_TIME[self._C._CAST_GCD]
        else:
            react_time = np.abs(self._config['react_time']*np.random.randn())
            self._state['player']['cast_timer'][next_hit] = react_time 
            self._state['player']['cast_type'][next_hit] = cast_type
            if cast_type < self._C._CAST_GCD:
                self._state['player']['cast_timer'][next_hit] += self._C._CAST_TIME[cast_type]
                if self._state['player']['buff_timer'][self._C._BUFF_MQG, next_hit] > 0.0:
                    self._state['player']['cast_timer'][next_hit] /= 1.0 + self._C._MQG
                self._state['player']['gcd'][next_hit] = np.max([0.0, self._C._GLOBAL_COOLDOWN + react_time - self._state['player']['cast_timer'][next_hit]])

        if self._C._LOG_SIM:
            message = '         ({:6.2f}): player {:d} started  casting {:s}'
            message = message.format(self._state['global']['running_time'] + react_time,
                                     next_hit + 1,
                                     self._C._LOG_SPELL[cast_type])
            self._log.append(message)
                
        self._state['global']['decision'] = False

        return

    def act_space(self, atype):
        remove = 0
        if atype == "none":
            remove = 2
        elif atype == "mqg":
            remove = 1

        return spaces.Discrete(self._C._CASTS - remove)

    def obs_space(self, atype):
        remove = 0
        if atype == "none":
            remove = 4
        elif atype == "mqg":
            remove = 2
        obs = 13 - remove
            
        return spaces.Box(0.0, 1.0, shape=(obs,), dtype=np.float32)
