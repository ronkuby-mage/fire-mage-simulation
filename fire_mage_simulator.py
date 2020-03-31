import os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import itertools
from multiprocessing import Pool

class Constant():
    
    def __init__(self):

        ## run parameters

        self._DO_CRIT_SP_EQUIV = True
        self._DO_ROTATION_SEARCH = True
        self._DO_DPS_PER_MAGE = True
        
        ## scenario variables
        self._NUM_MAGES = 6
        self._HIT_CHANCE = 0.96
        self._DAMAGE = 700

        self._CRIT_START = 0.15
        self._CRIT_END = 0.70
        self._CRIT_STEP = 0.05

        self._MAGES_START = 3
        self._MAGES_END = 9

        self._SP_START = 300
        self._SP_END = 900
        self._SP_STEP = 50

        self._SIM_SIZE = 25000

        self._DURATION_AVERAGE = 120.0
        self._DURATION_SIGMA = 12.0

        # curse of the elements and firepower (improved scorch handled on-the-fly)
        self._DAMAGE_MULTIPLIER = 1.1*1.1

        ## strategy/performance variables
        # maximum seconds before scorch expires for designated mage to start casting scorch
        self._MAX_SCORCH_REMAIN = 5.0

        # cast initial/response time variation
        self._INITIAL_SIGMA = 0.4
        self._CONTINUING_SIGMA = 0.05

        # rotation strategies
        self._FIRST_SPELL = 1
        self._FIRST_PYROBLAST = 0
        self._FIRST_FROSTBOLT = 1
        self._INITAL_SCORCHES = 2
        self._INITIAL_ONE = 0
        self._INITIAL_TWO = 2
        self._FIRE_BLAST = 4
        self._FIRE_BLAST_NO = 0
        self._FIRE_BLAST_YES = 4

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

        self._EXTRA_SCORCHES = 1

        ## debugging

        self._LOG_SIM = -1 # set to -1 for no log
        self._LOG_SPELL = ['scorch    ', 'pyroblast ', 'fireball  ', 'fire blast']

def advance(arrays, crit_chance, plus_damage, rotation):
    C = Constant()

    total_damage = arrays['total_damage']
    ignite_count = arrays['ignite_count']
    ignite_time = arrays['ignite_time']
    ignite_tick = arrays['ignite_tick']
    ignite_value = arrays['ignite_value']
    scorch_count = arrays['scorch_count']
    scorch_time = arrays['scorch_time']
    running_time = arrays['running_time']
    cast_timer = arrays['cast_timer']
    cast_type = arrays['cast_type']
    comb_stack = arrays['comb_stack']
    comb_left = arrays['comb_left']
    spell_timer = arrays['spell_timer']
    spell_type = arrays['spell_type']
    cast_number = arrays['cast_number']
    duration = arrays['duration']
    arrays['damage'] = np.zeros((C._SIM_SIZE, 1))
    damage = arrays['damage']

    epsilon = 0.000001
    scorches = (rotation&C._INITAL_SCORCHES) == C._INITIAL_TWO
    early_combustion = False
    fire_blast_yes = (rotation&C._FIRE_BLAST) == C._FIRE_BLAST_YES

    if early_combustion:
        comb_left[:, :] = C._COMBUSTIONS
        comb_stack[:, :] = 0
    
    still_going = np.where(running_time < duration)[0]
    if still_going.size == 0:
        return False

    cast_time = np.min(cast_timer[still_going], axis=1, keepdims=True)
    spell_time = np.min(spell_timer[still_going], axis=1, keepdims=True)
    ignite_copy = np.copy(ignite_time[still_going])

    zi_array = np.logical_and(np.logical_and(ignite_copy < cast_time,
                                             ignite_count[still_going]),
                              np.logical_or(ignite_copy < scorch_time[still_going],
                                            np.logical_not(scorch_count[still_going])))
    zi_array = np.logical_and(zi_array, ignite_copy < ignite_tick[still_going])
    zi_array = np.logical_and(zi_array, ignite_copy < spell_time)
    zero_ignite = np.where(zi_array)[0]
    if zero_ignite.size > 0:
        running_time[still_going[zero_ignite]] += ignite_time[still_going[zero_ignite]]
        cast_timer[still_going[zero_ignite], :] -= ignite_time[still_going[zero_ignite]]
        spell_timer[still_going[zero_ignite], :] -= ignite_time[still_going[zero_ignite]]
        scorch_time[still_going[zero_ignite]] -= ignite_time[still_going[zero_ignite]]
        if C._LOG_SIM >= 0:
            if C._LOG_SIM in still_going[zero_ignite]:
                sub_index = still_going[zero_ignite].tolist().index(C._LOG_SIM)
                message = ' {:7.0f} ({:6.2f}): ignite expired'
                print(message.format(total_damage[C._LOG_SIM][0] + damage[C._LOG_SIM][0], running_time[C._LOG_SIM][0]))
        ignite_count[still_going[zero_ignite]] = 0
        ignite_time[still_going[zero_ignite]] = 0.0
        ignite_value[still_going[zero_ignite]] = 0.0
        ignite_tick[still_going[zero_ignite]] = 0.0

    ti_array = np.logical_and(ignite_tick[still_going] < cast_time,
                              ignite_tick[still_going] < scorch_time[still_going])
    ti_array = np.logical_and(ti_array, ignite_count[still_going])
    ti_array = np.logical_and(ti_array, ignite_tick[still_going] < spell_time)
    tick_ignite = np.where(ti_array)[0]
    if tick_ignite.size > 0:
        running_time[still_going[tick_ignite]] += ignite_tick[still_going[tick_ignite]]
        cast_timer[still_going[tick_ignite], :] -= ignite_tick[still_going[tick_ignite]]
        spell_timer[still_going[tick_ignite], :] -= ignite_tick[still_going[tick_ignite]]
        scorch_time[still_going[tick_ignite]] -= ignite_tick[still_going[tick_ignite]]
        ignite_time[still_going[tick_ignite]] -= ignite_tick[still_going[tick_ignite]]
        ignite_tick[still_going[tick_ignite]] = C._IGNITE_TICK
        multiplier = 1.0 + 0.03*scorch_count[still_going[tick_ignite]]
        damage[still_going[tick_ignite]] += ignite_value[still_going[tick_ignite]]*multiplier
        if  C._LOG_SIM >= 0:
            if  C._LOG_SIM in still_going[tick_ignite]:
                sub_index = still_going[tick_ignite].tolist().index( C._LOG_SIM)
                message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                print(message.format(total_damage[ C._LOG_SIM][0] + damage[ C._LOG_SIM][0], running_time[ C._LOG_SIM][0], ignite_value[ C._LOG_SIM][0]*multiplier[sub_index][0]))

    ig_array = np.logical_or(zi_array, ti_array)
    se_array = np.logical_and(np.logical_and(np.logical_not(ig_array),
                                             scorch_time[still_going] < cast_time),
                              scorch_count[still_going])
    
    se_array = np.logical_and(se_array, ignite_copy < spell_time)
    scorch_expire = np.where(se_array)[0]
    if scorch_expire.size > 0:
        if  C._LOG_SIM >= 0:
            if  C._LOG_SIM in still_going[scorch_expire]:
                message = '         ({:6.2f}): scorch expired {:4.2f}'
                print(message.format(running_time[ C._LOG_SIM][0], scorch_time[still_going[scorch_expire]][0][0]))
        running_time[still_going[scorch_expire]] += scorch_time[still_going[scorch_expire]]
        cast_timer[still_going[scorch_expire], :] -= scorch_time[still_going[scorch_expire]]
        spell_timer[still_going[scorch_expire], :] -= scorch_time[still_going[scorch_expire]]
        ignite_time[still_going[scorch_expire]] -= scorch_time[still_going[scorch_expire]]
        ignite_tick[still_going[scorch_expire]] -= scorch_time[still_going[scorch_expire]]
        scorch_count[still_going[scorch_expire]] = 0
        scorch_time[still_going[scorch_expire]] = 0.0

    cast_array = np.logical_not(np.logical_or(ig_array, se_array))
    cast_array = np.logical_and(cast_array, cast_time < spell_time)
    cast_ends = np.where(cast_array)[0]
    if cast_ends.size > 0:
        cst = still_going[cast_ends]
        next_hit = np.argmin(cast_timer[cst, :], axis=1)
        add_time = np.min(cast_timer[cst, :], axis=1, keepdims=True)
        running_time[cst] += add_time
        ignite_time[cst] -= add_time
        ignite_tick[cst] -= add_time
        cast_timer[cst] -= add_time
        spell_timer[cst] -= add_time
        scorch_time[cst] -= add_time
       
        react_time = np.abs(C._CONTINUING_SIGMA*np.random.randn(cst.size))
        cast_copy = np.copy(cast_type[cst, next_hit])

        if  C._LOG_SIM >= 0:
            if  C._LOG_SIM in cst:
                message = '         ({:6.2f}): player {:d} finished casting {:s}'
                sub_index = cst.tolist().index( C._LOG_SIM)
                message = message.format(running_time[ C._LOG_SIM][0],
                                         next_hit[sub_index] + 1,
                                         C._LOG_SPELL[cast_copy[sub_index]])
                print(message)

        # pyroblast next
        if scorches:
            pyro_array = np.squeeze(cast_number[cst, next_hit] == C._EXTRA_SCORCHES)
        else:
            pyro_array = np.squeeze(np.logical_not(cast_number[cst, next_hit]))
        pyroblast = np.where(pyro_array)[0]
        if fire_blast_yes:
            cast_timer[cst[pyroblast], next_hit[pyroblast]] = epsilon + react_time[pyroblast]
            cast_type[cst[pyroblast], next_hit[pyroblast]] = C._CAST_FIRE_BLAST
        elif (rotation&C._FIRST_SPELL) == C._FIRST_PYROBLAST:
            cast_timer[cst[pyroblast], next_hit[pyroblast]] = C._PYROBLAST_CASTTIME + react_time[pyroblast]
            cast_type[cst[pyroblast], next_hit[pyroblast]] = C._CAST_PYROBLAST
        else:
            cast_timer[cst[pyroblast], next_hit[pyroblast]] = C._FIREBALL_CASTTIME + C._FROSTBOLT_CASTTIME + react_time[pyroblast]
            cast_type[cst[pyroblast], next_hit[pyroblast]] = C._CAST_FIREBALL
            damage[cst[pyroblast]] += C._HIT_CHANCE*(1 + C._FROSTBOLT_CRIT_DAMAGE*(crit_chance - C._FROSTBOLT_CRIT_MOD))*(C._FROSTBOLT_DAMAGE + C._FROSTBOLT_MODIFIER*(plus_damage - C._FROSTBOLT_PLUS))*C._FROSTBOLT_OVERALL
            

        # scorch next
        scorcher = np.logical_not(np.logical_or(next_hit, pyro_array)) # scorch mage only
        scorch_array = np.logical_and(scorcher,
                                      np.logical_or(np.squeeze(scorch_count[cst]) < C._SCORCH_STACK,
                                                    np.squeeze(scorch_time[cst]) < C._MAX_SCORCH_REMAIN))
        scorch_array = np.logical_and(scorch_array, cast_copy != C._CAST_SCORCH)
        if scorches:
            scorch_array = np.logical_or(scorch_array, cast_number[cst, next_hit] < C._EXTRA_SCORCHES)
        if fire_blast_yes:
            scorch_array = np.logical_and(scorch_array, cast_number[cst, next_hit] >= C._EXTRA_SCORCHES + 1)
        scorch = np.where(scorch_array)[0]
        cast_timer[cst[scorch], next_hit[scorch]] = C._SCORCH_CASTTIME + react_time[scorch]
        cast_type[cst[scorch], next_hit[scorch]] = C._CAST_SCORCH

        # fireball next
        fireball = np.where(np.logical_not(np.logical_or(scorch_array, pyro_array)))[0]
        cast_timer[cst[fireball], next_hit[fireball]] = C._FIREBALL_CASTTIME + react_time[fireball]
        cast_type[cst[fireball], next_hit[fireball]] = C._CAST_FIREBALL

        spell_type[cst, next_hit] = cast_copy
        spell_timer[cst, next_hit] = C._SPELL_TIME[cast_copy]
        if fire_blast_yes:
            gcd = np.where(cast_number[cst, next_hit] == C._EXTRA_SCORCHES)[0]
            cast_timer[cst[gcd], next_hit[gcd]] += C._GLOBAL_COOLDOWN
        cast_number[cst, next_hit] += 1

    spell_lands = np.where(np.logical_not(np.logical_or(np.logical_or(ig_array, se_array), cast_array)))[0]
    if spell_lands.size > 0:
        spl = still_going[spell_lands]
        next_hit = np.argmin(spell_timer[spl, :], axis=1)
        add_time = np.min(spell_timer[spl, :], axis=1, keepdims=True)
        running_time[spl] += add_time
        ignite_time[spl] -= add_time
        ignite_tick[spl] -= add_time
        cast_timer[spl] -= add_time
        spell_timer[spl] -= add_time
        scorch_time[spl] -= add_time

        spell_copy = spell_type[spl, next_hit]

        if  C._LOG_SIM >= 0:
            if  C._LOG_SIM in spl:
                message = ' ({:6.2f}): player {:d} {:s} landed '
                sub_index = spl.tolist().index( C._LOG_SIM)
                message = message.format(running_time[ C._LOG_SIM][0],
                                         next_hit[sub_index] + 1,
                                         C._LOG_SPELL[spell_copy[sub_index]])
                message2 = 'misses         '

        for spell in range(C._CASTS):
            
            is_spell = np.where(spell_copy == spell)[0]
            spell_hits = np.where(np.random.rand(is_spell.size) < C._HIT_CHANCE)[0]
            if spell_hits.size > 0:

                sph = spl[is_spell][spell_hits]
                spell_damage = C._SPELL_BASE[spell] + \
                               C._SPELL_RANGE[spell]*np.random.rand(sph.size, 1) +\
                               C._MULTIPLIER[spell]*plus_damage
                spell_damage *= (1.0 + 0.03*scorch_count[sph])*C._DAMAGE_MULTIPLIER
                # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

                # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MECHANICS **
                ccrit_chance = crit_chance + C._PER_COMBUSTION*comb_stack[sph, next_hit[is_spell][spell_hits]]*comb_left[sph, next_hit[is_spell][spell_hits]]
                crit_array = np.random.rand(sph.size) < ccrit_chance
                lcrits = np.where(crit_array)[0]
                crits = sph[lcrits]
                # refresh ignite to full 4 seconds
                ignite_time[crits] = C._IGNITE_TIME + epsilon
                # if we dont have a full stack
                mod_val = np.where(ignite_count[crits] < C._IGNITE_STACK)[0]
                # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                ignite_value[crits[mod_val]] += C._CRIT_DAMAGE*C._IGNITE_DAMAGE*spell_damage[lcrits[mod_val]]
                mod_val2 = np.where(ignite_count[crits] == 0)[0]
                # set the tick
                ignite_tick[crits[mod_val2]] = C._IGNITE_TICK
                # increment to max of five (will do nothing if alreeady at 5)
                ignite_count[crits] = np.minimum(ignite_count[crits] + 1, C._IGNITE_STACK)
                damage[crits] += C._CRIT_DAMAGE*spell_damage[lcrits]
                comb_left[crits, next_hit[is_spell][spell_hits][lcrits]] = np.maximum(comb_left[crits, next_hit[is_spell][spell_hits][lcrits]] - 1, 0)

                # normal hit
                nocrits = np.where(np.logical_not(crit_array))[0]
                damage[sph[nocrits]] += spell_damage[nocrits]

                if  C._LOG_SIM >= 0:
                    if  C._LOG_SIM in sph:
                        sub_index = sph.tolist().index(C._LOG_SIM)
                        if  C._LOG_SIM in crits:
                            message2 = 'crits for {:4.0f} '.format(C._CRIT_DAMAGE*spell_damage[sub_index][0])
                        else:
                            message2 = ' hits for {:4.0f} '.format(spell_damage[sub_index][0])

                # scorch
                if C._IS_SCORCH[spell]:
                    scorch_time[sph] = C._SCORCH_TIME
                    scorch_count[sph] = np.minimum(scorch_count[sph] + 1, C._SCORCH_STACK)
                    
                comb_stack[sph, next_hit[is_spell][spell_hits]] += 1
        spell_timer[spl, next_hit] = C._DURATION_AVERAGE

        # cast combustion before pyroblast (don't apply to scorch)
        if not early_combustion:
            if scorches:
                comb_array = cast_number[spl, next_hit] == int(fire_blast_yes) + C._EXTRA_SCORCHES + 1
            else:
                comb_array = cast_number[spl, next_hit] == int(fire_blast_yes) + 1
            do_comb = np.where(comb_array)[0]
            comb_left[spl[do_comb], next_hit[do_comb]] = C._COMBUSTIONS
            comb_stack[spl[do_comb], next_hit[do_comb]] = 0


        if  C._LOG_SIM >= 0:
            if  C._LOG_SIM in spl:
                sub_index = spl.tolist().index(C._LOG_SIM)
                dam_done = ' {:7.0f}'.format(total_damage[ C._LOG_SIM][0] + damage[C._LOG_SIM][0])
                message3 = C._LOG_SPELL[cast_type[C._LOG_SIM][next_hit[sub_index]]]
                message = message + message2 + 'next is ' + message3
                status = ' ic {:d} it {:4.2f} in {:4.2f} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d}'
                status = status.format(ignite_count[C._LOG_SIM][0],
                                       max([ignite_time[C._LOG_SIM][0], 0.0]),
                                       max([ignite_tick[C._LOG_SIM][0], 0.0]),
                                       ignite_value[C._LOG_SIM][0],
                                       scorch_count[C._LOG_SIM][0],
                                       max([scorch_time[C._LOG_SIM][0], 0.0]),
                                       comb_stack[C._LOG_SIM][next_hit[sub_index]],
                                       comb_left[C._LOG_SIM][next_hit[sub_index]])
                print(dam_done + message + status)

    
    return True

def get_damage(sp, crit, num_mages, rotation):
    C = Constant()
    sim_size = C._SIM_SIZE
    arrays = {
            'total_damage': np.zeros((sim_size, 1)),
            'ignite_count': np.zeros((sim_size, 1)).astype(np.int32),
            'ignite_time': np.zeros((sim_size, 1)),
            'ignite_tick': np.zeros((sim_size, 1)),
            'ignite_value': np.zeros((sim_size, 1)),
            'scorch_count': np.zeros((sim_size, 1)).astype(np.int32),
            'scorch_time': np.zeros((sim_size, 1)),
            'running_time': np.zeros((sim_size, 1)),
            'cast_timer': np.abs(C._INITIAL_SIGMA*np.random.randn(sim_size, num_mages)),
            'cast_type': C._CAST_SCORCH*np.ones((sim_size, num_mages)).astype(np.int32),
            'comb_stack': np.zeros((sim_size, num_mages)).astype(np.int32),
            'comb_left': np.zeros((sim_size, num_mages)).astype(np.int32),
            'spell_timer': C._DURATION_AVERAGE*np.ones((sim_size, num_mages)),
            'spell_type': C._CAST_SCORCH*np.ones((sim_size, num_mages)).astype(np.int32),
            'cast_number': np.zeros((sim_size, num_mages)).astype(np.int32),
            'duration': C._DURATION_AVERAGE + C._DURATION_SIGMA*np.random.randn(sim_size, 1)}
    

    if  C._LOG_SIM >= 0:
        message = 'log for spell power = {:3.0f}, crit chance = {:2.0f}%, hit chance = {:2.0f}%:'
        message = message.format(sp, crit*100.0, C._HIT_CHANCE*100.0)
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

    while advance(arrays, crit, sp, rotation):
        still_going = np.where(arrays['running_time'] < arrays['duration'])[0]
        arrays['total_damage'][still_going] += arrays['damage'][still_going]
    if  C._LOG_SIM >= 0:
        print('total damage = {:7.0f}'.format(arrays['total_damage'][ C._LOG_SIM][0]))

    return (arrays['total_damage']/arrays['duration']).mean()

def get_damage_diff(sp, crit, num_mages, rotation):
    dcrit = 0.025
    dsp = 25.0
    factor = dsp/dcrit/100.0

    dm_sp = get_damage(sp - dsp, crit, num_mages, rotation)
    dp_sp = get_damage(sp + dsp, crit, num_mages, rotation)
    dm_crit = get_damage(sp, crit - dcrit, num_mages, rotation)
    dp_crit = get_damage(sp, crit + dcrit, num_mages, rotation)

    return factor*(dp_crit - dm_crit)/(dp_sp - dm_sp)

def get_rotation_ratio(damage, crit, num_mages, rotation1, rotation2):
    dm_1 = get_damage(damage, crit, num_mages, rotation1)
    dm_2 = get_damage(damage, crit, num_mages, rotation2)
            
    return dm_2/dm_1

if __name__ == '__main__':
    C = Constant()
    if C._DO_CRIT_SP_EQUIV:
        crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
        sps = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, C._SP_STEP)
        nmages = np.arange(C._MAGES_START, C._MAGES_END + 1, dtype=np.int32)
        rotation = C._FIRST_PYROBLAST|C._INITIAL_ONE|C._FIRE_BLAST_NO
        rotations = np.array([rotation], dtype=np.int32)
        args = itertools.product(sps, crit_chance, nmages, rotations)

        print('Generating plots. This could take a while.  Reduce _SIM_SIZE for faster less but less accurate results.')
        with Pool() as p:
            out = np.array(p.starmap(get_damage_diff, args)).reshape((len(sps), len(crit_chance), len(nmages), len(rotations)))

        for index, num_mages in enumerate(nmages):
            conversions = np.squeeze(out[:, :, index, :])
            colors = ['indigo', 'purple', 'darkblue', 'royalblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
            plt.close('all')
            fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
            plt.title('{:d} mages, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(num_mages, C._HIT_CHANCE*100.0, C._SIM_SIZE, C._DURATION_AVERAGE))
            plt.xlabel('Crit Chance (percent)')
            plt.ylabel('SP ratio')
            plt.xlim(0, 75.0)
            plt.ylim(0, 5 + int(np.array(conversions).max()/5)*5)

            for color, spell_power, conv in zip(colors, sps, conversions):
                plt.plot(100.0*np.array(crit_chance), np.array(conv), label='{:3.0f} SP'.format(spell_power), color=color, marker='.')
            plt.legend()
            plt.grid()
            savefile = 'sp_equiv_plots\sp_equiv_{:d}_mages_{:2.0f}_{:d}.png'.format(num_mages, C._HIT_CHANCE*100.0, C._SIM_SIZE)
            os.makedirs('sp_equiv_plots', exist_ok=True)
            plt.savefig(savefile)

    if C._DO_ROTATION_SEARCH:
        desc = ['(frostbolt+fireball average damage)/(pyroblast average damage)',
                '(cast two scorches first)/(cast one scorch first)',
                '(fire blast, no pyroblast)/(cast combustion after scorch)']
        fn_desc = ['frostbolt', 'two_scorches', 'fire_blast_open']
        first_rotation = np.array([C._FIRST_PYROBLAST, C._INITIAL_ONE, C._FIRE_BLAST_NO], dtype=np.int32)
        second_rotation = np.array([C._FIRST_FROSTBOLT, C._INITIAL_TWO, C._FIRE_BLAST_YES], dtype=np.int32)
        desc = ['(fire blast, no pyroblast)/(cast combustion after scorch)']
        fn_desc = ['fire_blast_open']
        first_rotation = np.array([C._FIRE_BLAST_NO], dtype=np.int32)
        second_rotation = np.array([C._FIRE_BLAST_YES], dtype=np.int32)

        crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
        nmages = np.arange(C._MAGES_START, C._MAGES_END + 1, dtype=np.int32)
        sps = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, 2.0*C._SP_STEP)
        for rotation1, rotation2, description, fn in zip(first_rotation, second_rotation, desc, fn_desc):
            rotation1s = np.array([rotation1], dtype=np.int32)
            rotation2s = np.array([rotation2], dtype=np.int32)
            args = itertools.product(sps, crit_chance, nmages, rotation1s, rotation2s)
            
            print('Generating plots. This could take a while.  Reduce _SIM_SIZE for faster less but less accurate results.')
            with Pool() as p:
                out = np.array(p.starmap(get_rotation_ratio, args)).reshape((len(sps), len(crit_chance), len(nmages), len(rotation1s), len(rotation2s)))

            for index, sp in enumerate(sps):
                compares = np.squeeze(out[index, :, :, :, :]).transpose()

                colors = ['indigo', 'royalblue', 'skyblue', 'lime', 'gold', 'darkorange', 'firebrick']
                plt.close('all')
                fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
                plt.title('{:3.0f} spell damage, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(sp, C._HIT_CHANCE*100.0, C._SIM_SIZE, C._DURATION_AVERAGE))
                plt.xlabel('Crit Chance (percent)')
                plt.ylabel(description)
                plt.xlim(0, 75.0)
                for color, num_mages, comp in zip(colors, nmages, compares):
                    plt.plot(100.0*np.array(crit_chance), np.array(comp), label='{:d} mages'.format(num_mages), color=color, marker='.')
                plt.legend()
                plt.grid()
                savefile = 'rotation_plots\{:s}_{:3.0f}.png'.format(fn, sp)
                os.makedirs('rotation_plots', exist_ok=True)
                plt.savefig(savefile)

    if C._DO_DPS_PER_MAGE:
        crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
        sps = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, C._SP_STEP)
        nmages = np.arange(1, C._MAGES_END + 1, dtype=np.int32)
        rotation = C._FIRST_PYROBLAST|C._INITIAL_ONE|C._FIRE_BLAST_NO
        rotations = np.array([rotation], dtype=np.int32)

        args = itertools.product(sps, crit_chance, nmages, rotations)

        with Pool() as p:
            out = np.array(p.starmap(get_damage, args)).reshape((len(sps), len(crit_chance), len(nmages), len(rotations)))
        out /= nmages.reshape(1, 1, nmages.size, 1)

        for index, sp in enumerate(sps):
            damages = np.squeeze(out[index, :, :, :])
            colors = ['indigo', 'purple', 'darkblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
            plt.close('all')
            fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
            plt.title('{:3.0f} spell damage, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(sp, C._HIT_CHANCE*100.0, C._SIM_SIZE, C._DURATION_AVERAGE))
            plt.xlabel('Number of mages')
            plt.ylabel('Average DPS')
            plt.xlim(0, 10)
            for color, crit, damage in zip(colors, crit_chance, damages):
                plt.plot(np.array(nmages), np.array(damage), label='{:4.2f}'.format(crit), color=color, marker='.')
            plt.legend()
            plt.grid()

            savefile = 'dps_per_mage_plots\spellpower_{:3.0f}.png'.format(sp)
            os.makedirs('dps_per_mage_plots', exist_ok=True)
            plt.savefig(savefile)

    # run a simulation outside multiprocessing to see log messages
    if C._LOG_SIM >= 0:
        d0 = get_damage(700, 0.35, 6, 4)
