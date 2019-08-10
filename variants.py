# -*- coding: utf-8 -*-
import chess.variant


class SimpleBoard:
    def __init__(self, initial_fen=None, chess960=False):
        self.initial_fen = initial_fen
        self.move_stack = []
        self.color = True if initial_fen.split()[1] == "w" else False
        self.chess960 = chess960

    def push(self, move):
        self.move_stack.append(move)
        self.color = not self.color

    def is_game_over(self):
        return False

    def fen(self):
        if self.initial_fen is None:
            return self.starting_fen
        else:
            return self.initial_fen


class MakrukBoard(SimpleBoard):
    aliases = ["Makruk"]
    uci_variant = "makruk"
    starting_fen = "rnsmksnr/8/pppppppp/8/8/PPPPPPPP/8/RNSKMSNR w - - 0 1"


class SittuyinBoard(SimpleBoard):
    aliases = ["Sittuyin"]
    uci_variant = "sittuyin"
    starting_fen = "8/8/4pppp/pppp4/4PPPP/PPPP4/8/8[rrnnssfkRRNNSSFK] w - - 0 1"


class ShogiBoard(SimpleBoard):
    aliases = ["Shogi"]
    uci_variant = "shogi"
    starting_fen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"


class XiangqiBoard(SimpleBoard):
    aliases = ["Xiangqi"]
    uci_variant = "xiangqi"
    starting_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


class PlacementBoard(SimpleBoard):
    aliases = ["Placement", "Bronstein", "Benko"]
    uci_variant = "placement"
    starting_fen = "8/pppppppp/8/8/8/8/PPPPPPPP/8[nnbbrrqkNNBBRRQK] w - - 0 1"


class CapablancaBoard(SimpleBoard):
    aliases = ["Capablanca"]
    uci_variant = "capablanca"
    starting_fen = "rnnbqkbnnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNNBQKBNNR w - - 0 1"


class SeirawanBoard(SimpleBoard):
    aliases = ["Seirawan"]
    uci_variant = "seirawan"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[HEhe] w KQBCDFGkqbcdfg - 0 1"


chess.variant.VARIANTS += [
    MakrukBoard,
    SittuyinBoard,
    ShogiBoard,
    XiangqiBoard,
    PlacementBoard,
    CapablancaBoard,
    SeirawanBoard,
]
