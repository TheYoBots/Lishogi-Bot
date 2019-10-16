# -*- coding: utf-8 -*-


class SimpleBoard:
    def __init__(self, initial_fen=None, chess960=False):
        self.initial_fen = initial_fen
        self.move_stack = []
        self.color = True if initial_fen.split()[1] == "w" else False
        self.chess960 = chess960

    def push(self, move):
        self.move_stack.append(move)
        self.color = not self.color

    def pop(self):
        del self.move_stack[-1]
        self.color = not self.color

    def is_game_over(self):
        return False

    def fen(self):
        if self.initial_fen is None:
            return self.starting_fen
        else:
            return self.initial_fen


class StandardBoard(SimpleBoard):
    uci_variant = "standard"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class CrazyhouseBoard(SimpleBoard):
    uci_variant = "crazyhouse"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"


class MakrukBoard(SimpleBoard):
    uci_variant = "makruk"
    starting_fen = "rnsmksnr/8/pppppppp/8/8/PPPPPPPP/8/RNSKMSNR w - - 0 1"


class CambodianBoard(SimpleBoard):
    uci_variant = "cambodian"
    starting_fen = "rnsmksnr/8/pppppppp/8/8/PPPPPPPP/8/RNSKMSNR w DEde - 0 1"


class SittuyinBoard(SimpleBoard):
    uci_variant = "sittuyin"
    starting_fen = "8/8/4pppp/pppp4/4PPPP/PPPP4/8/8[rrnnssfkRRNNSSFK] w - - 0 1"


class ShogiBoard(SimpleBoard):
    uci_variant = "shogi"
    starting_fen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL[] b - 1"


class XiangqiBoard(SimpleBoard):
    uci_variant = "xiangqi"
    starting_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


class PlacementBoard(SimpleBoard):
    uci_variant = "placement"
    starting_fen = "8/pppppppp/8/8/8/8/PPPPPPPP/8[nnbbrrqkNNBBRRQK] w - - 0 1"


class CapablancaBoard(SimpleBoard):
    uci_variant = "capablanca"
    starting_fen = "rnabqkbcnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNABQKBCNR w - - 0 1"


class CapahouseBoard(SimpleBoard):
    uci_variant = "capahouse"
    starting_fen = "rnabqkbcnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNABQKBCNR[] w - - 0 1"


class SeirawanBoard(SimpleBoard):
    uci_variant = "seirawan"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[HEhe] w KQBCDFGkqbcdfg - 0 1"


class ShouseBoard(SimpleBoard):
    uci_variant = "shouse"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[HEhe] w KQBCDFGkqbcdfg - 0 1"


class GrandBoard(SimpleBoard):
    uci_variant = "grand"
    starting_fen = "r8r/1nbqkcabn1/pppppppppp/10/10/10/10/PPPPPPPPPP/1NBQKCABN1/R8R w - - 0 1"


class GrandhouseBoard(SimpleBoard):
    uci_variant = "grandhouse"
    starting_fen = "r8r/1nbqkcabn1/pppppppppp/10/10/10/10/PPPPPPPPPP/1NBQKCABN1/R8R[] w - - 0 1"


class GothicBoard(SimpleBoard):
    uci_variant = "gothic"
    starting_fen = "rnbqckabnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNBQCKABNR w KQkq - 0 1"


class GothhouseBoard(SimpleBoard):
    uci_variant = "gothhouse"
    starting_fen = "rnbqckabnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNBQCKABNR[] w KQkq - 0 1"


class MiniShogiBoard(SimpleBoard):
    uci_variant = "minishogi"
    starting_fen = "rbsgk/4p/5/P4/KGSBR[-] b - 1"


VARIANT2BOARD = {
    "standard": StandardBoard,
    "crazyhouse": CrazyhouseBoard,
    "makruk": MakrukBoard,
    "sittuyin": SittuyinBoard,
    "shogi": ShogiBoard,
    "xiangqi": XiangqiBoard,
    "placement": PlacementBoard,
    "capablanca": CapablancaBoard,
    "capahouse": CapahouseBoard,
    "seirawan": SeirawanBoard,
    "shouse": ShouseBoard,
    "grand": GrandBoard,
    "grandhouse": GrandhouseBoard,
    "gothic": GothicBoard,
    "gothhouse": GothhouseBoard,
    "minishogi": MiniShogiBoard,
    "cambodian": CambodianBoard,
}
