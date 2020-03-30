import os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import time

## run parameters

_DO_CRIT_SP_EQUIV = True
_DO_ROTATION_SEARCH = True
_DO_DPS_PER_MAGE = True

## scenario variables
_NUM_MAGES = 6
_HIT_CHANCE = 0.96
_DAMAGE = 700

_CRIT_START = 0.15
_CRIT_END = 0.70
_CRIT_STEP = 0.05

_MAGES_START = 3
_MAGES_END = 9

_SP_START = 300
_SP_END = 900
_SP_STEP = 50

_SIM_SIZE = 25000

_DURATION_AVERAGE = 120.0
_DURATION_SIGMA = 12.0

# curse of the elements and firepower (improved scorch handled on-the-fly)
_DAMAGE_MULTIPLIER = 1.1*1.1

## strategy/performance variables
# maximum seconds before scorch expires for designated mage to start casting scorch
_MAX_SCORCH_REMAIN = 5.0

# cast initial/response time variation
_INITIAL_SIGMA = 0.4
_CONTINUING_SIGMA = 0.05

# rotation strategies
_FIRST_SPELL = 1
_FIRST_PYROBLAST = 0
_FIRST_FROSTBOLT = 1
_INITAL_SCORCHES = 2
_INITIAL_ONE = 0
_INITIAL_TWO = 2
_COMBUSTION_TIMING = 4
_COMBUSTION_LATER = 0
_COMBUSTION_FIRST = 4

## constants, do not change
_IGNITE_TIME = 4.0
_IGNITE_STACK = 5

_SCORCH_TIME = 30.0
_SCORCH_STACK = 5

_CAST_SCORCH = 0
_CAST_PYROBLAST = 1
_CAST_FIREBALL = 2
_CASTS = 3

_MULTIPLIER = [0.428571429, 1.0, 1.0]
_SPELL_BASE = [237, 716, 596]
_SPELL_RANGE = [43, 174, 164]
_IS_SCORCH = [True, False, False]
_SPELL_TIME = np.array([0.0, 0.875, 0.875])

_FIREBALL_RANK = 12
if _FIREBALL_RANK == 11:
    _SPELL_BASE[_CAST_FIREBALL] = 561.0
    _SPELL_RANGE[_CAST_FIREBALL] = 154.0

_IGNITE_DAMAGE = 0.2*1.1
_CRIT_DAMAGE = 1.5

_COMBUSTIONS = 3
_PER_COMBUSTION = 0.1

_SCORCH_CASTTIME = 1.5
_PYROBLAST_CASTTIME = 6.0
_FIREBALL_CASTTIME = 3.0

_FROSTBOLT_TALENTED = False
_FROSTBOLT_DAMAGE = 535
_FROSTBOLT_MODIFIER = 0.814285714
_FROSTBOLT_CRIT_MOD = 0.06
_FROSTBOLT_PLUS = 50.0

if _FROSTBOLT_TALENTED:
    _FROSTBOLT_CASTTIME = 2.5
    _FROSTBOLT_CRIT_DAMAGE = 1.0
    _FROSTBOLT_OVERALL = 1.1*1.06
else:
    _FROSTBOLT_CASTTIME = 3.0
    _FROSTBOLT_CRIT_DAMAGE = 0.5
    _FROSTBOLT_OVERALL = 1.1

_EXTRA_SCORCHES = 1

## debugging

_LOG_SIM = -1 # set to -1 for no log
_LOG_SPELL = ['scorch   ', 'pyroblast', 'fireball ']


def advance(arrays, crit_chance, plus_damage, rotation):
    total_damage = arrays['total_damage']
    ignite_count = arrays['ignite_count']
    ignite_time = arrays['ignite_time']
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
    arrays['damage'] = np.zeros((_SIM_SIZE, 1))
    damage = arrays['damage']

    scorches = (rotation&_INITAL_SCORCHES) == _INITIAL_TWO
    early_combustion = (rotation&_COMBUSTION_TIMING) == _COMBUSTION_FIRST
    if early_combustion:
        comb_left[:, :] = _COMBUSTIONS
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
    zi_array = np.logical_and(zi_array, ignite_copy < _IGNITE_TIME/2.0)
    zi_array = np.logical_and(zi_array, ignite_copy < spell_time)
    zero_ignite = np.where(zi_array)[0]
    if zero_ignite.size > 0:
        running_time[still_going[zero_ignite]] += ignite_time[still_going[zero_ignite]]
        cast_timer[still_going[zero_ignite], :] -= ignite_time[still_going[zero_ignite]]
        spell_timer[still_going[zero_ignite], :] -= ignite_time[still_going[zero_ignite]]
        scorch_time[still_going[zero_ignite]] -= ignite_time[still_going[zero_ignite]]
        multiplier = 1.0 + 0.03*scorch_count[still_going[zero_ignite]]
        damage[still_going[zero_ignite]] += ignite_value[still_going[zero_ignite]]*multiplier
        if _LOG_SIM >= 0:
            if _LOG_SIM in still_going[zero_ignite]:
                sub_index = still_going[zero_ignite].tolist().index(_LOG_SIM)
                message = ' {:7.0f} ({:6.2f}): ignite expired  {:4.0f} damage done'
                print(message.format(total_damage[_LOG_SIM][0] + damage[_LOG_SIM][0], running_time[_LOG_SIM][0], ignite_value[_LOG_SIM][0]*multiplier[sub_index][0]))
        ignite_count[still_going[zero_ignite]] = 0
        ignite_time[still_going[zero_ignite]] = 0.0
        ignite_value[still_going[zero_ignite]] = 0.0
        

    ti_array = np.logical_and(np.logical_and((ignite_copy - _IGNITE_TIME/2.0) < cast_time,
                                              ignite_copy >= _IGNITE_TIME/2.0),
                               np.logical_or((ignite_copy - _IGNITE_TIME/2.0) < scorch_time[still_going],
                                             np.logical_not(scorch_count[still_going])))
    ti_array = np.logical_and(ti_array, ignite_count[still_going])
    ti_array = np.logical_and(ti_array, (ignite_copy - _IGNITE_TIME/2.0) < spell_time)
    two_ignite = np.where(ti_array)[0]
    if two_ignite.size > 0:
        running_time[still_going[two_ignite]] += ignite_time[still_going[two_ignite]] - _IGNITE_TIME/2.0
        cast_timer[still_going[two_ignite], :] -= ignite_time[still_going[two_ignite]] - _IGNITE_TIME/2.0
        spell_timer[still_going[two_ignite], :] -= ignite_time[still_going[two_ignite]] - _IGNITE_TIME/2.0
        scorch_time[still_going[two_ignite]] -= ignite_time[still_going[two_ignite]] - _IGNITE_TIME/2.0
        multiplier = 1.0 + 0.03*scorch_count[still_going[two_ignite]]
        damage[still_going[two_ignite]] += ignite_value[still_going[two_ignite]]*multiplier
        ignite_time[still_going[two_ignite]] = _IGNITE_TIME/2.0 - 0.000001
        if _LOG_SIM >= 0:
            if _LOG_SIM in still_going[two_ignite]:
                sub_index = still_going[two_ignite].tolist().index(_LOG_SIM)
                message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                print(message.format(total_damage[_LOG_SIM][0] + damage[_LOG_SIM][0], running_time[_LOG_SIM][0], ignite_value[_LOG_SIM][0]*multiplier[sub_index][0]))

    ig_array = np.logical_or(zi_array, ti_array)
    se_array = np.logical_and(np.logical_and(np.logical_not(ig_array),
                                             scorch_time[still_going] < cast_time),
                              scorch_count[still_going])
    
    se_array = np.logical_and(se_array, ignite_copy < spell_time)
    scorch_expire = np.where(se_array)[0]
    if scorch_expire.size > 0:
        if _LOG_SIM >= 0:
            if _LOG_SIM in still_going[scorch_expire]:
                message = '         ({:6.2f}): scorch expired {:4.2f}'
                print(message.format(running_time[_LOG_SIM][0], scorch_time[still_going[scorch_expire]][0][0]))
        running_time[still_going[scorch_expire]] += scorch_time[still_going[scorch_expire]]
        cast_timer[still_going[scorch_expire], :] -= scorch_time[still_going[scorch_expire]]
        spell_timer[still_going[scorch_expire], :] -= scorch_time[still_going[scorch_expire]]
        ignite_time[still_going[scorch_expire]] -= scorch_time[still_going[scorch_expire]]
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
        cast_timer[cst] -= add_time
        spell_timer[cst] -= add_time
        scorch_time[cst] -= add_time
       
        react_time = np.abs(_CONTINUING_SIGMA*np.random.randn(cst.size))
        cast_copy = np.copy(cast_type[cst, next_hit])

        if _LOG_SIM >= 0:
            if _LOG_SIM in cst:
                message = '         ({:6.2f}): player {:d} finished casting {:s}'
                sub_index = cst.tolist().index(_LOG_SIM)
                message = message.format(running_time[_LOG_SIM][0],
                                         next_hit[sub_index] + 1,
                                         _LOG_SPELL[cast_copy[sub_index]])
                print(message)

        # pyroblast next
        if scorches:
            pyro_array = np.squeeze(cast_number[cst, next_hit] == _EXTRA_SCORCHES)
        else:
            pyro_array = np.squeeze(np.logical_not(cast_number[cst, next_hit]))
        pyroblast = np.where(pyro_array)[0]
        if (rotation&_FIRST_SPELL) == _FIRST_PYROBLAST:
            cast_timer[cst[pyroblast], next_hit[pyroblast]] = _PYROBLAST_CASTTIME + react_time[pyroblast]
            cast_type[cst[pyroblast], next_hit[pyroblast]] = _CAST_PYROBLAST
        else:
            cast_timer[cst[pyroblast], next_hit[pyroblast]] = _FIREBALL_CASTTIME + _FROSTBOLT_CASTTIME + react_time[pyroblast]
            cast_type[cst[pyroblast], next_hit[pyroblast]] = _CAST_FIREBALL
            damage[cst[pyroblast]] += _HIT_CHANCE*(1 + _FROSTBOLT_CRIT_DAMAGE*(crit_chance - _FROSTBOLT_CRIT_MOD))*(_FROSTBOLT_DAMAGE + _FROSTBOLT_MODIFIER*(plus_damage - _FROSTBOLT_PLUS))*_FROSTBOLT_OVERALL
            

        # scorch next
        scorcher = np.logical_not(np.logical_or(next_hit, pyro_array)) # scorch mage only
        scorch_array = np.logical_and(scorcher,
                                      np.logical_or(np.squeeze(scorch_count[cst]) < _SCORCH_STACK,
                                                    np.squeeze(scorch_time[cst]) < _MAX_SCORCH_REMAIN))
        scorch_array = np.logical_and(scorch_array, cast_copy != _CAST_SCORCH)
        if scorches:
            scorch_array = np.logical_or(scorch_array, cast_number[cst, next_hit] < _EXTRA_SCORCHES)
        scorch = np.where(scorch_array)[0]
        cast_timer[cst[scorch], next_hit[scorch]] = _SCORCH_CASTTIME + react_time[scorch]
        cast_type[cst[scorch], next_hit[scorch]] = _CAST_SCORCH

        # fireball next
        fireball = np.where(np.logical_not(np.logical_or(scorch_array, pyro_array)))[0]
        cast_timer[cst[fireball], next_hit[fireball]] = _FIREBALL_CASTTIME + react_time[fireball]
        cast_type[cst[fireball], next_hit[fireball]] = _CAST_FIREBALL
        
        spell_type[cst, next_hit] = cast_copy
        spell_timer[cst, next_hit] = _SPELL_TIME[cast_copy]
        cast_number[cst, next_hit] += 1

    spell_lands = np.where(np.logical_not(np.logical_or(np.logical_or(ig_array, se_array), cast_array)))[0]
    if spell_lands.size > 0:
        spl = still_going[spell_lands]
        next_hit = np.argmin(spell_timer[spl, :], axis=1)
        add_time = np.min(spell_timer[spl, :], axis=1, keepdims=True)
        running_time[spl] += add_time
        ignite_time[spl] -= add_time
        cast_timer[spl] -= add_time
        spell_timer[spl] -= add_time
        scorch_time[spl] -= add_time

        spell_copy = spell_type[spl, next_hit]

        if _LOG_SIM >= 0:
            if _LOG_SIM in spl:
                message = ' ({:6.2f}): player {:d} {:s} landed '
                sub_index = spl.tolist().index(_LOG_SIM)
                message = message.format(running_time[_LOG_SIM][0],
                                         next_hit[sub_index] + 1,
                                         _LOG_SPELL[spell_copy[sub_index]])
                message2 = 'misses         '

        for spell in range(_CASTS):
            
            is_spell = np.where(spell_copy == spell)[0]
            spell_hits = np.where(np.random.rand(is_spell.size) < _HIT_CHANCE)[0]
            if spell_hits.size > 0:

                sph = spl[is_spell][spell_hits]
                spell_damage = _SPELL_BASE[spell] + \
                               _SPELL_RANGE[spell]*np.random.rand(sph.size, 1) +\
                               _MULTIPLIER[spell]*plus_damage
                spell_damage *= (1.0 + 0.03*scorch_count[sph])*_DAMAGE_MULTIPLIER
                # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

                # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MECHANICS **
                ccrit_chance = crit_chance + _PER_COMBUSTION*comb_stack[sph, next_hit[is_spell][spell_hits]]*comb_left[sph, next_hit[is_spell][spell_hits]]
                crit_array = np.random.rand(sph.size) < ccrit_chance
                lcrits = np.where(crit_array)[0]
                crits = sph[lcrits]
                # refresh ignite to full 4 seconds
                ignite_time[crits] = _IGNITE_TIME
                # if we dont have a full stack
                mod_val = np.where(ignite_count[crits] < _IGNITE_STACK)[0]
                # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                ignite_value[crits[mod_val]] += _CRIT_DAMAGE*_IGNITE_DAMAGE*spell_damage[lcrits[mod_val]]
                # increment to max of five (will do nothing if alreeady at 5)
                ignite_count[crits] = np.minimum(ignite_count[crits] + 1, _IGNITE_STACK)
                damage[crits] += _CRIT_DAMAGE*spell_damage[lcrits]
                comb_left[crits, next_hit[is_spell][spell_hits][lcrits]] = np.maximum(comb_left[crits, next_hit[is_spell][spell_hits][lcrits]] - 1, 0)

                # normal hit
                nocrits = np.where(np.logical_not(crit_array))[0]
                damage[sph[nocrits]] += spell_damage[nocrits]

                if _LOG_SIM >= 0:
                    if _LOG_SIM in sph:
                        sub_index = sph.tolist().index(_LOG_SIM)
                        if _LOG_SIM in crits:
                            message2 = 'crits for {:4.0f} '.format(_CRIT_DAMAGE*spell_damage[sub_index][0])
                        else:
                            message2 = ' hits for {:4.0f} '.format(spell_damage[sub_index][0])

                # scorch
                if _IS_SCORCH[spell]:
                    scorch_time[sph] = _SCORCH_TIME
                    scorch_count[sph] = np.minimum(scorch_count[sph] + 1, _SCORCH_STACK)
                    
                comb_stack[sph, next_hit[is_spell][spell_hits]] += 1
                spell_timer[sph, next_hit[is_spell][spell_hits]] = _DURATION_AVERAGE

        # cast combustion before pyroblast (don't apply to scorch)
        if not early_combustion:
            if scorches:
                comb_array = cast_number[spl, next_hit] == _EXTRA_SCORCHES + 1
            else:
                comb_array = cast_number[spl, next_hit] == 1
            do_comb = np.where(comb_array)[0]
            comb_left[spl[do_comb], next_hit[do_comb]] = _COMBUSTIONS
            comb_stack[spl[do_comb], next_hit[do_comb]] = 0


        if _LOG_SIM >= 0:
            if _LOG_SIM in spl:
                sub_index = spl.tolist().index(_LOG_SIM)
                dam_done = ' {:7.0f}'.format(total_damage[_LOG_SIM][0] + damage[_LOG_SIM][0])
                message3 = _LOG_SPELL[cast_type[_LOG_SIM][next_hit[sub_index]]]
                message = message + message2 + 'next is ' + message3
                status = ' ic {:d} it {:4.2f} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d}'
                status = status.format(ignite_count[_LOG_SIM][0],
                                       max([ignite_time[_LOG_SIM][0], 0.0]),
                                       ignite_value[_LOG_SIM][0],
                                       scorch_count[_LOG_SIM][0],
                                       max([scorch_time[_LOG_SIM][0], 0.0]),
                                       comb_stack[_LOG_SIM][next_hit[sub_index]],
                                       comb_left[_LOG_SIM][next_hit[sub_index]])
                print(dam_done + message + status)

    
    return True

def get_damage(sp, crit, num_mages, rotation):
    arrays = {
            'total_damage': np.zeros((_SIM_SIZE, 1)),
            'ignite_count': np.zeros((_SIM_SIZE, 1)).astype(np.int32),
            'ignite_time': np.zeros((_SIM_SIZE, 1)),
            'ignite_value': np.zeros((_SIM_SIZE, 1)),
            'scorch_count': np.zeros((_SIM_SIZE, 1)).astype(np.int32),
            'scorch_time': np.zeros((_SIM_SIZE, 1)),
            'running_time': np.zeros((_SIM_SIZE, 1)),
            'cast_timer': np.abs(_INITIAL_SIGMA*np.random.randn(_SIM_SIZE, num_mages)),
            'cast_type': _CAST_SCORCH*np.ones((_SIM_SIZE, num_mages)).astype(np.int32),
            'comb_stack': np.zeros((_SIM_SIZE, num_mages)).astype(np.int32),
            'comb_left': np.zeros((_SIM_SIZE, num_mages)).astype(np.int32),
            'spell_timer': _DURATION_AVERAGE*np.ones((_SIM_SIZE, num_mages)),
            'spell_type': _CAST_SCORCH*np.ones((_SIM_SIZE, num_mages)).astype(np.int32),
            'cast_number': np.zeros((_SIM_SIZE, num_mages)).astype(np.int32),
            'duration': _DURATION_AVERAGE + _DURATION_SIGMA*np.random.randn(_SIM_SIZE, 1)}
    

    if _LOG_SIM >= 0:
        message = 'log for spell power = {:3.0f}, crit chance = {:2.0f}%, hit chance = {:2.0f}%:'
        message = message.format(sp, crit*100.0, _HIT_CHANCE*100.0)
        print(message)
        print('    KEY:')
        print('      ic = ignite stack size')
        print('      it = ignite time remaining')
        print('      ic = ignite damage per tick')
        print('      sc = scorch stack size')
        print('      st = scorch time remaining')
        print('      cs = combustion stack size (ignore if cl is 0)')
        print('      cl = combustion remaining crits')

    while advance(arrays, crit, sp, rotation):
        still_going = np.where(arrays['running_time'] < arrays['duration'])[0]
        arrays['total_damage'][still_going] += arrays['damage'][still_going]
    if _LOG_SIM >= 0:
        print('total damage = {:7.0f}'.format(arrays['total_damage'][_LOG_SIM][0]))

    return (arrays['total_damage']/arrays['duration']).mean()

if _DO_CRIT_SP_EQUIV:
    dcrit = 0.025
    dsp = 25.0
    factor = dsp/dcrit/100.0
    crit_chance = np.arange(_CRIT_START, _CRIT_END + _CRIT_STEP/2.0, _CRIT_STEP)
    sps = np.arange(_SP_START, _SP_END + _SP_STEP/2.0, _SP_STEP)
    rotation = _FIRST_PYROBLAST|_INITIAL_ONE|_COMBUSTION_LATER
    t0 = time.time()
    for num_mages in range(_MAGES_START, _MAGES_END + 1):
        conversions = []
        for sp in sps:
            conversion = []
            for crit in crit_chance:
                print('On mage {:d} SP {:3.0f} Crit {:4.2f}'.format(num_mages, sp, crit))
                dm_sp = get_damage(sp - dsp, crit, num_mages, rotation)
                print('    ', dm_sp)
                dp_sp = get_damage(sp + dsp, crit, num_mages, rotation)
                print('    ', dp_sp)
                dm_crit = get_damage(sp, crit - dcrit, num_mages, rotation)
                print('    ', dm_crit)
                dp_crit = get_damage(sp, crit + dcrit, num_mages, rotation)
                print('    ', dp_crit)

                print('  time = {:5.0f} {:f}'.format(time.time() - t0, factor*(dp_crit - dm_crit)/(dp_sp - dm_sp)))
                conversion.append(factor*(dp_crit - dm_crit)/(dp_sp - dm_sp))
        
            conversions.append(conversion)

        colors = ['indigo', 'purple', 'darkblue', 'royalblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
        plt.close('all')
        fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
        plt.title('{:d} mages, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(num_mages, _HIT_CHANCE*100.0, _SIM_SIZE, _DURATION_AVERAGE))
        plt.xlabel('Crit Chance (percent)')
        plt.ylabel('SP ratio')
        plt.xlim(0, 75.0)
        plt.ylim(0, 5 + int(np.array(conversions).max()/5)*5)

        for color, spell_power, conv in zip(colors, sps, conversions):
            plt.plot(100.0*np.array(crit_chance), np.array(conv), label='{:3.0f} SP'.format(spell_power), color=color, marker='.')
        plt.legend()
        plt.grid()
        savefile = 'sp_equiv_plots\sp_equiv_{:d}_mages_{:2.0f}_{:d}.png'.format(num_mages, _HIT_CHANCE*100.0, _SIM_SIZE)
        os.makedirs('sp_equiv_plots', exist_ok=True)
        plt.savefig(savefile)

if _DO_ROTATION_SEARCH:
    
    desc = ['(frostbolt+fireball average damage)/(pyroblast average damage)',
            '(cast two scorches first)/(cast one scorch first)',
            '(cast combustion before scorch)/(cast combustion after scorch)']
    first_rotation = [_FIRST_PYROBLAST, _INITIAL_ONE, _COMBUSTION_LATER]
    second_rotation = [_FIRST_FROSTBOLT, _INITIAL_TWO, _COMBUSTION_FIRST]
    
    for index, (rotation1, rotation2, description) in enumerate(zip(first_rotation, second_rotation, desc)):
        crit_chance = np.arange(_CRIT_START, _CRIT_END + _CRIT_STEP/2.0, _CRIT_STEP)
        nmages = range(_MAGES_START, _MAGES_END + 1)
        compares = []
        for num_mages in nmages:
            compare = []
            for crit in crit_chance:
                dm_1 = get_damage(_DAMAGE, crit, num_mages, rotation1)
                dm_2 = get_damage(_DAMAGE, crit, num_mages, rotation2)
            
                compare.append(dm_2/dm_1)
                print('On {:} num mages {:d} Crit {:4.2f} {:6.1f} {:6.1f}'.format(index, num_mages, crit, dm_1, dm_2))
            compares.append(compare)

        colors = ['indigo', 'royalblue', 'skyblue', 'lime', 'gold', 'darkorange', 'firebrick']
        plt.close('all')
        fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
        plt.title('{:3.0f} spell damage, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(_DAMAGE, _HIT_CHANCE*100.0, _SIM_SIZE, _DURATION_AVERAGE))
        plt.xlabel('Crit Chance (percent)')
        plt.ylabel(description)
        plt.xlim(0, 75.0)

        for color, num_mages, comp in zip(colors, nmages, compares):
            plt.plot(100.0*np.array(crit_chance), np.array(comp), label='{:d} mages'.format(num_mages), color=color, marker='.')
        plt.legend()
        plt.grid()
        savefile = 'rotation_plots\comparison_{:d}.png'.format(index)
        os.makedirs('rotation_plots', exist_ok=True)
        plt.savefig(savefile)

if _DO_DPS_PER_MAGE:

    nmages = range(_MAGES_START - 2, _MAGES_END + 1)
    rotation = _FIRST_PYROBLAST|_INITIAL_ONE|_COMBUSTION_LATER
    
    crit_chance = np.arange(_CRIT_START, _CRIT_END + _CRIT_STEP/2.0, _CRIT_STEP)
    for sp in np.arange(_SP_START, _SP_END + _SP_STEP/2.0, 2.0*_SP_STEP):
        
        damages = []
        for crit in crit_chance:
            damage = []
            for num_mages in nmages:
                print('On {:3.0f} {:2.0f} {:d}'.format(sp, crit*100.0, num_mages))
                
                d0 = get_damage(sp, crit, num_mages, rotation)
                damage.append(d0/num_mages)
                
            damages.append(damage)
            
        colors = ['indigo', 'purple', 'darkblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
        plt.close('all')
        fig = plt.figure(figsize=(10.0, 7.0), dpi=200)
        plt.title('{:3.0f} spell damage, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(sp, _HIT_CHANCE*100.0, _SIM_SIZE, _DURATION_AVERAGE))
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

#d0 = get_damage(700, 0.45, 6, 0)