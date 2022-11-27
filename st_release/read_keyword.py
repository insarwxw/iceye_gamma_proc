# par.py

import numpy as np



def read_keyword(file, keyword, delimiter=":", rm_unit=None, multi_val=None):
    f = open(file, 'r')
    s = ''
    keyword_found = False
    for line in f:
        keyword_from_line = line.split(delimiter)[0].strip()
        if keyword_from_line == keyword:
            line = line.strip()
            s = line.split(delimiter)
            s = delimiter.join(s[1:])
            keyword_found = True
            break
    f.close()

    if rm_unit is not None:
        pos = s.find(rm_unit)
        s = s[0:pos]

    if multi_val is not None:
        s = [x for x in s.split(multi_val[0]) if x]
        strs = ["" for x in range(len(multi_val) - 1)]
        for i in range(1, len(multi_val)):
            if int(multi_val[i]) <= len(s) - 1:
                strs[i - 1] = s[int(multi_val[i])].strip()
            else:
                strs[i - 1] = '-1'
        return strs

        # print(s)
        # print(np.array(np.int32(multi_val[1:])))
        # s=np.array(s)[np.int32(multi_val[1:])]

    if not keyword_found:
        s = '-1'

    return s.strip()  # .replace(' ','')

