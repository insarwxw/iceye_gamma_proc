def read_keyword(par_file: str, keyword: str,
                 delimiter=":", rm_unit: str = '',
                 multi_val=None):
    """
    Look for the selected keyword inside the selected txt file.
    see St_RELEASE/COMMON/PYTHON/reset_keyword.py from more details.
    :param par_file: absolute path to parameter file.
    :param keyword: selected keyword
    :param delimiter: keyword/value delimiter
    :param rm_unit: parameter unit [str]
    :param multi_val: keyword associated with multiple values (e.g. List)
    :return: Value associated to the selected keyword
    """
    s = ''
    with open(par_file, 'r') as fid:
        keyword_found = False
        for line in fid:
            keyword_from_line = line.split(delimiter)[0].strip()
            if keyword_from_line == keyword:
                line = line.strip()
                s = line.split(delimiter)
                s = delimiter.join(s[1:])
                keyword_found = True
                break
    if rm_unit:
        pos = s.find(rm_unit)
        s = s[:pos]

    if multi_val:
        s = [x for x in s.split(multi_val[0]) if x]
        strs = ["" for x in range(len(multi_val)-1)]
        for i in range(1, len(multi_val)):
            if int(multi_val[i]) <= len(s)-1:
                strs[i-1] = s[int(multi_val[i])].strip()
            else:
                strs[i-1] = '-1'
        return strs

    if not keyword_found:
        s = '-1'

    return s.strip()
