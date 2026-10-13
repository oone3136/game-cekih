"""
Modul AI Bot Pemain Bapak-bapak Pos Ronda.
Bot memiliki kecerdasan taktis:
- Mengenali kombinasi Seri & Tris
- Tahu kapan harus serok kartu buangan (terutama jika bisa langsung TUTUP)
- Memilih kartu buangan yang aman agar tidak kena denda cekih
- Menghindari buang Joker
"""

import random
from typing import List, Tuple, Optional
from itertools import combinations
from card import Card
from player import Player
from config import GameConfig
from rules import (
    check_discard_pickup_validity, check_tutup,
    is_valid_meld, partition_into_melds, Meld
)

class BotPlayer(Player):
    def __init__(self, name: str, personality: str = "imbang"):
        super().__init__(name, is_human=False)
        self.personality = personality  # 'penakut', 'imbang', 'nekat'

    def decide_draw(
        self,
        discard_pile: List[Card],
        is_first_round: bool,
        config: GameConfig
    ) -> Tuple[str, Optional[int], Optional[List[Card]]]:
        """
        Memutuskan mau ambil dari kocokan atau serok buangan.
        Return:
        - ('DECK', None, None)
        - ('DISCARD', depth_idx, [pair_c1, pair_c2])
        """
        if is_first_round or not discard_pile:
            return "DECK", None, None

        # Evaluasi kartu buangan dalam batas jangkauan
        max_search = min(len(discard_pile), config.max_discard_depth)
        
        best_pickup = None
        best_priority = -999

        for depth in range(max_search):
            target_card = discard_pile[depth]

            # Cari pasangan 2 kartu di tangan yang cocok
            for c1, c2 in combinations(self.hand, 2):
                pair = [c1, c2]
                valid, _ = check_discard_pickup_validity(
                    self.hand, target_card, pair, config,
                    open_melds=self.open_melds, other_scooped_cards=discard_pile[:depth]
                )
                if valid:
                    # Simulasi serok: kartu 0..depth ikut terambil
                    simulated_hand = self.hand.copy()
                    scooped = discard_pile[:depth + 1]
                    simulated_hand.extend(scooped)

                    # Prioritas 1: Jika dengan serok ini langsung bisa TUTUP!
                    tutup_opts = check_tutup(simulated_hand, config)
                    if tutup_opts:
                        # Prioritas tertinggi! Langsung sikat!
                        return "DISCARD", depth, pair

                    # Jika tidak langsung tutup, pertimbangkan risiko tumpukan serok
                    # Makin dalam serok, makin banyak kartu sampah yang terangkut
                    cards_scooped_count = depth + 1
                    risk_penalty = cards_scooped_count * 8

                    # Bonus membentuk kombinasi baru
                    priority = 50 - risk_penalty

                    if priority > best_priority:
                        best_priority = priority
                        best_pickup = (depth, pair)

        # Hanya ambil jika prioritas menguntungkan (biasanya kedalaman 1 atau 2)
        if best_pickup and best_priority > 20:
            depth, pair = best_pickup
            return "DISCARD", depth, pair

        return "DECK", None, None

    def decide_tutup_or_gantung(
        self,
        tutup_options: List[Tuple[Card, List[Meld]]],
        remaining_deck: int
    ) -> Tuple[bool, Card, List[Meld]]:
        """
        Memutuskan apakah mau TUTUP sekarang atau GANTUNG (lanjut main).
        """
        best_opt = max(tutup_options, key=lambda opt: opt[0].rank)
        close_card, melds = best_opt

        # Jika tutupan Raja atau As, selalu TUTUP (poin besar!)
        if close_card.card_type in ("AS", "RAJA"):
            return True, close_card, melds

        # Jika tutupan Anak:
        if self.personality == "nekat" and remaining_deck > 15:
            # 40% peluang gantung demi cari kartu tutupan lebih mahal
            if random.random() < 0.4:
                return False, close_card, melds

        # Default bot: Tutup sekarang untuk mengamankan poin
        return True, close_card, melds

    def decide_discard(self, config: GameConfig) -> Card:
        """
        Memilih 1 kartu dari tangan untuk dibuang ke discard pile.
        Prinsip:
        1. JANGAN PERNAH buang Joker jika bisa dihindari!
        2. Jangan buang kartu yang sudah jadi bagian dari meld.
        3. Buang kartu mentah yang tidak terhubung dengan kartu lain.
        """
        candidates = [c for c in self.hand if not c.is_joker]
        if not candidates:
            # Terpaksa buang apa saja jika tangan semua joker
            return self.hand[0]

        # Hitung skor kegunaan tiap kartu (kartu yang punya koneksi angka/kembang sama diberi nilai tinggi)
        scored_cards = []
        for card in candidates:
            utility = 0
            for other in self.hand:
                if other == card or other.is_joker:
                    continue
                # Hubungan Seri: kembang sama dan selisih rank dekat
                if other.suit == card.suit and abs(other.rank - card.rank) in (1, 2):
                    utility += 10
                # Hubungan Tris: rank sama
                if other.rank == card.rank:
                    utility += 8

            # Kartu angka besar (K, Q, J, A) yang mentah/tanpa koneksi lebih diprioritaskan
            # untuk dibuang agar tidak menumpuk denda minus besar
            danger_penalty = 0
            if card.rank == 14:
                danger_penalty = 15
            elif card.rank in (11, 12, 13):
                danger_penalty = 10
            else:
                danger_penalty = card.rank

            # Skor akhir: makin rendah skornya, makin layak dibuang
            final_score = utility - (danger_penalty * 0.5)
            scored_cards.append((final_score, card))

        scored_cards.sort(key=lambda x: x[0])
        # Pilih kartu dengan utilitas terendah
        return scored_cards[0][1]
