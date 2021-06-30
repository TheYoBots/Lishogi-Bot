import re

#usi, uci

def isusi(move):
    return bool(re.match("([1-9][a-i][1-9][a-i]\+?$)|([PLNSGBR]\*[1-9][a-i]$)", move))

def isuci(move):
    return bool(re.match("([a-i][1-9][a-i][1-9]\+?$)|([PLNSGBR]\*[a-i][1-9]$)", move))

# changes uci to usi and usi to uci
def switchusiuci(move) -> str:
	transtable = {97: 57, 98: 56, 99: 55, 100: 54, 101: 53, 102: 52, 103: 51, 104: 50, 105: 49 }
	transtable.update({v: k for k, v in transtable.items()})
	return move.translate(transtable)

# makes sure the move is usi
def makeusi(move) -> str:
    if(isuci(move)):
        return switchusiuci(move)
    else:
        return move

# makes sure the move is uci
def makeuci(move) -> str:
    if(isusi(move)):
        return switchusiuci(move)
    else:
        return move
