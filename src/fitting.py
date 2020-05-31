import os
import numpy as np
import pickle
import json
from sklearn.linear_model import LinearRegression
from itertools import product, combinations_with_replacement

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
    return 4.0*(vals - rang[0])/(rang[1] - rang[0]) - 2.0

def poly(order, values):
    value_list = []
    for jdx, val in enumerate(values):
        value_list.append([chr(ord('A') + jdx) + str(idx) for idx in range(val)])
    value_index = list(range(len(value_list)))
    tind = 0
    outs = [[0]]
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

run_name = "frostbolt_7n_7m_1p"
#run_name = "fireball_7n_7m_1p"
dfn = "../mc/" + run_name
cfn = "../config/" + run_name + ".json"
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
num_mages = args["num_mages"]["num_mages"]

order = 5
arrays = [sps[:, :g1_size],
          sps[:, g1_size:],
          hits[:, :g1_size],
          hits[:, g1_size:],
          crits[:, :g1_size],
          crits[:, g1_size:],
          durs[:, None]]
num_terms = [arr.shape[1] for arr in arrays]
outs = poly(order, num_terms)
num_coeff = outs[-1][0] + 1
X = np.zeros((arrays[0].shape[0], num_coeff))
y = np.stack(values) 
for out in outs:
    coeff_idx = out[0]
    term = 1.0
    for group, member, exponent in out[1:]:
        term *= np.power(arrays[group][:, member], exponent)
    X[:, coeff_idx] += term
    print(out)
model = LinearRegression(fit_intercept=False)
reg = model.fit(X, y)
print(reg.coef_)
print(reg.score(X, y))
print(np.sqrt(np.power(reg.predict(X) - y, 2).mean()))

big_terms = np.where(np.abs(reg.coef_) >= 0.3)[0]
X = X[:, big_terms]
model = LinearRegression(fit_intercept=False)
reg = model.fit(X, y)
print(reg.coef_)
print(reg.score(X, y))
print(np.sqrt(np.power(reg.predict(X) - y, 2).mean()))

fid2 = open('coeff.txt', 'wt')
with open('terms.txt', 'wt') as fid:
    for idx, tidx in enumerate(big_terms):
        tell = '= '
        for out in outs:
            if out[0] == tidx:
                out_st = ''
                for group, member, exponent in out[1:]:
                    if group < 6:
                        if group%2:
                            row = 3 + 4*member + group//2
                        else:
                            row = 3 + 4*(g2_size + member) + group//2
                    else:
                        row = 2
                    exp_str = '' if exponent <= 1 else '^' + str(int(exponent))
                    out_st += 'Z' + str(row) + exp_str + '*'
                if len(out) > 1:
                    tell += out_st[:-1] + ' + '
        fid.write(tell[:-3] + '\n')
        fid2.write('{:.10e}'.format(reg.coef_[idx]) + '\n')
fid2.close()



