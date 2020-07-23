import numpy as np
import constants
from decisions import Decider

class Encounter():

    def __init__(self, array_generator, rotation, response, config, is_mc):
        self._array_generator = array_generator
        self._rotation = rotation
        self._response = response
        self._config = config
        self._is_mc = is_mc

    def _subtime(self, sub, add_time):
        C = self._C
        running_time = self._arrays['global']['running_time']
        player = self._arrays['player']
        boss = self._arrays['boss']

        running_time[sub] += add_time
        player['cast_timer'][sub, :] -= add_time[:, None]
        player['spell_timer'][sub, :] -= add_time[:, None]
        boss['ignite_timer'][sub] -= add_time
        boss['tick_timer'][sub] -= add_time
        boss['scorch_timer'][sub] -= add_time
        for buff in range(C._BUFFS):
            player['buff_timer'][buff][sub, :] -= add_time[:, None]
        for debuff in range(C._DEBUFFS):
            boss['debuff_timer'][debuff][sub] -= add_time

    def _do_cast(self, still_going, cast_array):
        C = self._C
        player = self._arrays['player']
        
        cast_ends = np.where(cast_array)[0]
        if cast_ends.size > 0:
            cst = still_going[cast_ends]
            next_hit = np.argmin(player['cast_timer'][cst, :], axis=1)
            add_time = np.min(player['cast_timer'][cst, :], axis=1)
            self._subtime(cst, add_time)

            if C._LOG_SIM >= 0:
                if C._LOG_SIM in cst:
                    message = '         ({:6.2f}): player {:d} finished casting {:s}'
                    sub_index = cst.tolist().index( C._LOG_SIM)
                    message = message.format(self._arrays['global']['running_time'][C._LOG_SIM],
                                             next_hit[sub_index] + 1,
                                             C._LOG_SPELL[player['cast_type'][cst[sub_index], next_hit[sub_index]]])
                    print(message)

            # transfer to spell
            instant_array = player['cast_type'][cst, next_hit] >= C._CAST_GCD
            no_instant = np.where(np.logical_not(instant_array))[0]
            player['spell_type'][cst[no_instant], next_hit[no_instant]] = player['cast_type'][cst[no_instant], next_hit[no_instant]]
            player['spell_timer'][cst[no_instant], next_hit[no_instant]] = C._SPELL_TIME[player['cast_type'][cst[no_instant], next_hit[no_instant]]]

            # apply instant spells
            combustion = np.where(player['cast_type'][cst, next_hit] == C._CAST_COMBUSTION)[0]
            player['comb_left'][cst[combustion], next_hit[combustion]] = C._COMBUSTIONS
            player['comb_stack'][cst[combustion], next_hit[combustion]] = 1
            player['comb_avail'][cst[combustion], next_hit[combustion]] -= 1

            for buff in range(C._BUFFS):
                tbuff = np.where(player['cast_type'][cst, next_hit] == C._BUFF_CAST_TYPE[buff])[0]
                player['buff_timer'][buff][cst[tbuff], next_hit[tbuff]] = C._BUFF_DURATION[buff]
                player['buff_avail'][buff][cst[tbuff], next_hit[tbuff]] -= 1

            # determine gcd        
            gcd_array = player['gcd'][cst, next_hit] > 0.0
            yes_gcd = np.where(gcd_array)[0]
            no_gcd = np.where(np.logical_not(gcd_array))[0]
        
            # push gcd
            player['cast_type'][cst[yes_gcd], next_hit[yes_gcd]] = C._CAST_GCD
            player['cast_timer'][cst[yes_gcd], next_hit[yes_gcd]] =\
                 player['gcd'][cst[yes_gcd], next_hit[yes_gcd]]
            player['gcd'][cst[yes_gcd], next_hit[yes_gcd]] = 0.0

            # inc cast number
            self._arrays['global']['decision'][cst[no_gcd]] = True
            player['cast_number'][cst[no_gcd], next_hit[no_gcd]] += 1 # attempt at batching

    def _do_spell(self, still_going, spell_array):
        C = self._C
        player = self._arrays['player']
        boss = self._arrays['boss']

        epsilon = 1.0e-6
    
        spell_lands = np.where(spell_array)[0]
        if spell_lands.size > 0:
            spl = still_going[spell_lands]
            lnext_hit = np.argmin(player['spell_timer'][spl, :], axis=1)
            add_time = np.min(player['spell_timer'][spl, :], axis=1)
            self._subtime(spl, add_time)

            # reset timer
            player['spell_timer'][spl, lnext_hit] = C._LONG_TIME

            if C._LOG_SIM >= 0:
                if C._LOG_SIM in spl:
                    message = ' ({:6.2f}): player {:d} {:s} landed '
                    sub_index = spl.tolist().index( C._LOG_SIM)
                    message = message.format(self._arrays['global']['running_time'][C._LOG_SIM],
                                             lnext_hit[sub_index] + 1,
                                             C._LOG_SPELL[player['spell_type'][C._LOG_SIM, lnext_hit[sub_index]]])
                    message2 = 'misses         '

            spell_hits = np.where(np.random.rand(spell_lands.size) < player['hit_chance'][spl, lnext_hit])[0]
            if spell_hits.size > 0:

                sph = spl[spell_hits]
                next_hit = lnext_hit[spell_hits]
                spell_type = player['spell_type'][sph, next_hit]

                spell_damage = C._SPELL_BASE[spell_type] + \
                               C._SPELL_RANGE[spell_type]*np.random.rand(sph.size) +\
                               C._SP_MULTIPLIER[spell_type]*player['spell_power'][sph, next_hit]
                spell_damage *= C._COE_MULTIPLIER*C._DAMAGE_MULTIPLIER[spell_type] # CoE + talents
                scorch = C._IS_FIRE[spell_type]*C._SCORCH_MULTIPLIER*boss['scorch_count'][sph]
                spell_damage *= 1.0 + scorch*(boss['scorch_timer'][sph] > 0.0).astype(np.float)
                pi = (player['buff_timer'][C._BUFF_POWER_INFUSION][sph, next_hit] > 0.0).astype(np.float)
                spell_damage *= 1.0 + C._POWER_INFUSION*pi
                spell_damage *= C._DMF_BUFF
                self._damage[sph] += spell_damage
                # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

                # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MECHANICS **
                comb_crit = C._PER_COMBUSTION*player['comb_stack'][sph, next_hit] - C._IS_SCORCH[spell_type] # scorch and batching
                comb_crit *= (player['comb_left'][sph, next_hit] > 0).astype(np.float)
                comb_crit *= C._IS_FIRE[spell_type]
                
                crit_chance = player['crit_chance'][sph, next_hit] + comb_crit + C._INCIN_BONUS[spell_type]
                crit_array = np.random.rand(sph.size) < crit_chance
                
                ignite_array = crit_array & C._IS_FIRE[spell_type].astype(np.bool)
                lcl_icrits = np.where(ignite_array)[0]
                gbl_icrits = sph[lcl_icrits]
                inext_hit = next_hit[lcl_icrits]
            
                # remove ignite if expired
                rem_val = np.where(boss['ignite_timer'][gbl_icrits] <= 0.0)[0]
                boss['ignite_count'][gbl_icrits[rem_val]] = 0
                boss['ignite_value'][gbl_icrits[rem_val]] = 0.0
            
                # refresh ignite to full 4 seconds
                boss['ignite_timer'][gbl_icrits] = C._IGNITE_TIME + epsilon
            
                # if we dont have a full stack
                mod_val = np.where(boss['ignite_count'][gbl_icrits] < C._IGNITE_STACK)[0]
                # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                boss['ignite_value'][gbl_icrits[mod_val]] += (1.0 + C._ICRIT_DAMAGE)*C._IGNITE_DAMAGE*spell_damage[lcl_icrits[mod_val]]

                # first in stack, set the tick
                mod_val2 = np.where(boss['ignite_count'][gbl_icrits] == 0)[0]
                boss['tick_timer'][gbl_icrits[mod_val2]] = C._IGNITE_TICK
                boss['ignite_multiplier'][gbl_icrits[mod_val2]] = C._DMF_BUFF*(1.0 + C._POWER_INFUSION*pi[lcl_icrits[mod_val2]])

                # increment to max of five (will do nothing if already at 5)
                boss['ignite_count'][gbl_icrits] = np.minimum(boss['ignite_count'][gbl_icrits] + 1, C._IGNITE_STACK)

                # add crit to damage
                self._damage[gbl_icrits] += C._ICRIT_DAMAGE*spell_damage[lcl_icrits]
            
                # remove from combustion
                player['comb_left'][gbl_icrits, inext_hit] = np.maximum(player['comb_left'][gbl_icrits, inext_hit] - 1, 0)

                # normal crit
                lcl_crits = np.where(crit_array & np.logical_not(C._IS_FIRE[spell_type]))[0]
                self._damage[sph[lcl_crits]] += C._CRIT_DAMAGE*spell_damage[lcl_crits]

                if C._LOG_SIM >= 0:
                    if C._LOG_SIM in sph:
                        sub_index = sph.tolist().index(C._LOG_SIM)
                        if  sub_index in lcl_crits:
                            message2 = 'crits for {:4.0f} '.format((1.0 + C._CRIT_DAMAGE)*spell_damage[sub_index])
                        elif sub_index in lcl_icrits:
                            message2 = 'crits for {:4.0f} '.format((1.0 + C._ICRIT_DAMAGE)*spell_damage[sub_index])
                        else:
                            message2 = ' hits for {:4.0f} '.format(spell_damage[sub_index])

                # scorch
                scorch_out = sph[np.where(boss['scorch_timer'][sph] <= 0.0)[0]]
                boss['scorch_count'][scorch_out] = 0
            
                scorch_list = np.where(C._IS_SCORCH[spell_type])[0]
                if scorch_list.size:
                    is_scorch = sph[scorch_list]
                    snext_hit = next_hit[scorch_list]
                    shit = np.where(np.random.rand(is_scorch.size) < player['hit_chance'][is_scorch, snext_hit])[0]
                    boss['scorch_timer'][is_scorch[shit]] = C._SCORCH_TIME
                    boss['scorch_count'][is_scorch[shit]] = np.minimum(boss['scorch_count'][is_scorch[shit]] + 1, C._SCORCH_STACK)
                    
                fire = np.where(C._IS_FIRE[spell_type])[0]
                player['comb_stack'][sph[fire], next_hit[fire]] += 1

            if C._LOG_SIM >= 0:
                if C._LOG_SIM in spl:
                    sub_index = spl.tolist().index(C._LOG_SIM)
                    dam_done = ' {:7.0f}'.format(self._arrays['global']['total_damage'][C._LOG_SIM] + self._damage[C._LOG_SIM])
                    message = message + message2
                    buffs = player['buff_timer']
                    is_mqg = 'msg' if buffs[C._BUFF_MQG][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '   '
                    is_pi =  'pi' if buffs[C._BUFF_POWER_INFUSION][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '  '
                    status = ' ic {:d} it {:4.2f} in {:s} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d} {:s} {:s}'
                    ival = boss['tick_timer'][C._LOG_SIM]
                    istat = '{:4.2f}'.format(ival) if ival > 0.0 and ival <= 2.0 else ' off'
                    status = status.format(boss['ignite_count'][C._LOG_SIM],
                                           max([boss['ignite_timer'][C._LOG_SIM], 0.0]),
                                           istat,
                                           boss['ignite_value'][C._LOG_SIM],
                                           boss['scorch_count'][C._LOG_SIM],
                                           max([boss['scorch_timer'][C._LOG_SIM], 0.0]),
                                           player['comb_stack'][C._LOG_SIM, lnext_hit[sub_index]],
                                           player['comb_left'][C._LOG_SIM, lnext_hit[sub_index]],
                                           is_mqg,
                                           is_pi)
                    print(dam_done + message + status)

    def _do_tick(self, still_going, tick_array):
        C = self._C
        boss = self._arrays['boss']

        tick_hits = np.where(tick_array)[0]
        if tick_hits.size > 0:
            tic = still_going[tick_hits]
            add_time = boss['tick_timer'][tic]
            self._subtime(tic, add_time)
        
            ignite_expire = boss['ignite_timer'][tic] <= 0.0
            yes_expire = tic[np.where(ignite_expire)[0]]
            boss['tick_timer'][yes_expire] = C._LONG_TIME
            
            no_expire = tic[np.where(np.logical_not(ignite_expire))[0]]
            boss['tick_timer'][no_expire] = C._IGNITE_TICK

            scorch = C._SCORCH_MULTIPLIER*boss['scorch_count'][no_expire]
            multiplier = C._COE_MULTIPLIER*boss['ignite_multiplier'][no_expire]
            multiplier *= 1.0 + scorch*(boss['scorch_timer'][no_expire] > 0.0).astype(np.float)
            self._damage[no_expire] += multiplier*boss['ignite_value'][no_expire]
            if self._is_mc:
                self._ignite[no_expire] += multiplier*boss['ignite_value'][no_expire]
            if C._LOG_SIM >= 0:
                if C._LOG_SIM in no_expire:
                    sub_index = no_expire.tolist().index(C._LOG_SIM)
                    message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                    print(message.format(self._arrays['global']['total_damage'][C._LOG_SIM] + self._damage[C._LOG_SIM],
                                         self._arrays['global']['running_time'][C._LOG_SIM],
                                         multiplier[sub_index]*boss['ignite_value'][C._LOG_SIM]))

    def _advance(self):
        going_array = (self._arrays['global']['running_time'] < self._arrays['global']['duration'])
        going_array &= np.logical_not(self._arrays['global']['decision'])
        still_going = np.where(going_array)[0]
        if still_going.size == 0:
            return False

        # cast finished
        cast_timer = np.copy(np.min(self._arrays['player']['cast_timer'][still_going, :], axis=1))
        spell_timer = np.copy(np.min(self._arrays['player']['spell_timer'][still_going, :], axis=1))
        tick_timer = np.copy(self._arrays['boss']['tick_timer'][still_going])
        cast_array = (cast_timer < spell_timer) & (cast_timer < tick_timer)
        self._do_cast(still_going, cast_array)

        # spell hits
        spell_array = np.logical_not(cast_array) & (spell_timer < tick_timer)
        self._do_spell(still_going, spell_array)

        tick_array = np.logical_not(cast_array | spell_array)
        self._do_tick(still_going, tick_array)
    
        return True
    
    def _apply_decisions(self, still_going, decisions, next_hit):
        C = self._C
        player = self._arrays['player']

        react_time = np.abs(self._response*np.random.randn(still_going.size))    

        player['cast_timer'][still_going, next_hit] = react_time
        player['cast_type'][still_going, next_hit] = decisions

        # spell is a fixed wait time
        wait = np.where(decisions == C._CAST_GCD)[0]
        player['cast_timer'][still_going[wait], next_hit[wait]] = C._CAST_TIME[C._CAST_GCD]
        
        # spell on global cooldown
        on_gcd = np.where(decisions < C._CAST_GCD)[0]
        player['cast_timer'][still_going[on_gcd], next_hit[on_gcd]] += C._CAST_TIME[decisions[on_gcd]]
        # mind quickening gem
        mqg = (player['buff_timer'][C._BUFF_MQG][still_going[on_gcd], next_hit[on_gcd]] > 0.0).astype(np.float)
        player['cast_timer'][still_going[on_gcd], next_hit[on_gcd]] /= (1.0 + C._MQG*mqg)
    
        player['gcd'][still_going[on_gcd], next_hit[on_gcd]] = np.maximum(0.0, C._GLOBAL_COOLDOWN + react_time[on_gcd] - player['cast_timer'][still_going[on_gcd], next_hit[on_gcd]])

        if C._LOG_SIM >= 0:
            if C._LOG_SIM in still_going:
                message = '         ({:6.2f}): player {:d} started  casting {:s}'
                sub_index = still_going.tolist().index(C._LOG_SIM)
                message = message.format(self._arrays['global']['running_time'][C._LOG_SIM] + react_time[sub_index],
                                         next_hit[sub_index] + 1,
                                         C._LOG_SPELL[player['cast_type'][still_going[sub_index], next_hit[sub_index]]])
                print(message)
        self._arrays['global']['decision'] = np.zeros(self._arrays['global']['decision'].shape, dtype=np.bool)
    
    def run(self):
        C = constants.Constant()
        self._C = C
        self._arrays = self._array_generator.run(C)

        decider = Decider(C,
                          self._rotation,
                          self._arrays['player']['cast_number'].shape,
                          self._config)
        
        # prep for first player to "move"
        first_act = np.min(self._arrays['player']['cast_timer'], axis=1)
        self._arrays['global']['duration'] += first_act
        self._arrays['player']['cast_timer'] -= first_act[:, None]
        next_hit = np.argmin(self._arrays['player']['cast_timer'], axis=1)
        self._arrays['player']['cast_number'][np.arange(self._arrays['player']['cast_timer'].shape[0]), next_hit] += 1

        if C._LOG_SIM >= 0:
            constants.log_message()
        still_going = np.arange(self._arrays['global']['running_time'].size)
        while True:
            self._damage = np.zeros(self._arrays['global']['total_damage'].size)
            if self._is_mc:
                self._ignite = np.zeros(self._arrays['global']['total_damage'].size)
            decisions, next_hit = decider.get_decisions(self._arrays, still_going)
            self._apply_decisions(still_going, decisions, next_hit)
            while self._advance():
                still_going = np.where(self._arrays['global']['running_time'] < self._arrays['global']['duration'])[0]
            self._arrays['global']['total_damage'][still_going] += self._damage[still_going]
            if self._is_mc:
                self._arrays['global']['ignite'][still_going] += self._ignite[still_going]
            if not still_going.size:
                break
        
        if C._LOG_SIM >= 0:
            print('total log damage = {:7.0f}'.format(self._arrays['global']['total_damage'][C._LOG_SIM]))
            print('average damage = {:9.1f}'.format(self._arrays['global']['total_damage'].mean()))
            print('std damage = {:7.1f}'.format(self._arrays['global']['total_damage'].std()))
            if self._is_mc:
                print('ignite damage = {:9.1f}'.format(self._arrays['global']['ignite'].mean()))

        dp_mage = self._arrays['global']['total_damage']/self._arrays['global']['duration']

        total_dps = dp_mage.mean()
        if self._is_mc:
        #if True:
            ip_mage = self._arrays['global']['ignite']/self._arrays['global']['duration']
            #pmage = np.concatenate([total_dps, ip_mage], axis=1)
            #spage = np.sort(pmage, axis=0)
            #print(spage[8990:9010, :])
            return total_dps, ip_mage.mean()
        else:
            return total_dps
                

def get_damage(params):
    array_generator = constants.ArrayGenerator(params)
    encounter = Encounter(array_generator,
                          params['rotation'],
                          params['timing']['response'],
                          params['configuration'],
                          params['mc'])
    return encounter.run()

