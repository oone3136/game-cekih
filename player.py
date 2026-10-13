"""
Modul Player untuk Remi Cekih.
Menangani tangan pemain, skor kumulatif, sortir kartu, dan tampilan.
"""

from typing import List, Optional
from card import Card
from config import GameConfig

class Player:
    def __init__(self, name: str, is_human: bool = False):
        self.name = name
        self.is_human = is_human
        self.hand: List[Card] = []
        self.score: int = 0
        self.melds = []  # Melds yang sudah dibuat
        self.open_melds: List[List[Card]] = []  # Kartu jadi yang ditaruh terbuka di meja

    def add_open_meld(self, meld_cards: List[Card]):
        """Menambahkan kombinasi kartu terbuka ke meja di depan pemain."""
        self.open_melds.append(meld_cards)

    def receive_cards(self, cards: List[Card]):
        self.hand.extend(cards)
        self.sort_hand()

    def add_card(self, card: Card):
        self.hand.append(card)
        self.sort_hand()

    def remove_card(self, card: Card):
        if card in self.hand:
            self.hand.remove(card)

    def sort_hand(self):
        """Sortir kartu berdasarkan kembang lalu nilai rank."""
        suit_order = {"SEKOP": 0, "HATI": 1, "KERITING": 2, "TAHU": 3}
        self.hand.sort(key=lambda c: (c.is_joker, suit_order.get(c.suit, 4), c.rank))

    def display_hand(self, show_indices: bool = True, use_color: bool = True) -> str:
        """Menampilkan kartu di tangan dengan rapi."""
        if not self.hand:
            return "(Kosong)"
        parts = []
        for i, card in enumerate(self.hand):
            prefix = f"{i+1}: " if show_indices else ""
            parts.append(f"{prefix}{card.display(use_color=use_color)}")
        return "  ".join(parts)

    def __repr__(self):
        return f"Player({self.name}, cards={len(self.hand)}, score={self.score})"
