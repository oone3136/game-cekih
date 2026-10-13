"""
Modul Deck (Kocokan Kartu) untuk Remi Cekih.
Mendukung kocok, bagi kartu, dan inisialisasi varian Joker.
"""

import random
from typing import List, Optional, Tuple
from card import Card, SUIT_SYMBOLS
from config import GameConfig

class Deck:
    def __init__(self, config: GameConfig):
        self.config = config
        self.cards: List[Card] = []
        self.wild_rank: Optional[int] = None
        self._build_deck()

    def _build_deck(self):
        self.cards.clear()
        suits = list(SUIT_SYMBOLS.keys())
        
        # 52 kartu standar (Rank 2..14)
        for suit in suits:
            for rank in range(2, 15):
                self.cards.append(Card(rank=rank, suit=suit, is_joker=False))

        # Mode Joker 2 Fisik (Joker Asli: Merah & Hitam)
        if self.config.joker_mode == "TWO_JOKERS":
            self.cards.append(Card(rank=99, suit="HATI", is_joker=True))
            self.cards.append(Card(rank=99, suit="SEKOP", is_joker=True))

    def shuffle(self):
        """Kocok tumpukan kartu secara acak."""
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        """Tarik 1 kartu dari atas tumpukan kocokan."""
        if not self.cards:
            return None
        return self.cards.pop()

    def setup_open_card_wild(self, opened_card: Card):
        """
        Jika mode OPEN_CARD_WILD aktif:
        Kartu pertama yang dibuka ke tumpukan buangan menentukan Joker (menjadi Kartu Mati).
        Semua kartu di sisa tumpukan / tangan yang memiliki angka sama (tepat 3 kartu) menjadi Joker aktif.
        """
        if self.config.joker_mode == "OPEN_CARD_WILD":
            self.wild_rank = opened_card.rank
            opened_card.is_joker = True
            # Tandai semua kartu yang memiliki angka ini di deck sebagai Joker (sisa 3 kartu)
            for card in self.cards:
                if card.rank == self.wild_rank:
                    card.is_joker = True

    def mark_wild_cards_in_list(self, card_list: List[Card]):
        """Menandai kartu liar di list kartu pemain jika mode OPEN_CARD_WILD."""
        if self.config.joker_mode == "OPEN_CARD_WILD" and self.wild_rank is not None:
            for card in card_list:
                if card.rank == self.wild_rank:
                    card.is_joker = True

    @property
    def remaining(self) -> int:
        return len(self.cards)

    def is_empty(self) -> bool:
        return len(self.cards) == 0
