from re import search, findall, IGNORECASE
from re import split as resplit

def pre_search(key, data):
    if not key:
        return(False)
    else:
        return(search(key, data, flags=IGNORECASE))

def key_search(data, key):
    if not isinstance(data, str) or not isinstance(key, str):
        raise ValueError('data and key should both be string.')

    if not search(r'".+?"', key):
        syntax_symbol = r'&|\-|\+|;|\(|\)'
        while search(r'/\d+?n/', key):
            in_slash = findall(r'/\d+?n/', key)[0]
            fore_slash = resplit(in_slash, key)[0]
            fore_slash = resplit(syntax_symbol, fore_slash)[-1]
            back_slash = resplit(in_slash, key)[1]
            back_slash = resplit(syntax_symbol, back_slash)[0]
            dummy_dot = findall(r'\d+', in_slash)[0]
            pre = fore_slash + in_slash + back_slash
            sub = fore_slash + '.{0,' + dummy_dot + '}' + back_slash + '|' + back_slash + '.{0,' + dummy_dot + '}' + fore_slash
            key = key.replace(pre, sub)
        while search(r'/\d+?/', key):
            pre = findall(r'/\d+?/', key)[0]
            dummy_dot = findall(r'\d+', pre)[0]
            sub = '.{0,' + dummy_dot + '}'
            key = key.replace(pre, sub)

        key_ls = resplit(r'\+', key)
        for i in key_ls:
            while search(r'\(.+?;.+?\)', i):
                in_par = findall(r'(?<=\().+?;.+?(?=\))', i)[0]
                sub = []
                for j in resplit(';', in_par):
                    stop=False
                    if search(r'\-', j):
                        for k in resplit(r'\-', j)[1:]:
                            if search(r'&', k):
                                and_ls = resplit(r'&', k)
                                if all(pre_search(regex, data) for regex in and_ls):
                                    stop=True
                                    break
                            else:
                                if pre_search(k, data):
                                    stop=True
                                    break
                        j = resplit(r'\-', j)[0]
                    if not stop:
                        sub.append(j)
                pre = '(' + in_par + ')'
                sub = '|'.join(sub)
                i = i.replace(pre, sub)
            if search(r'\-', i):
                for j in resplit(r'\-', i)[1:]:
                    stop = False
                    if search(r'&', j):
                        and_ls = resplit(r'&', j)
                        if all(pre_search(regex ,data) for regex in and_ls):
                            stop = True
                            break
                    else:
                        if pre_search(j, data):
                            stop = True
                            break
                if stop:
                    continue
                i = resplit(r'\-', i)[0]
            if search(r'&', i):
                and_ls = resplit(r'&', i)
                if all(pre_search(regex, data) for regex in and_ls):
                    return(True)
            else:
                if pre_search(i, data):
                    return(True)
        return(False)
    else:
        temp_escape = findall('".+?"', key)
        temp_escape = [x.replace(r'+', r'\+') for x in temp_escape]
        temp_escape = [x.replace(r'-', r'\-') for x in temp_escape]
        temp_escape = [x.replace(r'(', r'\(') for x in temp_escape]
        temp_escape = [x.replace(r')', r'\)') for x in temp_escape]
        temp_key = resplit('|'.join(temp_escape), key)
        temp_escape = [x.replace(r'"', r'') for x in temp_escape]
        temp_key = [x.replace(r'&', r'~&~') for x in temp_key]
        temp_key = [x.replace(r'-', r'~-~') for x in temp_key]
        temp_key = [x.replace(r'+', r'~+~') for x in temp_key]
        temp_key = [x.replace(r';', r'~;~') for x in temp_key]
        temp_key = [x.replace(r'(', r'~(~') for x in temp_key]
        temp_key = [x.replace(r')', r'~)~') for x in temp_key]
        temp_key = [x.replace(r'/', r'~/~') for x in temp_key]
        if len(temp_escape) + 1 != len(temp_key):
            raise ValueError('error with syntax ""')
        for i in range(len(temp_key)):
            if i == 0:
                key = temp_key[i]
            else:
                key = key + temp_escape[i-1]
                key = key + temp_key[i]

        syntax_symbol = r'~&~|~\-~|~\+~|~;~|~\(~|~\)~'
        while search(r'~/~\d+?n~/~', key):
            in_slash = findall(r'~/~\d+?n~/~', key)[0]
            fore_slash = resplit(in_slash, key)[0]
            fore_slash = resplit(syntax_symbol, fore_slash)[-1]
            back_slash = resplit(in_slash, key)[1]
            back_slash = resplit(syntax_symbol, back_slash)[0]
            dummy_dot = findall(r'\d+', in_slash)[0]
            pre = fore_slash + in_slash + back_slash
            sub = fore_slash + '.{0,' + dummy_dot + '}' + back_slash + '|' + back_slash + '.{0,' + dummy_dot + '}' + fore_slash
            key = key.replace(pre, sub)
        while search(r'~/~\d+?~/~', key):
            pre = findall(r'~/~\d+?~/~', key)[0]
            dummy_dot = findall(r'\d+', pre)[0]
            sub = '.{0,' + dummy_dot + '}'
            key = key.replace(pre, sub)

        key_ls = resplit(r'~\+~', key)
        for i in key_ls:
            while search(r'~\(~.+?~;~.+?~\)~', i):
                in_par = findall(r'(?<=~\(~).+?~;~.+?(?=~\)~)', i)[0]
                sub = []
                for j in resplit('~;~', in_par):
                    stop=False
                    if search(r'~\-~', j):
                        for k in resplit(r'~\-~', j)[1:]:
                            if search(r'~&~', k):
                                and_ls = resplit(r'~&~', k)
                                if all(pre_search(regex, data) for regex in and_ls):
                                    stop=True
                                    break
                            else:
                                if pre_search(k, data):
                                    stop=True
                                    break
                        j = resplit(r'~\-~', j)[0]
                    if not stop:
                        sub.append(j)
                pre = '~(~' + in_par + '~)~'
                sub = '|'.join(sub)
                i = i.replace(pre, sub)
            if search(r'~\-~', i):
                for j in resplit(r'~\-~', i)[1:]:
                    stop = False
                    if search(r'~&~', j):
                        and_ls = resplit(r'~&~', j)
                        if all(pre_search(regex ,data) for regex in and_ls):
                            stop = True
                            break
                    else:
                        if pre_search(j, data):
                            stop = True
                            break
                if stop:
                    continue
                i = resplit(r'~\-~', i)[0]
            if search(r'~&~', i):
                and_ls = resplit(r'~&~', i)
                if all(pre_search(regex, data) for regex in and_ls):
                    return(True)
            else:
                if pre_search(i, data):
                    return(True)
        return(False)

if __name__ == '__main__':
    pass
