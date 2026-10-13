"""
Modul Representasi Kartu dan Kembang Remi.
Kembang khas Sunda/Pos Ronda:
- Sekop (♠)
- Hati (♥)
- Keriting (♣)
- Tahu / Wajik (♦)
"""

from typing import Optional

SUIT_SYMBOLS = {
    "SEKOP": "♠",
    "HATI": "♥",
    "KERITING": "♣",
    "TAHU": "♦"
}

RANK_NAMES = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
    11: "J", 12: "Q", 13: "K", 14: "A", 99: "JKR"
}

# ANSI Color codes untuk visual terminal yang jelas
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"

class Card:
    def __init__(self, rank: int, suit: Optional[str] = None, is_joker: bool = False):
        self.rank = rank              # 2..14, atau 99 untuk Joker
        self.suit = suit              # 'SEKOP', 'HATI', 'KERITING', 'TAHU', atau None untuk Joker
        self.is_joker = is_joker      # True jika ini Joker (fisik atau wild card)
        self.original_rank = rank
        self.original_suit = suit

    @property
    def card_type(self) -> str:
        """Kategori kartu: 'JOKER', 'AS', 'RAJA', atau 'ANAK'."""
        if self.is_joker or self.rank == 99:
            return "JOKER"
        if self.rank == 14:
            return "AS"
        if self.rank in (11, 12, 13):
            return "RAJA"
        return "ANAK"

    @property
    def rank_name(self) -> str:
        if self.is_joker:
            return "JKR"
        return RANK_NAMES.get(self.rank, str(self.rank))

    def display(self, use_color: bool = True) -> str:
        """Tampilan kartu ramah terminal."""
        if self.is_joker:
            symbol = f"[★ {RANK_NAMES.get(self.rank, str(self.rank))}]"
            return f"{COLOR_YELLOW}{COLOR_BOLD}{symbol}{COLOR_RESET}" if use_color else symbol

        suit_sym = SUIT_SYMBOLS.get(self.suit, "?")
        rank_name = RANK_NAMES.get(self.rank, str(self.rank))
        card_str = f"[{rank_name}{suit_sym}]"

        if not use_color:
            return card_str

        # Warna Merah untuk Hati dan Tahu (Wajik)
        if self.suit in ("HATI", "TAHU"):
            return f"{COLOR_RED}{COLOR_BOLD}{card_str}{COLOR_RESET}"
        else:
            return f"{COLOR_CYAN}{COLOR_BOLD}{card_str}{COLOR_RESET}"

    def __str__(self) -> str:
        return self.display(use_color=False)

    def __repr__(self) -> str:
        return self.display(use_color=False)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit and self.is_joker == other.is_joker

    def __hash__(self) -> int:
        return hash((self.rank, self.suit, self.is_joker))
