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

# sfen, fen

# replaces color, black goes first in shogi, but chesslike backend still assumes white goes first
def fixColor(fen) -> str:
	splitted = fen.split(' ')
	if len(splitted) > 1:
		color = splitted[1]
		if color == "b":
			splitted[1] = "w"
		else:
			splitted[1] = "b"
		return " ".join(splitted)

# Changing backend representation of pieces to normal representation
def fixPosition(position) -> str:
    position = position.replace("U", "+L").replace("M", "+N").replace("A", "+S").replace("D", "+R").replace("H", "+B").replace("T", "+P").replace("u", "+l").replace("m", "+n").replace("a", "+s").replace("d", "+r").replace("h", "+b").replace("t", "+p")
    return fixPocket(position)

# Orders pocket properly (pppr -> r3p)
def fixPocket(sfen) -> str:
    splitted = sfen.split(' ')
    if(len(splitted) > 2 and splitted[2] != '-'):
        # rook, bishop, gold, silver, knight, lance, pawn
        pieceOrder = "RBGSNLPrbgsnlp"
        pocket = ""
        for i in "RBGSNLPrbgsnlp":
            c = splitted[2].count(i)
            if c == 0:
                pass
            elif c == 1:
                pocket += i
            else:
                pocket += str(c) + i

        splitted[2] = pocket
    return ' '.join(splitted)

# if called on sfen, it will switch starting color
def makesfenfromfen(fen) -> str:
    if(fen == "startpos"):
        return fen
    return fixColor(fixPocket(fixPosition(fen)))
