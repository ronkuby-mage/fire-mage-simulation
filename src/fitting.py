import os
import numpy as np
import pickle
import json
from sklearn.preprocessing import PolynomialFeatures
from itertools import permutations, product, combinations_with_replacement

def find_combinations_util(arr, index, num, reducedNum):
    if (reducedNum < 0):
        return []
    if (reducedNum == 0):
        return [tuple([arr[i] for i in range(index)])]
    prev = 1 if index == 0 else arr[index - 1]
    combs = []
    for k in range(prev, num + 1):
        arr[index] = k;
        combs += find_combinations_util(arr, index + 1, num, reducedNum - k)

    return combs

def find_combs(n):
    arr = [0]*n
    combs = find_combinations_util(arr, 0, n, n)
    combs = [sorted(aa, reverse=True) for aa in combs]
    return sorted(combs, reverse=True)

def range_norm(vals, rang):
    return 2.0 - 4.0*(vals - rang[0])/(rang[1] - rang[0])    

def poly(order, values):
    value_list = []
    for jdx, val in enumerate(values):
        value_list.append([chr(ord('A') + jdx) + str(idx) for idx in range(val)])
    value_index = list(range(len(value_list)))
    tind = 0
    outs = [[0, ()]]
    prefs = set([-1])
    for torder in range(order):
        for comb in find_combs(torder + 1):
            for ptype in combinations_with_replacement(value_index, len(comb)):
                if len(set(ptype)) < len(ptype):
                    continue
                perms = []
                for set_ind, count in zip(ptype, comb):
                    ll = []
                    for comb2 in find_combs(count):
                        for perm in combinations_with_replacement(value_list[set_ind], len(comb2)):
                            if len(set(perm)) < len(perm):
                                continue
                            sf = ''
                            for val, p in zip(perm, comb2):
                                sf += ' ' + str(p) + str(val)
                            ll.append(str(tind) + ':' + sf)
                        tind += 1
                    perms.append(ll)
                for tt in product(*perms):
                    llist = [tt[0]] + [dd.split(': ')[-1] for dd in tt[1:]]
                    llist = ' '.join(llist)
                    cc = llist.split(': ')
                    if cc[0] not in prefs:
                        prefs.add(cc[0])
                    output = [len(prefs) - 1]
                    cca = cc[1].split(' ')
                    for entry in cca:
                        output.append((ord(entry[1]) - ord('A'),
                                       ord(entry[2]) - ord('0'),
                                       float(ord(entry[0]) - ord('0'))))
                    outs.append(output)
    return outs

dfn = "../mc/"
cfn = "../config/monte_carlo_test.json"
order = 2
with open(cfn, "rt") as fid:
    config = json.load(fid)
sp_range = config['stats']['spell_power']['clip']
hit_range = config['stats']['hit_chance']['clip']
crit_range = config['stats']['crit_chance']['clip']
dur_range = config['timing']['duration']['clip']

values = []
sps = []
hits = []
crits = []
durs = []
for fn in os.listdir(dfn):
    filename = os.path.join(dfn, fn)

    with open(filename, "rb") as fid:
        while fid.tell() < os.fstat(fid.fileno()).st_size:
            values.append(pickle.load(fid))
            args = pickle.load(fid)
            sp = range_norm(np.array(args['spell_power']['fixed']), sp_range)
            hit = range_norm(np.array(args['hit_chance']['fixed']), hit_range)
            crit = range_norm(np.array(args['crit_chance']['fixed']), crit_range)
            dur = range_norm(np.array(args['timing']['duration']['mean']), dur_range)
            sps.append(sp)
            hits.append(hit)
            crits.append(crit)
            durs.append(dur)

sps = np.stack(sps)
hits = np.stack(hits)
crits = np.stack(crits)
durs = np.stack(durs)
g2_size = args["num_mages"]["num_pi"]
g1_size = args["num_mages"]["num_mages"] - g2_size

order = 3
values = (g1_size, g2_size, g1_size, g2_size, g1_size, g2_size, 1)
outs = poly(order, values)
for out in outs:
    print(out)

