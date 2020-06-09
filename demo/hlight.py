import re

def hlight_term(string, term):
    term = term.split()

    if str(type(string)) == "<class 'NoneType'>":
        result = " "
        return result

    if len(string) < 300:
        return string

    elif len(string) < 600:
        if len(term) < 2:
            idx = string.find(term[0])
            if idx < 10:
                begin = idx
                result = string[begin:begin + 300]
                result = result + " ..."
            elif idx < 300:
                begin = idx - 10
                result = string[begin:begin + 300]
                result = "... " + result + " ..."
            else:
                begin = 300
                result = string[begin:begin + 300]
                result = "... " + result
        else:
            begin = 300
            for i in range(len(term)):
                begin = min(begin-10, string.find(term[i]))
            result = string[begin:begin + 300]
            result = result + " ..."
        return result
    else:
        if len(term) < 2:
            idx = string.find(term[0])
            if idx < 10:
                begin = idx
                result = string[begin:begin + 300]
                result = result + " ..."
            elif idx < len(string)-300:
                begin = idx-10
                result = string[begin:begin + 300]
                result = "... " + result + " ..."
            else:
                begin = len(string)-300
                result = string[begin:begin + 300]
                result = "... " + result
        else:
            begin = len(string)-300
            for i in range(len(term)):
                begin = min(begin-10, string.find(term[i]))
            result = string[begin:begin+300]
            result = result + " ..."
        return result
