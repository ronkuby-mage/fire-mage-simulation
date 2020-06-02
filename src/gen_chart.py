

# 6 frost
# =SUMPRODUCT(DI2:DI74, DP2:DP74)

# 6 fire
# =SUMPRODUCT(DQ2:DQ73, DX2:DX73)

# 7 frost
# =SUMPRODUCT(DY2:DY60, EF2:EF60)

def to_alpha(num):
    d0 = chr(num//26 + ord('A'))
    d1 = chr(num%26 + ord('A'))
    
    return d0 + d1

def sum_prod(col1, col2, clen):
    return 'SUMPRODUCT({:s}2:{:s}{:d}, {:s}2:{:s}{:d})'.format(to_alpha(col1),
                                to_alpha(col1),
                                clen,
                                to_alpha(col2),
                                to_alpha(col2),
                                clen)


stype = 'frost'
column = 4

length = {
        'frost': [
                33,
                86,
                106,
                98,
                81,
                74,
                60,
                60,
                51],
        'fire': [
                29,
                91,
                113,
                101,
                85,
                73,
                66,
                64,
                60],
        }


start_col = 6
per_spec = 8
per_nm = 2*per_spec

for num_mages in range(9):
    col = start_col + per_nm*num_mages
    if stype == 'fire':
        col += per_spec
    clen = length[stype][num_mages]
    total_damage = sum_prod(col, col + per_spec - 1, clen)
    if column == 0:
        print('=', total_damage)
    else:
        #=10*(SUMPRODUCT(DD2:DD85, $DH2:$DH85) - SUMPRODUCT(DA2:DA85, $DH2:$DH85))/(SUMPRODUCT(DB2:DB85, $DH2:$DH85) - SUMPRODUCT(DA2:DA85, $DH2:$DH85))
        if column%2:
            numc = col + 3
        else:
            numc = col + 2
        if column > 2:
            denc = col + 4
            numc += 3
        else:
            denc = col + 1
        num = sum_prod(numc, col + per_spec - 1, clen) + ' - ' +  total_damage
        den = sum_prod(denc, col + per_spec - 1, clen) + ' - ' +  total_damage
        print('=10*(' + num + ')/(' + den + ')')

