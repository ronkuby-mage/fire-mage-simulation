import numpy as np
from constants import Constant, init_arrays, log_message

def advance(arrays, plus_damage, hit_chance, crit_chance, rotation, sim_size):
    C = Constant(sim_size=sim_size)

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

    num_mages = cast_timer.shape[1]
    extra_scorches = C._EXTRA_SCORCHES[num_mages]

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

        if C._LOG_SIM >= 0:
            if  C._LOG_SIM in cst:
                message = '         ({:6.2f}): player {:d} finished casting {:s}'
                sub_index = cst.tolist().index( C._LOG_SIM)
                message = message.format(running_time[ C._LOG_SIM][0],
                                         next_hit[sub_index] + 1,
                                         C._LOG_SPELL[cast_copy[sub_index]])
                print(message)

        # special spell next
        special_array = cast_number[cst, next_hit] == extra_scorches
        special = np.where(special_array)[0]
        if rotation == C._FIRE_BLAST:
            cast_timer[cst[special], next_hit[special]] = epsilon + react_time[special]
            cast_type[cst[special], next_hit[special]] = C._CAST_FIRE_BLAST
        elif rotation == C._FROSTBOLT:
            cast_timer[cst[special], next_hit[special]] = C._PYROBLAST_CASTTIME + react_time[special]
            cast_type[cst[special], next_hit[special]] = C._CAST_PYROBLAST
        else:
            cast_timer[cst[special], next_hit[special]] = C._FIREBALL_CASTTIME + C._FROSTBOLT_CASTTIME + react_time[special]
            cast_type[cst[special], next_hit[special]] = C._CAST_FIREBALL
            damage[cst[special]] += hit_chance*(1 + C._FROSTBOLT_CRIT_DAMAGE*(crit_chance - C._FROSTBOLT_CRIT_MOD))*(C._FROSTBOLT_DAMAGE + C._FROSTBOLT_MODIFIER*(plus_damage - C._FROSTBOLT_PLUS))*C._FROSTBOLT_OVERALL

        # scorch next
        scorcher = np.logical_not(np.logical_or(next_hit, special_array)) # scorch mage only
        scorch_array = np.logical_and(scorcher,
                                      np.logical_or(np.squeeze(scorch_count[cst]) < C._SCORCH_STACK,
                                                    np.squeeze(scorch_time[cst]) < C._MAX_SCORCH_REMAIN))
        scorch_array = np.logical_and(scorch_array, cast_copy != C._CAST_SCORCH)
        scorch_array = np.logical_and(scorch_array, cast_number[cst, next_hit] > extra_scorches + 1)
        # now scorch array is just for scorcher
        scorch_array = np.logical_or(scorch_array, cast_number[cst, next_hit] < extra_scorches)
        # now everyone
        scorch = np.where(scorch_array)[0]
        cast_timer[cst[scorch], next_hit[scorch]] = C._SCORCH_CASTTIME + react_time[scorch]
        cast_type[cst[scorch], next_hit[scorch]] = C._CAST_SCORCH

        # fireball next
        fireball = np.where(np.logical_not(np.logical_or(scorch_array, special_array)))[0]
        cast_timer[cst[fireball], next_hit[fireball]] = C._FIREBALL_CASTTIME + react_time[fireball]
        cast_type[cst[fireball], next_hit[fireball]] = C._CAST_FIREBALL

        spell_type[cst, next_hit] = cast_copy
        spell_timer[cst, next_hit] = C._SPELL_TIME[cast_copy]
        if rotation == C._FIRE_BLAST:
            gcd = np.where(cast_number[cst, next_hit] == extra_scorches + 1)[0]
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
            spell_hits = np.where(np.random.rand(is_spell.size) < hit_chance)[0]
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
        comb_array = cast_number[spl, next_hit] == int(rotation == C._FIRE_BLAST) + extra_scorches + 1
        do_comb = np.where(comb_array)[0]
        if  C._LOG_SIM >= 0:
            cmessage = ''
            if C._LOG_SIM in spl[do_comb]:
                sub_index = spl[do_comb].tolist().index(C._LOG_SIM)
                cmessage = '         (------): combustion cast by player {:d}'.format(next_hit[do_comb[sub_index]] + 1)
        comb_left[spl[do_comb], next_hit[do_comb]] = C._COMBUSTIONS
        comb_stack[spl[do_comb], next_hit[do_comb]] = 0


        if  C._LOG_SIM >= 0:
            if C._LOG_SIM in spl:
                if cmessage:
                    print(cmessage)
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
    
def get_damage(sp, hit, crit, num_mages, rotation, response, sim_size):
    C = Constant(sim_size=sim_size)
    arrays = init_arrays(C, num_mages, response)
    if  C._LOG_SIM >= 0:
        log_message(sp, hit, crit)

    while advance(arrays, sp, hit, crit, rotation, sim_size):
        still_going = np.where(arrays['running_time'] < arrays['duration'])[0]
        arrays['total_damage'][still_going] += arrays['damage'][still_going]
    if  C._LOG_SIM >= 0:
        print('total damage = {:7.0f}'.format(arrays['total_damage'][ C._LOG_SIM][0]))

    return (arrays['total_damage']/arrays['duration']).mean()

def get_crit_damage_diff(sp, hit, crit, num_mages, rotation, response, sim_size):
    dcrit = 0.025
    dsp = 25.0
    factor = dsp/dcrit/100.0

    dm_sp = get_damage(sp - dsp, hit, crit, num_mages, rotation, response, sim_size)
    dp_sp = get_damage(sp + dsp, hit, crit, num_mages, rotation, response, sim_size)
    dm_crit = get_damage(sp, hit, crit - dcrit, num_mages, rotation, response, sim_size)
    dp_crit = get_damage(sp, hit, crit + dcrit, num_mages, rotation, response, sim_size)

    return factor*(dp_crit - dm_crit)/(dp_sp - dm_sp)

def get_hit_damage_diff(sp, hit, crit, num_mages, rotation, response, sim_size):
    dhit = 0.01
    dsp = 25.0
    factor = dsp/dhit/100.0

    dm_sp = get_damage(sp - dsp, hit, crit, num_mages, rotation, response, sim_size)
    dp_sp = get_damage(sp + dsp, hit, crit, num_mages, rotation, response, sim_size)
    dm_hit = get_damage(sp, hit - dhit, crit, num_mages, rotation, response, sim_size)
    dp_hit = get_damage(sp, hit + dhit, crit, num_mages, rotation, response, sim_size)

    return factor*(dp_hit - dm_hit)/(dp_sp - dm_sp)

