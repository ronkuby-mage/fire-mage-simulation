import os
import json
from copy import deepcopy

cfn = ["..", "config", "mc"]
bases = ["fireball", "frostbolt", "frostbolt2", "frostbolt3"]
rots = [2, 2, 4, 4, 4]

print('hi')
for num_pi in range(0, 5):
    for num_mages in range(max([1, num_pi]), 10):
        for rotation in bases[:rots[num_pi]]:
            run_name = '{:s}_{:d}n_{:d}m_{:d}p'.format(rotation, num_mages,
                        num_mages, num_pi)
            fn = os.path.join(*cfn, run_name + '.json')
            with open(fn, 'rt') as fid:
                base = json.load(fid)
                print(base['mc_params'])
            new_config = deepcopy(base)
            new_config['mc_params']['batches'] = 9999
            with open(fn, 'wt') as fid:
                json.dump(new_config, fid, indent=4)
            
