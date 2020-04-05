import os
import numpy as np
import itertools
from multiprocessing import Pool
import time
import pickle
from constants import Constant
import plots
from mechanics import get_damage, get_crit_damage_diff

## run parameters
_DO_ROTATION_SEARCH = False
_DO_RESPONSE_SEARCH = False
_DO_CRIT_SP_EQUIV = True
#_DO_DPS_PER_MAGE = False

def fill_args(args, crit_chance, nmages):
    for index, arg in enumerate(args):
        filename = '../savestates/rotation_{:3.0f}_{:2.0f}.dat'.format(arg[0], 100.0*arg[1])
        with open(filename, 'rb') as fid:
            sim_size = pickle.load(fid)
            rotation_map = pickle.load(fid)
        cindex = crit_chance.tolist().index(arg[2])
        mindex = nmages.tolist().index(arg[3])
        rotation = rotation_map[cindex, mindex]
        targ = list(arg)
        targ[4] = rotation
        args[index] = tuple(targ)

    return sim_size

def main():
    C = Constant()
    t0 = time.time()

    spell_damage = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, C._SP_STEP)
    hit_chance = np.arange(C._HIT_START, C._HIT_END + C._HIT_STEP/2.0, C._HIT_STEP)
    crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
    nmages = np.arange(1, C._MAGES_END + 1, dtype=np.int32)

    for hit in hit_chance:
        for spd in spell_damage:
            # First look through the 3 {scorch -> spell -> fireball} rotations
            # where spell can be fire blast, frostbolt, or pyroblast.
            # The best rotation is recorded for each combination of:
            #   * spell power
            #   * hit chance
            #   * crit chance
            #   * number of mages
            filename = '../savestates/rotation_{:3.0f}_{:2.0f}.dat'.format(spd, 100.0*hit)
            if _DO_ROTATION_SEARCH:
                sps = np.array([spd])
                hits = np.array([hit])
                sim_size = np.array([C._ROTATION_SIMSIZE]).astype(np.int32)
                big_desc = ['Damage(frostbolt rotation)/Damage(pyroblast rotation)',
                            'Damage(fire blast rotation)/Damage(pyroblast rotation)']
                big_fn_desc = ['frostbolt', 'fire_blast']
                big_rotations = [C._FROSTBOLT, C._FIRE_BLAST]
            
                if _DO_RESPONSE_SEARCH:
                    responses = np.arange(0.0, 3.05, 0.10)
                else:
                    responses = np.array([C._INITIAL_SIGMA])
        
                print('Hit = {:2.0f} spd = {:3.0f}'.format(100.0*hit, spd))
                rotation_map = -np.ones((len(crit_chance), len(nmages)), dtype=np.int16)
                damage_map = np.zeros((len(crit_chance), len(nmages)))
                for rindex, (rotation, desc, fn_desc) in enumerate(zip(big_rotations, big_desc, big_fn_desc)):
                    rotations = np.array([0, rotation], dtype=np.int32)
            
                    args = itertools.product(sps, hits, crit_chance, nmages, rotations, responses, sim_size)
        
                    largs = [*args]
                    print('  Starting {:d} sims with samples {:d} each.  Estimated run time is {:.2f} minutes.'.format(len(largs), sim_size[0], 5e-5*len(largs)*sim_size[0]/60.0))
                    with Pool() as p:
                        out = np.array(p.starmap(get_damage, largs)).reshape((len(sps), len(hits), len(crit_chance), len(nmages), len(rotations), len(responses), len(sim_size)))

                    if _DO_RESPONSE_SEARCH:
                        resp_index = np.argmin(np.abs(responses  - C._INITIAL_SIGMA))
                        dd = [np.squeeze(out[:, :, :, :, 0, resp_index]),
                              np.squeeze(out[:, :, :, :, 1, resp_index])]
                    else:
                        dd = [np.squeeze(out[:, :, :, :, 0, :]), 
                              np.squeeze(out[:, :, :, :, 1, :])]
                    for index, damage in zip([0, rotation], dd):
                        replacer = np.where(damage > damage_map)
                        damage_map[replacer] = damage[replacer]
                        rotation_map[replacer] = index

                    if _DO_RESPONSE_SEARCH:
                        for index, crit in enumerate(crit_chance):
                            damages = np.squeeze(out[:, :, index, :, 1, :])/np.squeeze(out[:, :, index, :, 0, :])
                            plots.plot_response(responses, damages, spd, hit, crit, fn_desc, desc, nmages, sim_size[0], C._DURATION_AVERAGE)

                    os.makedirs('../savestates/', exist_ok=True)
                    with open(filename, 'wb') as fid:
                        pickle.dump(sim_size, fid)
                        pickle.dump(rotation_map, fid)
                else:
                    with open(filename, 'rb') as fid:
                        sim_size = pickle.load(fid)
                        rotation_map = pickle.load(fid)
                        
                plots.plot_rotation(crit_chance, nmages, rotation_map, spd, hit, sim_size[0], C._DURATION_AVERAGE, C._INITIAL_SIGMA)

        if _DO_ROTATION_SEARCH:
            print('{:3.0f} rotation/spread complete after {:.0f} seconds'.format(spd, time.time() - t0))

        # Calculate spell power to crit chance equivalency
        # Use the previously computed best rotation for each parameter set
        for num_mages in nmages:
            filename = '../savestates/rotation_{:2.0f}_{:d}.dat'.format(100.0*hit, num_mages)
            if _DO_CRIT_SP_EQUIV:
                hits = np.array([hit])
                mages = np.array([num_mages])
                sim_size = C._CRIT_SIMSIZE*nmages.astype(np.float32).mean()/num_mages
                sim_size = np.array([sim_size]).astype(np.int32)
                rotations = np.array([0]).astype(np.int16)
                responses = np.array([C._INITIAL_SIGMA])

                args = itertools.product(spell_damage, hits, crit_chance, mages, rotations, responses, sim_size)
                largs = [*args]
                fill_args(largs, crit_chance, nmages)

                print('Hit = {:2.0f} # mages = {:d}'.format(100.0*hit, num_mages))

                lsim_size = 0
                if os.path.exists(filename):
                    with open(filename, 'rb') as fid:
                        lsim_size = pickle.load(fid)[0]
                        conversions = pickle.load(fid)
                if lsim_size != sim_size[0]:
                    print('  Starting {:d} sims with {:d} mages and samples {:d} each.  Estimated run time is {:.2f} minutes.'.format(len(largs), num_mages, sim_size[0], 8e-5*len(largs)*num_mages*sim_size[0]/60.0))
                    with Pool() as p:
                        out = np.array(p.starmap(get_crit_damage_diff, largs)).reshape((len(spell_damage), len(hits), len(crit_chance), len(mages), len(rotations), len(responses), len(sim_size)))
                    conversions = np.squeeze(out)

                os.makedirs('../savestates/', exist_ok=True)
                with open(filename, 'wb') as fid:
                    pickle.dump(sim_size, fid)
                    pickle.dump(conversions, fid)
            else:
                with open(filename, 'rb') as fid:
                    sim_size = pickle.load(fid)
                    conversions = pickle.load(fid)

            plots.plot_crit_equiv(spell_damage, crit_chance, conversions, hit, num_mages, sim_size[0], C._DURATION_AVERAGE)

    os.makedirs('../data/', exist_ok=True)
    fid = open('../data/crit_equiv.csv', 'wt')
    fid.write('spell damage,hit chance,crit chance,number of mages,simulations,crit equivalency\n')
    for hit in hit_chance:
        for num_mages in nmages:
            filename = '../savestates/rotation_{:2.0f}_{:d}.dat'.format(100.0*hit, num_mages)
            if os.path.exists(filename):
                with open(filename, 'rb') as fid2:
                    sim_size = pickle.load(fid2)
                    conversions = pickle.load(fid2)
                for sindex, spd in enumerate(spell_damage):
                    for cindex, crit in enumerate(crit_chance):
                        output = '{:3.0f},{:2.0f},{:2.0f},{:d},{:d},{:6.3f}\n'
                        output = output.format(spd, 100.0*hit, 100.0*crit, num_mages,
                                               sim_size[0], conversions[sindex, cindex])
                        fid.write(output)
    fid.close()

if __name__ == '__main__':
    main()