KEY_TEXT = "rkjfawtphxuoievokbanzmycaksjdgoql"

def toupper(char: str):
    """ converts letter to upper case if neccesary """
    if len(char) != 1:
        return None

    num = ord(char)
    if num >= 65 and num <= 90:
        return char
    
    elif num >= 97 and num <= 122:
        return chr(num - 32)

    else:
        return None

def tolower(char: str):
    """ converts letters to lowercase if necessary """
    if len(char) != 1:
        return None
    
    num = ord(char)
    if num >= 65 and num <= 90:
        return chr(num + 32)
    
    elif num >= 97 and num <= 122:
        return char

    else:
        return None

def scramble(plain_text: str):
    """ scrambles text using a string as the cypher key """
    cypher_text = ""
    i = 0
    for char in plain_text:
        if i > len(KEY_TEXT) - 1:
            i = 0

        if char.isalpha() and char.isupper():
            key = ord(toupper(KEY_TEXT[i])) - 65
            curr_index = ord(char) - 65
            new_index = (curr_index + key) % 26
            new_letter = 65 + new_index
            cypher_text += chr(new_letter)

        elif char.isalpha() and char.islower():
            key = ord(tolower(KEY_TEXT[i])) - 97
            curr_index = ord(char) - 97
            new_index = (curr_index + key) % 26
            new_letter = 97 + new_index
            cypher_text += chr(new_letter)

        else:
            cypher_text += char

        i += 1

    return(cypher_text)

def unscramble(cypher_text: str):
    """ unscrables text, uses a string as the cypher key """
    i = 0
    plain_text = ""
    for char in cypher_text:

        if i > len(KEY_TEXT) - 1:
            i = 0
    
        if char.isalpha() and char.isupper():
            key = ord(toupper(KEY_TEXT[i])) - 65
            curr_index = ord(char) - 65
            new_index = (curr_index - key) % 26
            new_letter = 65 + new_index
            plain_text += chr(new_letter)

        elif char.isalpha() and char.islower():
            key = ord(tolower(KEY_TEXT[i])) - 97
            curr_index = ord(char) - 97
            new_index = (curr_index - key) % 26
            new_letter = 97 + new_index
            plain_text += chr(new_letter)

        else:
            plain_text += char

        i += 1
    
    return(plain_text)