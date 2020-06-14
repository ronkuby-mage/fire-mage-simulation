import os
import json
from copy import deepcopy

cfn = "../config/mc"

base_fn = "frostbolt3_3n_3m_3p"
#base_fn = "fireball_3n_3m_3p"
max_pi = 3
max_mqg = 9


with open(os.path.join(cfn, base_fn + '.json'), 'rt') as fid:
    base = json.load(fid)
    
bsplit  = base_fn.split('n_')
for num_mages in range(max([max_pi, 1]), 10):
    num_mqg = min([num_mages, max_mqg])
    num_pi = min([num_mages, max_pi])
    new_config = deepcopy(base)    
    new_config['configuration'][0]['num_mages'] = num_mages
    new_config['configuration'][0]['num_mqg'] = num_mqg
    new_config['configuration'][0]['num_pi'] = num_pi
    new_fn = '{:s}{:d}n_{:d}m_{:d}p.json'.format(bsplit[0][:-1],
              num_mages,
              num_mqg,
              num_pi)
    print(new_fn)
    with open(os.path.join(cfn, new_fn), 'wt') as fid:
        json.dump(new_config, fid, indent=4)

