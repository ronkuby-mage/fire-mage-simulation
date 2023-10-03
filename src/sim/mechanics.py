import numpy as np
from . import constants
from .decisions import Decider

class Encounter():

    def __init__(self, array_generator, rotation, response, var, config, world_buffs, boss_buffs, run_params):
        self._array_generator = array_generator
        self._rotation = rotation
        self._response = response
        self._var = var
        self._config = config
        self._world_buffs = world_buffs
        self._boss_buffs = boss_buffs
        self._run_params = run_params

    def _subtime(self, sub, add_time):
        C = self._C
        running_time = self._arrays['global']['running_time']
        player = self._arrays['player']
        boss = self._arrays['boss']

        running_time[sub] += add_time
        player['cast_timer'][sub, :] -= add_time[:, None]
        player['spell_timer'][sub, :] -= add_time[:, None]
        player['comb_cooldown'][sub, :] -= add_time[:, None]
        player['fb_cooldown'][sub, :] -= add_time[:, None]
        boss['ignite_timer'][sub] -= add_time
        boss['tick_timer'][sub] -= add_time
        boss['scorch_timer'][sub] -= add_time
        for buff in range(C._BUFFS):
            player['buff_timer'][buff][sub, :] -= add_time[:, None]
            player['buff_cooldown'][buff][sub, :] -= add_time[:, None]
        for debuff in range(C._DEBUFFS):
            boss['debuff_timer'][debuff][sub] -= add_time
        boss['spell_vulnerability'][sub] -= add_time
        player['nightfall'][sub, :] -= add_time[:, None]

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
            
            fire_blast = np.where(player['cast_type'][cst, next_hit] == C._CAST_FIRE_BLAST)[0]
            player['fb_cooldown'][cst[fire_blast], next_hit[fire_blast]] = C._FIRE_BLAST_COOLDOWN

            # apply instant spells
            combustion = np.where(player['cast_type'][cst, next_hit] == C._CAST_COMBUSTION)[0]
            player['comb_left'][cst[combustion], next_hit[combustion]] = C._COMBUSTIONS
            player['comb_stack'][cst[combustion], next_hit[combustion]] = 1
            player['comb_avail'][cst[combustion], next_hit[combustion]] -= 1
            player['comb_cooldown'][cst[combustion], next_hit[combustion]] = np.inf # temporary

            for buff in range(C._BUFFS):
                tbuff = np.where(player['cast_type'][cst, next_hit] == C._BUFF_CAST_TYPE[buff])[0]
                player['buff_timer'][buff][cst[tbuff], next_hit[tbuff]] = C._BUFF_DURATION[buff]
                #player['buff_avail'][buff][cst[tbuff], next_hit[tbuff]] -= 1
                player['buff_cooldown'][buff][cst[tbuff], next_hit[tbuff]] = C._BUFF_COOLDOWN[buff]
                if buff < C._DAMAGE_BUFFS:
                    player['buff_ticks'][buff][cst[tbuff], next_hit[tbuff]] = 0
                # internal cooldown (MQG too)
                if buff < C._DAMAGE_BUFFS + 1:
                    for buff2 in range(C._DAMAGE_BUFFS + 1):
                        if buff2 == buff:
                            continue
                        player['buff_cooldown'][buff2][cst[tbuff], next_hit[tbuff]] =\
                            np.maximum(player['buff_cooldown'][buff2][cst[tbuff], next_hit[tbuff]], C._BUFF_DURATION[buff])

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

                #print(self._arrays['player']['cleaner'], self._arrays['player']['cleaner'].shape)
                the_cleaner = np.any(np.equal(next_hit.reshape(next_hit.size, 1), self._arrays['player']['cleaner']), axis=1)
                #the_cleaner = (next_hit == self._arrays['player']['cast_number'].shape[1] - 1) | (next_hit == 1)
                if not self._all:
                    the_player = np.any(np.equal(next_hit.reshape(next_hit.size, 1), self._arrays['player']['target']), axis=1)
                    is_play = np.where(the_player)[0]
                is_clean = np.where(the_cleaner)[0]
                not_clean = np.where(np.logical_not(the_cleaner))[0]
                
                is_dragonling = np.logical_and(self._arrays['global']['running_time'][sph] >= boss['dragonling'],
                                               self._arrays['global']['running_time'][sph] < boss['dragonling'] + C._DRAGONLING_DURATION).astype(np.float32)
                buff_damage = C._DRAGONLING_BUFF*is_dragonling
                for buff in range(C._DAMAGE_BUFFS):
                    active = (player['buff_timer'][buff][sph, next_hit] > 0.0).astype(np.float32)
                    ticks = player['buff_ticks'][buff][sph, next_hit]
                    buff_damage += active*(C._BUFF_DAMAGE[buff] + ticks*C._BUFF_PER_TICK[buff])
                    player['buff_ticks'][buff][sph, next_hit] += 1
                    
                spell_damage = C._SPELL_BASE[spell_type] + \
                               C._SPELL_RANGE[spell_type]*np.random.rand(sph.size) +\
                               C._SP_MULTIPLIER[spell_type]*(player['spell_power'][sph, next_hit] + buff_damage)
                rolls = np.random.rand(sph.size)
                conditions = [np.logical_and(rolls >= ll, rolls < ul) for ll, ul in zip(C._RES_THRESH, C._RES_THRESH_UL)]
                partials = np.piecewise(rolls, conditions, C._RES_AMOUNT)
                partials[np.logical_not(C._IS_FIRE[spell_type].astype(bool))] = 1.0
                spell_damage *= partials

                spell_damage *= C._COE_MULTIPLIER*C._DAMAGE_MULTIPLIER[spell_type] # CoE + talents
                scorch = C._IS_FIRE[spell_type]*C._SCORCH_MULTIPLIER*boss['scorch_count'][sph]
                spell_damage *= 1.0 + scorch*(boss['scorch_timer'][sph] > 0.0).astype(np.float32)
                pi = (player['buff_timer'][C._BUFF_POWER_INFUSION][sph, next_hit] > 0.0).astype(np.float32)
                spell_damage *= 1.0 + C._POWER_INFUSION*pi
                spell_damage *= 1.0 + C._NIGHTFALL_BUFF*(boss["spell_vulnerability"][sph] > 0.0).astype(np.float32)
                
                spell_damage[not_clean] *= C._NORMAL_BUFF
                spell_damage[is_clean] *= C._NORMAL_BUFF_C
                self._damage[sph] += spell_damage
                if not self._all:
                    self._player[sph[is_play]] += spell_damage[is_play]
                # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

                # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MECHANICS **
                comb_crit = C._PER_COMBUSTION*player['comb_stack'][sph, next_hit] - C._IS_SCORCH[spell_type] # scorch and batching
                comb_crit *= (player['comb_left'][sph, next_hit] > 0).astype(np.float32)
                comb_crit *= C._IS_FIRE[spell_type]
                
                crit_chance = player['crit_chance'][sph, next_hit] + comb_crit + C._INCIN_BONUS[spell_type]
                crit_array = np.random.rand(sph.size) < crit_chance
                
                ignite_array = crit_array & C._IS_FIRE[spell_type].astype(bool)

                lcrit_clean = np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_cleaner)[0]
                lnot_crit_clean = np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & np.logical_not(the_cleaner))[0]
                gcrit_clean = sph[np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_cleaner)[0]]
                gnot_crit_clean = sph[np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & np.logical_not(the_cleaner))[0]]

                lcl_icrits = np.where(ignite_array)[0]
                gbl_icrits = sph[lcl_icrits]
                inext_hit = next_hit[lcl_icrits]
            
                # remove ignite if expired
                rem_val = np.where(boss['ignite_timer'][gbl_icrits] <= 0.0)[0]
                boss['ignite_count'][gbl_icrits[rem_val]] = 0
                boss['ignite_value'][gbl_icrits[rem_val]] = 0.0

                # record late crits
                rem_val = np.where(boss['ignite_timer'][gbl_icrits] < C._DECISION_POINT)[0]
                player['crit_too_late'][gbl_icrits[rem_val], :] = True

                # extend by 4 secs, reset timer if no more ticks (31MAR22)
                # comment this section and uncomment next section to return to classic mechanics
                new_tick = np.where((boss['tick_timer'][gbl_icrits] > C._IGNITE_TICK) & (boss['ignite_count'][gbl_icrits] > 0))[0]
                boss['tick_timer'][gbl_icrits[new_tick]] = C._IGNITE_TICK
                boss['ignite_timer'][gbl_icrits] = C._IGNITE_TIME + epsilon

                # add tick if 1 tick remaining
                # comment this section and uncomment next section to return to TBC mechanics
                #new_tick = np.where(boss['ignite_timer'][gbl_icrits] <= C._IGNITE_TICK)[0]
                #boss['ignite_timer'][gbl_icrits[new_tick]] += C._IGNITE_TICK

                ## refresh ignite to full 4 seconds
                #boss['ignite_timer'][gbl_icrits] = C._IGNITE_TIME + epsilon

                # if we dont have a full stack
                mod_val = np.where(boss['ignite_count'][gnot_crit_clean] < C._IGNITE_STACK)[0]
                # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                boss['ignite_value'][gnot_crit_clean[mod_val]] += (1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF*C._IGNITE_DAMAGE*spell_damage[lnot_crit_clean[mod_val]]
                mod_val = np.where(boss['ignite_count'][gcrit_clean] < C._IGNITE_STACK)[0]
                # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                boss['ignite_value'][gcrit_clean[mod_val]] += (1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF_C*C._IGNITE_DAMAGE*spell_damage[lcrit_clean[mod_val]]

                # first in stack, set the tick
                mod_val2 = np.where(boss['ignite_count'][gnot_crit_clean] == 0)[0]
                boss['tick_timer'][gnot_crit_clean[mod_val2]] = C._IGNITE_TICK
                # comment the next line to return to TBC ignite mechanics
                boss['ignite_timer'][gnot_crit_clean[mod_val2]] = C._IGNITE_TIME + epsilon
                boss['ignite_multiplier'][gnot_crit_clean[mod_val2]] = C._IGNITE_BUFF*(1.0 + C._POWER_INFUSION*pi[lnot_crit_clean[mod_val2]])
                mod_val2 = np.where(boss['ignite_count'][gcrit_clean] == 0)[0]
                boss['tick_timer'][gcrit_clean[mod_val2]] = C._IGNITE_TICK
                # comment the next line to return to TBC ignite mechanics
                boss['ignite_timer'][gcrit_clean[mod_val2]] = C._IGNITE_TIME + epsilon
                boss['ignite_multiplier'][gcrit_clean[mod_val2]] = C._IGNITE_BUFF_C*(1.0 + C._POWER_INFUSION*pi[lcrit_clean[mod_val2]])


                # increment to max of five (will do nothing if already at 5)
                boss['ignite_count'][gbl_icrits] = np.minimum(boss['ignite_count'][gbl_icrits] + 1, C._IGNITE_STACK)

                # add crit to damage
                self._damage[gbl_icrits] -= spell_damage[lcl_icrits]
                self._damage[gnot_crit_clean] += spell_damage[lnot_crit_clean]*(1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF
                self._damage[gcrit_clean] += spell_damage[lcrit_clean]*(1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF_C
                if not self._all:
                    lcrit_play = np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player)[0]
                    gcrit_play = sph[np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player)[0]]

                    lcrit_play_notclean = np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player & np.logical_not(the_cleaner))[0]
                    gcrit_play_notclean = sph[np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player & np.logical_not(the_cleaner))[0]]
                    lcrit_play_clean = np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player & the_cleaner)[0]
                    gcrit_play_clean = sph[np.where(crit_array & C._IS_FIRE[spell_type].astype(bool) & the_player & the_cleaner)[0]]

                    self._player[gcrit_play] -= spell_damage[lcrit_play]
                    self._player[gcrit_play_notclean] += spell_damage[lcrit_play_notclean]*(1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF
                    self._player[gcrit_play_clean] += spell_damage[lcrit_play_clean]*(1.0 + C._ICRIT_DAMAGE)*C._CRIT_BUFF_C
               
                self._crit[gbl_icrits] += (1.0 + C._ICRIT_DAMAGE)*spell_damage[lcl_icrits]

                # check last combustion
                comb_off = np.where(player['comb_left'][gbl_icrits, inext_hit] == 1)[0]
                player['comb_cooldown'][gbl_icrits[comb_off], inext_hit[comb_off]] = C._COMBUSTION_COOLDOWN

                # remove from combustion
                player['comb_left'][gbl_icrits, inext_hit] = np.maximum(player['comb_left'][gbl_icrits, inext_hit] - 1, 0)

                # normal crit
                lcl_crits = np.where(crit_array & np.logical_not(C._IS_FIRE[spell_type]))[0]
                self._damage[sph[lcl_crits]] += C._CRIT_DAMAGE*spell_damage[lcl_crits]
                if not self._all:
                    lcrit_play_nf = np.where(crit_array & np.logical_not(C._IS_FIRE[spell_type].astype(bool)) & the_player)[0]
                    gcrit_play_nf = sph[np.where(crit_array & np.logical_not(C._IS_FIRE[spell_type].astype(bool)) & the_player)[0]]
                    self._player[gcrit_play_nf] += C._CRIT_DAMAGE*spell_damage[lcrit_play_nf]

                if C._LOG_SIM >= 0:
                    if C._LOG_SIM in sph:
                        sub_index = sph.tolist().index(C._LOG_SIM)
                        if  sub_index in lcl_crits:
                            message2 = 'crits for {:5.0f} '.format((1.0 + C._CRIT_DAMAGE)*spell_damage[sub_index])
                        elif sub_index in lcl_icrits:
                            message2 = 'crits for {:5.0f} '.format((1.0 + C._ICRIT_DAMAGE)*spell_damage[sub_index])
                        else:
                            message2 = ' hits for {:5.0f} '.format(spell_damage[sub_index])

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
                    is_sapp = 'sap' if buffs[C._BUFF_SAPP][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '   '
                    is_toep = 'toep' if buffs[C._BUFF_TOEP][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '   '
                    is_zhc = 'zhc' if buffs[C._BUFF_ZHC][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '   '
                    is_mqg = 'mqg' if buffs[C._BUFF_MQG][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '   '
                    is_pi =  'pi' if buffs[C._BUFF_POWER_INFUSION][C._LOG_SIM, lnext_hit[sub_index]] > 0.0 else '  '
                    status = ' ic {:d} it {:4.2f} in {:s} id {:5.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d} {:s} {:s} {:s} {:s} {:s}'
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
                                           is_sapp,
                                           is_toep,
                                           is_zhc,
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
            no_expire = tic[np.where(np.logical_not(ignite_expire))[0]]

            # new ignite mechanics (31MAR22) comment this section and uncomment block below to revert
            refresh_array = boss['ignite_timer'][tic] >= 2.0
            new_ignite = tic[np.where(refresh_array)[0]]
            no_ignite = tic[np.where(np.logical_not(refresh_array))[0]]
            boss['tick_timer'][new_ignite] = C._IGNITE_TICK
            boss['tick_timer'][no_ignite] = C._LONG_TIME

            ## uncomment to revert
            #yes_expire = tic[np.where(ignite_expire)[0]]
            #boss['tick_timer'][yes_expire] = C._LONG_TIME
            #boss['tick_timer'][no_expire] = C._IGNITE_TICK
            #multiplier = np.ones(no_expire.shape)
            
            scorch = C._SCORCH_MULTIPLIER*boss['scorch_count'][no_expire]
            multiplier = C._COE_MULTIPLIER*boss['ignite_multiplier'][no_expire]
            multiplier *= 1.0 + scorch*(boss['scorch_timer'][no_expire] > 0.0).astype(np.float32)
            multiplier *= 1.0 + C._NIGHTFALL_BUFF*(boss["spell_vulnerability"][no_expire] > 0.0).astype(np.float32)

            rolls = np.random.rand(multiplier.size)
            conditions = [np.logical_and(rolls >= ll, rolls < ul) for ll, ul in zip(C._RES_THRESH, C._RES_THRESH_UL)]
            partials = np.piecewise(rolls, conditions, C._RES_AMOUNT)
            multiplier *= partials

            #self._damage[no_expire] += multiplier*boss['ignite_value'][no_expire]
            self._ignite[no_expire] += multiplier*boss['ignite_value'][no_expire]
            if C._LOG_SIM >= 0:
                if C._LOG_SIM in no_expire:
                    sub_index = no_expire.tolist().index(C._LOG_SIM)
                    message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                    print(message.format(self._arrays['global']['total_damage'][C._LOG_SIM] + self._damage[C._LOG_SIM],
                                         self._arrays['global']['running_time'][C._LOG_SIM],
                                         multiplier[sub_index]*boss['ignite_value'][C._LOG_SIM]))

    def _do_proc(self, still_going, proc_array):
        C = self._C
        player = self._arrays['player']        
        boss = self._arrays['boss']

        proc_hits = np.where(proc_array)[0]
        if proc_hits.size > 0:
            proc = still_going[proc_hits]
            next_proc = np.argmin(player['nightfall'][proc, :], axis=1)
            add_time = np.min(player['nightfall'][proc, :], axis=1)

            self._subtime(proc, add_time)

            player['nightfall'][proc, next_proc] = player["nightfall_period"][next_proc]

            rolls = np.random.rand(proc.size)
            procs = np.where(rolls < C._NIGHTFALL_PROB)[0]
            boss["spell_vulnerability"][proc[procs]] = C._NIGHTFALL_DURATION

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
        proc_timer = np.copy(np.min(self._arrays['player']['nightfall'][still_going, :], axis=1))
        cast_array = (cast_timer < spell_timer) & (cast_timer < tick_timer) & (cast_timer < proc_timer)

        # casts
        self._do_cast(still_going, cast_array)

        # spell hits
        spell_array = np.logical_not(cast_array) & (spell_timer < tick_timer) & (spell_timer < proc_timer)
        self._do_spell(still_going, spell_array)

        # ticks
        tick_array = np.logical_not(cast_array | spell_array) & (tick_timer < proc_timer)
        self._do_tick(still_going, tick_array)
        
        # procs
        proc_array = np.logical_not(cast_array | spell_array | tick_array)
        self._do_proc(still_going, proc_array)
    
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
        mqg = (player['buff_timer'][C._BUFF_MQG][still_going[on_gcd], next_hit[on_gcd]] > 0.0).astype(np.float32)
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
        self._arrays['global']['decision'] = np.zeros(self._arrays['global']['decision'].shape, dtype=bool)
    
    def run(self, update_progress):
        double_dip = (1.0 + 0.1*float("sayges_dark_fortune_of_damage" in self._world_buffs))
        double_dip *= (1.0 + 1.9*float(self._boss_buffs == "thaddius"))
        C = constants.Constant(double_dip)
        self._C = C

        over_time = True if self._run_params["type"] == "over_time" else False
        self._arrays = self._array_generator.run(C, over_time)
        self._all = self._arrays['player']['target'].size == self._arrays['player']['cast_number'].shape[1]

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
            self._damage = np.zeros(self._arrays['global']['running_time'].size)
            if not self._all:
                self._player = np.zeros(self._arrays['global']['running_time'].size)
            self._crit = np.zeros(self._arrays['global']['running_time'].size)
            self._ignite = np.zeros(self._arrays['global']['running_time'].size)
            decisions, next_hit = decider.get_decisions(self._arrays, still_going)
            self._apply_decisions(still_going, decisions, next_hit)
            while self._advance():
                still_going = np.where(self._arrays['global']['running_time'] < self._arrays['global']['duration'])[0]
            if not over_time:
                self._arrays['global']['total_damage'][still_going] += self._damage[still_going]
                if not self._all:
                    self._arrays['global']['player'][still_going] += self._player[still_going]
                self._arrays['global']['crit'][still_going] += self._crit[still_going]
                self._arrays['global']['ignite'][still_going] += self._ignite[still_going]
            else:
                if self._all:
                    for sidx, stime in enumerate(self._arrays['global']['running_time']):
                        self._arrays['global']['total_damage'][sidx].append((stime, self._damage[sidx], self._ignite[sidx]))
                else:
                    for sidx, stime in enumerate(self._arrays['global']['running_time']):
                        self._arrays['global']['total_damage'][sidx].append((stime, self._player[sidx], self._ignite[sidx]))
            progress = 100*self._arrays['global']['running_time'].mean()/self._arrays['global']['duration'].mean()
            update_progress.emit((self._run_params["id"], progress))
            if not still_going.size:
                break

        target_fraction = len(self._config["target"])/self._arrays['player']['cast_number'].shape[1]
        if not over_time:
            if C._LOG_SIM >= 0:
                print('total log damage = {:7.0f}'.format(self._arrays['global']['total_damage'][C._LOG_SIM]/self._arrays['player']['cast_number'].shape[1]/self._arrays['global']['duration'][C._LOG_SIM]))
                print('average damage = {:9.1f}'.format(self._arrays['global']['total_damage'].mean()))
                print('std damage = {:7.1f}'.format(self._arrays['global']['total_damage'].std()))
                print('crit damage = {:9.1f}'.format(self._arrays['global']['crit'].mean()))
                print('ignite damage = {:9.1f}'.format(self._arrays['global']['ignite'].mean()))
    
            if self._all:
                mage_damage = (self._arrays['global']['total_damage'] + self._arrays['global']['ignite'])/self._arrays['global']['duration']
            else:
                mage_damage = self._arrays['global']['player']/self._arrays['global']['duration']
                mage_damage += self._arrays['global']['ignite']*target_fraction/self._arrays['global']['duration']

            smage = np.sort(mage_damage)
    
            return self._run_params["id"], smage
        else:
            sim_size = len(self._arrays['global']['total_damage'])
            dur_dist = self._run_params["dur_dist"]
            # variablity depends on length (5%).  This smooths out curves
            cutoff = 0.05*dur_dist.reshape(dur_dist.size, 1)*np.random.randn(len(dur_dist), sim_size) 
            for didx, dur in enumerate(dur_dist):
                cutoff[didx, :] += dur
            cutoff[cutoff < 0.0] = 0.0

            max_ind = np.array([len(arr) for arr in self._arrays['global']['total_damage']]).astype(np.int32) - 1
            max_length = max(max_ind) + 1
            ctime = np.inf*np.ones((max_length, sim_size))
            damage = np.zeros((max_length, sim_size))
            ignite = np.zeros((max_length, sim_size))

            for sidx in range(sim_size):
                cur_array = self._arrays['global']['total_damage'][sidx]
                cur_length = len(cur_array)
                ctime[:cur_length, sidx] = np.array([arr[0] for arr in cur_array])
                damage[:cur_length, sidx] = np.array([arr[1] for arr in cur_array])
                ignite[:cur_length, sidx] = np.array([arr[2] for arr in cur_array])

            damage = np.cumsum(damage, axis=0)
            ignite = np.cumsum(ignite, axis=0)

            total_damage = []
            total_ignite = []
            for cidx in range(cutoff.shape[0]):
                up_to = np.argmax(ctime > cutoff[cidx, :], axis=0).squeeze()
                up_to[np.logical_not(up_to)] = max_ind[np.logical_not(up_to)]
                total_cut = ctime[up_to, np.arange(sim_size)]
                total_damage.append((damage[up_to, np.arange(sim_size)]/total_cut).mean())
                total_ignite.append((ignite[up_to, np.arange(sim_size)]/total_cut).mean())
            total_dam = np.array(total_damage)
            ignite_dam = np.array(total_ignite)

            return self._run_params["id"], total_dam + target_fraction*ignite_dam

def get_damage(params, run_params, progress_callback=None):
    if constants._LOG_SIM >= 0:
        print(params)
    array_generator = constants.ArrayGenerator(params)
    encounter = Encounter(array_generator,
                          params['rotation'],
                          params['timing']['response'],
                          params['timing']['duration']['var'],
                          params['configuration'],
                          params["buffs"]["world"],
                          params["buffs"]["boss"],
                          run_params)
    return encounter.run(progress_callback)

