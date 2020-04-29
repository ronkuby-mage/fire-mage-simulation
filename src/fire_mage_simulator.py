import os
import numpy as np
import itertools
from pathos.multiprocessing import Pool
import time
from mechanics import get_damage, get_crit_damage_diff, get_hit_damage_diff
import plots
import constants

def main():
    get_damage(700.0, 0.970, 0.300, 6, 1.0, 100000)

    C = constants.Constant()
    
    spell_damage = np.arange(C._SP_START, C._SP_END + C._SP_STEP/2.0, C._SP_STEP)
    crit_chance = np.arange(C._CRIT_START, C._CRIT_END + C._CRIT_STEP/2.0, C._CRIT_STEP)
    hit = 0.95
    num_mages = 6
    
    hits = np.array([hit])
    mages = np.array([num_mages])
    sim_size = C._CRIT_SIMSIZE*5/num_mages
    sim_size = np.array([sim_size]).astype(np.int32)
    responses = np.array([C._INITIAL_SIGMA])

    args = itertools.product(spell_damage, hits, crit_chance, mages, responses, sim_size)
    largs = [*args]

    print('Hit = {:2.0f} # mages = {:d}'.format(100.0*hit, num_mages))
    with Pool() as p:
        out = np.array(p.starmap(get_crit_damage_diff, largs)).reshape((len(spell_damage), len(hits), len(crit_chance), len(mages), len(responses), len(sim_size)))
    conversions = np.squeeze(out)

    plots.plot_equiv(spell_damage, crit_chance, conversions, hit, num_mages, sim_size[0], C._DURATION_AVERAGE, 'crit')

    
    
if __name__ == '__main__':
    main()