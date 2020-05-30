import os
import pickle
import numpy as np

prefix = ["frostbolt_r1_", "fire_blast_", "pyroblast_", "wait_1s_", "frostbolt_"]

dfn = "../savestates/rotation/"
nn = "1_"
n_w = np.array([1, 3, 7, 12, 7, 3, 1], dtype=np.float)
n_w /= n_w.sum()
#n_c = np.array([0, 0, 0, 0, 3, 9, 7, 1, 0], dtype=np.float)
n_c = np.array([0, 2, 9, 5, 0, 0, 0, 0, 0], dtype=np.float)
n_c /= n_c.sum()
n_c, n_w = np.meshgrid(n_c, n_w)
n_n = n_c*n_w
print(n_n)

for fn in os.listdir(dfn):
    for pref2 in prefix:
        pref = pref2 + nn
        if len(fn.split(pref)) > 1:
            break
    else:
        continue
    filename = dfn + fn
    with open(filename, 'rb') as fid:
        values = pickle.load(fid)
    worth = (values*n_n).sum()
    print(fn, worth)
        
                    
