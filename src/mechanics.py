import numpy as np
import constants

def subtime(C, arrays, sub, add_time):
    arrays['global']['running_time'][sub] += add_time
    arrays['player']['cast_timer'][sub, :] -= add_time[:, None]
    arrays['player']['spell_timer'][sub, :] -= add_time[:, None]
    arrays['boss']['ignite_timer'][sub] -= add_time
    arrays['boss']['tick_timer'][sub] -= add_time
    arrays['boss']['scorch_timer'][sub] -= add_time
    for buff in range(C._BUFFS):
        arrays['player']['buff_timer'][buff][sub, :] -= add_time[:, None]
    for debuff in range(C._DEBUFFS):
        arrays['boss']['debuff_timer'][debuff][sub] -= add_time

    return

def do_cast(C, arrays, still_going, cast_array):
    cast_ends = np.where(cast_array)[0]
    if cast_ends.size > 0:
        cst = still_going[cast_ends]
        next_hit = np.argmin(arrays['player']['cast_timer'][cst, :], axis=1)
        add_time = np.min(arrays['player']['cast_timer'][cst, :], axis=1)
        subtime(C, arrays, cst, add_time)

        if C._LOG_SIM >= 0:
            if C._LOG_SIM in cst:
                message = '         ({:6.2f}): player {:d} finished casting {:s}'
                sub_index = cst.tolist().index( C._LOG_SIM)
                message = message.format(arrays['global']['running_time'][C._LOG_SIM],
                                         next_hit[sub_index] + 1,
                                         C._LOG_SPELL[arrays['player']['cast_type'][cst[sub_index], next_hit[sub_index]]])
                print(message)

        # transfer to spell
        instant_array = arrays['player']['cast_type'][cst, next_hit] >= C._CAST_GCD
        no_instant = np.where(np.logical_not(instant_array))[0]
        arrays['player']['spell_type'][cst[no_instant], next_hit[no_instant]] = arrays['player']['cast_type'][cst[no_instant], next_hit[no_instant]]
        arrays['player']['spell_timer'][cst[no_instant], next_hit[no_instant]] = C._SPELL_TIME[arrays['player']['cast_type'][cst[no_instant], next_hit[no_instant]]]

        # apply instant spells
        combustion = np.where(arrays['player']['cast_type'][cst, next_hit] == C._CAST_COMBUSTION)[0]
        arrays['player']['comb_left'][cst[combustion], next_hit[combustion]] = C._COMBUSTIONS
        arrays['player']['comb_stack'][cst[combustion], next_hit[combustion]] = 0
        arrays['player']['comb_avail'][cst[combustion], next_hit[combustion]] -= 1

        for buff in range(C._BUFFS):
            tbuff = np.where(arrays['player']['cast_type'][cst, next_hit] == C._BUFF_CAST_TYPE[buff])[0]
            arrays['player']['buff_timer'][buff][cst[tbuff], next_hit[tbuff]] = C._BUFF_DURATION[buff]
            arrays['player']['buff_avail'][buff][cst[tbuff], next_hit[tbuff]] -= 1

        # determine gcd        
        gcd_array = arrays['player']['gcd'][cst, next_hit] > 0.0
        yes_gcd = np.where(gcd_array)[0]
        no_gcd = np.where(np.logical_not(gcd_array))[0]
        
        # push gcd
        arrays['player']['cast_type'][cst[yes_gcd], next_hit[yes_gcd]] = C._CAST_GCD
        arrays['player']['cast_timer'][cst[yes_gcd], next_hit[yes_gcd]] =\
            arrays['player']['gcd'][cst[yes_gcd], next_hit[yes_gcd]]
        arrays['player']['gcd'][cst[yes_gcd], next_hit[yes_gcd]] = 0.0

        # inc cast number
        arrays['global']['decision'][cst[yes_gcd]] = False
        arrays['global']['decision'][cst[no_gcd]] = True
        arrays['player']['cast_number'][cst[no_gcd], next_hit[no_gcd]] += 1 # attempt at batching

def do_spell(C, arrays, still_going, spell_array):
    epsilon = 1.0e-6
    
    spell_lands = np.where(spell_array)[0]
    if spell_lands.size > 0:
        spl = still_going[spell_lands]
        lnext_hit = np.argmin(arrays['player']['spell_timer'][spl, :], axis=1)
        add_time = np.min(arrays['player']['spell_timer'][spl, :], axis=1)
        subtime(C, arrays, spl, add_time)

        # reset timer
        arrays['player']['spell_timer'][spl, lnext_hit] = C._LONG_TIME

        if C._LOG_SIM >= 0:
            if C._LOG_SIM in spl:
                message = ' ({:6.2f}): player {:d} {:s} landed '
                sub_index = spl.tolist().index( C._LOG_SIM)
                message = message.format(arrays['global']['running_time'][C._LOG_SIM],
                                         lnext_hit[sub_index] + 1,
                                         C._LOG_SPELL[arrays['player']['spell_type'][C._LOG_SIM, lnext_hit[sub_index]]])
                message2 = 'misses         '

        spell_hits = np.where(np.random.rand(spell_lands.size) < arrays['player']['hit_chance'][spl, lnext_hit])[0]
        if spell_hits.size > 0:

            sph = spl[spell_hits]
            next_hit = lnext_hit[spell_hits]
            spell_type = arrays['player']['spell_type'][sph, next_hit]

            spell_damage = C._SPELL_BASE[spell_type] + \
                           C._SPELL_RANGE[spell_type]*np.random.rand(sph.size) +\
                           C._SP_MULTIPLIER[spell_type]*arrays['player']['spell_power'][sph, next_hit]
            spell_damage *= C._COE_MULTIPLIER*C._DAMAGE_MULTIPLIER[spell_type] # CoE + talents
            scorch = C._IS_FIRE[spell_type]*C._SCORCH_MULTIPLIER*arrays['boss']['scorch_count'][sph]
            spell_damage *= 1.0 + scorch*(arrays['boss']['scorch_timer'][sph] > 0.0).astype(np.float)
            pi = (arrays['player']['buff_timer'][C._BUFF_POWER_INFUSION][sph, next_hit] > 0.0).astype(np.float)
            spell_damage *= 1.0 + C._POWER_INFUSION*pi
            spell_damage *= C._DMF_BUFF
            arrays['global']['damage'][sph] += spell_damage
            # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

            # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MECHANICS **
            comb_crit = C._PER_COMBUSTION*arrays['player']['comb_stack'][sph, next_hit]
            comb_crit *= (arrays['player']['comb_left'][sph, next_hit] > 0).astype(np.float)
            comb_crit *= C._IS_FIRE[spell_type]
            crit_chance = arrays['player']['crit_chance'][sph, next_hit] + comb_crit + C._INCIN_BONUS[spell_type]
            crit_array = np.random.rand(sph.size) < crit_chance

            ignite_array = crit_array & C._IS_FIRE[spell_type].astype(np.bool)
            lcl_icrits = np.where(ignite_array)[0]
            gbl_icrits = sph[lcl_icrits]
            inext_hit = next_hit[lcl_icrits]
            
            # remove ignite if expired
            rem_val = np.where(arrays['boss']['ignite_timer'][gbl_icrits] <= 0.0)[0]
            arrays['boss']['ignite_count'][gbl_icrits[rem_val]] = 0
            arrays['boss']['ignite_value'][gbl_icrits[rem_val]] = 0.0
            
            # refresh ignite to full 4 seconds
            arrays['boss']['ignite_timer'][gbl_icrits] = C._IGNITE_TIME + epsilon
            
            # if we dont have a full stack
            mod_val = np.where(arrays['boss']['ignite_count'][gbl_icrits] < C._IGNITE_STACK)[0]
            # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
            arrays['boss']['ignite_value'][gbl_icrits[mod_val]] += (1.0 + C._ICRIT_DAMAGE)*C._IGNITE_DAMAGE*spell_damage[lcl_icrits[mod_val]]
            arrays['boss']['ignite_multiplier'][gbl_icrits[mod_val]] = C._DMF_BUFF*(1.0 + C._POWER_INFUSION*pi[lcl_icrits[mod_val]])

            # first in stack, set the tick
            mod_val2 = np.where(arrays['boss']['ignite_count'][gbl_icrits] == 0)[0]
            arrays['boss']['tick_timer'][gbl_icrits[mod_val2]] = C._IGNITE_TICK

            # increment to max of five (will do nothing if already at 5)
            arrays['boss']['ignite_count'][gbl_icrits] = np.minimum(arrays['boss']['ignite_count'][gbl_icrits] + 1, C._IGNITE_STACK)

            # add crit to damage
            arrays['global']['damage'][gbl_icrits] += C._ICRIT_DAMAGE*spell_damage[lcl_icrits]
            
            # remove from combustion
            arrays['player']['comb_left'][gbl_icrits, inext_hit] = np.maximum(arrays['player']['comb_left'][gbl_icrits, inext_hit] - 1, 0)

            # normal crit
            lcl_crits = np.where(crit_array & np.logical_not(C._IS_FIRE[spell_type]))[0]
            arrays['global']['damage'][sph[lcl_crits]] += C._CRIT_DAMAGE*spell_damage[lcl_crits]

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
            scorch_out = sph[np.where(arrays['boss']['scorch_timer'][sph] <= 0.0)[0]]
            arrays['boss']['scorch_count'][scorch_out] = 0
            
            scorch = sph[np.where(C._IS_SCORCH[spell_type])[0]]
            arrays['boss']['scorch_timer'][scorch] = C._SCORCH_TIME
            arrays['boss']['scorch_count'][scorch] = np.minimum(arrays['boss']['scorch_count'][scorch] + 1, C._SCORCH_STACK)
                    
            fire = np.where(C._IS_FIRE[spell_type])[0]
            arrays['player']['comb_stack'][sph[fire], next_hit[fire]] += 1

        if C._LOG_SIM >= 0:
            if C._LOG_SIM in spl:
                sub_index = spl.tolist().index(C._LOG_SIM)
                dam_done = ' {:7.0f}'.format(arrays['global']['total_damage'][C._LOG_SIM] + arrays['global']['damage'][C._LOG_SIM])
                message3 = C._LOG_SPELL[arrays['player']['cast_type'][C._LOG_SIM][lnext_hit[sub_index]]]
                message = message + message2 + 'next is ' + message3
                status = ' ic {:d} it {:4.2f} in {:s} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d}'
                ival = arrays['boss']['tick_timer'][C._LOG_SIM]
                istat = '{:4.2f}'.format(ival) if ival > 0.0 and ival <= 2.0 else ' off'
                status = status.format(arrays['boss']['ignite_count'][C._LOG_SIM],
                                       max([arrays['boss']['ignite_timer'][C._LOG_SIM], 0.0]),
                                       istat,
                                       arrays['boss']['ignite_value'][C._LOG_SIM],
                                       arrays['boss']['scorch_count'][C._LOG_SIM],
                                       max([arrays['boss']['scorch_timer'][C._LOG_SIM], 0.0]),
                                       arrays['player']['comb_stack'][C._LOG_SIM, lnext_hit[sub_index]],
                                       arrays['player']['comb_left'][C._LOG_SIM, lnext_hit[sub_index]])
                print(dam_done + message + status)

def do_tick(C, arrays, still_going, tick_array):
    tick_hits = np.where(tick_array)[0]
    if tick_hits.size > 0:
        tic = still_going[tick_hits]
        add_time = arrays['boss']['tick_timer'][tic]
        subtime(C, arrays, tic, add_time)
        
        ignite_expire = arrays['boss']['ignite_timer'][tic] <= 0.0
        yes_expire = tic[np.where(ignite_expire)[0]]
        arrays['boss']['tick_timer'][yes_expire] = C._LONG_TIME
        
        no_expire = tic[np.where(np.logical_not(ignite_expire))[0]]
        arrays['boss']['tick_timer'][no_expire] = C._IGNITE_TICK

        scorch = C._SCORCH_MULTIPLIER*arrays['boss']['scorch_count'][no_expire]
        multiplier = C._COE_MULTIPLIER*arrays['boss']['ignite_multiplier'][no_expire]
        multiplier *= 1.0 + scorch*(arrays['boss']['scorch_timer'][no_expire] > 0.0).astype(np.float)
        arrays['global']['damage'][no_expire] += multiplier*arrays['boss']['ignite_value'][no_expire]
        if C._LOG_SIM >= 0:
            if C._LOG_SIM in no_expire:
                sub_index = no_expire.tolist().index(C._LOG_SIM)
                message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                print(message.format(arrays['global']['total_damage'][C._LOG_SIM] + arrays['global']['damage'][C._LOG_SIM],
                                     arrays['global']['running_time'][C._LOG_SIM],
                                     multiplier[sub_index]*arrays['boss']['ignite_value'][C._LOG_SIM]))

def advance(C, arrays):
    arrays['global']['damage'] = np.zeros(C._SIM_SIZE)

    going_array = (arrays['global']['running_time'] < arrays['global']['duration'])
    going_array &= np.logical_not(arrays['global']['decision'])
    still_going = np.where(going_array)[0]
    if still_going.size == 0:
        return False

    # cast finished
    cast_timer = np.copy(np.min(arrays['player']['cast_timer'][still_going, :], axis=1))
    spell_timer = np.copy(np.min(arrays['player']['spell_timer'][still_going, :], axis=1))
    tick_timer = np.copy(arrays['boss']['tick_timer'][still_going])
    cast_array = (cast_timer < spell_timer) & (cast_timer < tick_timer)
    do_cast(C, arrays, still_going, cast_array)

    # spell hits
    spell_array = np.logical_not(cast_array) & (spell_timer < tick_timer)
    do_spell(C, arrays, still_going, spell_array)

    tick_array = np.logical_not(cast_array | spell_array)
    do_tick(C, arrays, still_going, tick_array)
    
    return True

def get_decisions(C, arrays):
    still_going = np.where(arrays['global']['running_time'] < arrays['global']['duration'])[0]
    next_hit = np.argmin(arrays['player']['cast_timer'][still_going, :], axis=1)
    
    react_time = np.abs(C._CONTINUING_SIGMA*np.random.randn(still_going.size))    

    mqg = (arrays['player']['buff_timer'][C._BUFF_MQG][still_going, next_hit] > 0.0).astype(np.float)    
    num_mages = arrays['player']['cast_timer'].shape[1]

    # begin decision -- filling cast_type and cast_timer    
    aut_scorch = arrays['player']['cast_number'][still_going, next_hit] == C._SCORCHES[num_mages]
    man_scorch = arrays['boss']['scorch_timer'][still_going] < C._MAX_SCORCH_REMAIN
    man_scorch |= arrays['boss']['scorch_count'][still_going] < C._SCORCH_STACK
    man_scorch &= (arrays['player']['cast_number'][still_going, next_hit] >= C._SCORCHES[num_mages] + 4)
    man_scorch &= np.logical_not(next_hit)
    do_scorch = aut_scorch | man_scorch
    scorch = np.where(do_scorch)[0]
    arrays['player']['cast_type'][still_going[scorch], next_hit[scorch]] = C._CAST_SCORCH
    arrays['player']['cast_timer'][still_going[scorch], next_hit[scorch]] = C._CAST_TIME[C._CAST_SCORCH]/(1.0 + C._MQG*mqg[scorch]) + react_time[scorch]
    
    do_fire_blast = arrays['player']['cast_number'][still_going, next_hit] == C._SCORCHES[num_mages] + 1
    fire_blast = np.where(do_fire_blast)[0]
    arrays['player']['cast_type'][still_going[fire_blast], next_hit[fire_blast]] = C._CAST_FIRE_BLAST
    arrays['player']['cast_timer'][still_going[fire_blast], next_hit[fire_blast]] = C._CAST_TIME[C._CAST_FIRE_BLAST] + react_time[fire_blast]
    
    do_combustion = arrays['player']['cast_number'][still_going, next_hit] == C._SCORCHES[num_mages] + 2
    combustion = np.where(do_combustion)[0]
    arrays['player']['cast_type'][still_going[combustion], next_hit[combustion]] = C._CAST_COMBUSTION
    arrays['player']['cast_timer'][still_going[combustion], next_hit[combustion]] = 0.0

    do_fireball = np.logical_not(do_scorch|do_fire_blast|do_combustion)
    fireball = np.where(do_fireball)[0]
    arrays['player']['cast_type'][still_going[fireball], next_hit[fireball]] = C._CAST_FIREBALL
    arrays['player']['cast_timer'][still_going[fireball], next_hit[fireball]] = C._CAST_TIME[C._CAST_FIREBALL]/(1.0 + C._MQG*mqg[scorch]) + react_time[fireball]
    
    # end decision
    gcd = np.where(arrays['player']['cast_type'][still_going, next_hit] < C._CAST_GCD)[0]
    arrays['player']['gcd'][still_going[gcd], next_hit[gcd]] = np.maximum(0.0, C._GLOBAL_COOLDOWN + react_time[gcd] - arrays['player']['cast_timer'][still_going[gcd], next_hit[gcd]])
    
    arrays['global']['decision'] = np.zeros(arrays['global']['decision'].shape, dtype=np.bool)

def get_damage(sp, hit, crit, num_mages, response, sim_size):
    C = constants.Constant(sim_size=sim_size)
    arrays = constants.init_const_arrays(C, sp, hit, crit, num_mages, response)
    if C._LOG_SIM >= 0:
        constants.log_message(sp, hit, crit)
    while True:
        while advance(C, arrays):
            still_going = np.where(arrays['global']['running_time'] < arrays['global']['duration'])[0]
            arrays['global']['total_damage'][still_going] += arrays['global']['damage'][still_going]
        if still_going.size == 0:
            break
        get_decisions(C, arrays)
        
    if C._LOG_SIM >= 0:
        print('total damage = {:7.0f}'.format(arrays['global']['total_damage'][ C._LOG_SIM]))

    return (arrays['global']['total_damage']/arrays['global']['duration']).mean()

def get_crit_damage_diff(sp, hit, crit, num_mages, response, sim_size):
    dcrit = 0.025
    dsp = 25.0
    factor = dsp/dcrit/100.0

    dm_sp = get_damage(sp - dsp, hit, crit, num_mages, response, sim_size)
    dp_sp = get_damage(sp + dsp, hit, crit, num_mages, response, sim_size)
    dm_crit = get_damage(sp, hit, crit - dcrit, num_mages, response, sim_size)
    dp_crit = get_damage(sp, hit, crit + dcrit, num_mages, response, sim_size)

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

