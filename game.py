"""
Modul Game Loop Remi Cekih Pos Ronda.
Mengatur giliran 4 pemain, serok buangan, cekih gantung, dan kalkulasi skor ronde.
"""

from typing import List, Tuple, Optional, Dict
from card import Card
from deck import Deck
from player import Player
from bot import BotPlayer
from config import GameConfig
from rules import (
    check_discard_pickup_validity, check_tutup,
    calculate_meld_points, calculate_deadwood_penalty,
    get_closing_card_value, get_deadwood_breakdown,
    find_optimal_layoffs, validate_layoff_selection, Meld
)

class DiscardEntry:
    def __init__(self, card: Card, discarded_by: Optional[int], is_dead: bool = False):
        self.card = card
        self.discarded_by = discarded_by  # index player (0..3) atau None jika bukaan awal meja
        self.is_dead = is_dead            # True jika ini kartu mati gantung (dilarang diserok)

    def __repr__(self):
        return f"{self.card}{' [MATI]' if self.is_dead else ''}"


class GameEngine:
    def __init__(self, config: GameConfig, human_name: str = "Kamu"):
        self.config = config
        self.players: List[Player] = [
            Player(name=human_name, is_human=True),
            BotPlayer(name="Pak RT", personality="imbang"),
            BotPlayer(name="Pak RW", personality="penakut"),
            BotPlayer(name="Pak Sukardi", personality="nekat")
        ]
        self.deck = Deck(config)
        self.discard_pile: List[DiscardEntry] = []  # index 0 adalah kartu buangan TERBARU
        self.current_player_idx = 0
        self.round_number = 1
        self.is_game_over = False
        self.last_action_description = ""

    def start_new_round(self, starting_player_idx: Optional[int] = None):
        """
        Memulai ronde baru: kocok kartu, bagi 7 lembar, dan buka 1 kartu pertama.
        Pemain yang mulai pertama bisa ditentukan (misal pemain nilai tertinggi).
        """
        self.deck = Deck(self.config)
        self.deck.shuffle()
        self.discard_pile.clear()
        self.round_number = 1
        self.last_action_description = ""

        if starting_player_idx is not None:
            self.current_player_idx = starting_player_idx
        else:
            self.current_player_idx = 0

        # Kosongkan tangan dan kartu terbuka pemain
        for p in self.players:
            p.hand.clear()
            p.melds.clear()
            p.open_melds.clear()

        # Bagi 7 kartu ke setiap pemain
        for _ in range(self.config.cards_per_player):
            for p in self.players:
                p.hand.append(self.deck.draw())

        # Buka 1 kartu pertama ke tumpukan buangan
        first_card = self.deck.draw()
        is_dead = False
        if self.config.joker_mode == "OPEN_CARD_WILD":
            # Set kartu liar berdasarkan kartu pertama yang dibuka
            self.deck.setup_open_card_wild(first_card)
            for p in self.players:
                self.deck.mark_wild_cards_in_list(p.hand)
            is_dead = True  # Kartu penentu gantung adalah KARTU MATI (3 sisa aktif di dek/tangan)

        self.discard_pile.append(DiscardEntry(card=first_card, discarded_by=None, is_dead=is_dead))

        # Sortir tangan semua pemain
        for p in self.players:
            p.sort_hand()

    def get_discard_cards(self) -> List[Card]:
        """Mengambil list objek Card dari tumpukan buangan."""
        return [entry.card for entry in self.discard_pile]

    def draw_from_deck(self, player: Player) -> Card:
        """Pemain menarik 1 kartu dari kocokan tertutup."""
        card = self.deck.draw()
        if self.config.joker_mode == "OPEN_CARD_WILD" and self.deck.wild_rank is not None:
            if card.rank == self.deck.wild_rank:
                card.is_joker = True
        player.add_card(card)
        return card

    def scoop_from_discard(
        self,
        player_idx: int,
        depth: int,
        pair_from_hand: List[Card]
    ) -> Tuple[bool, str, List[Card]]:
        """
        Sistem SEROK BUANGAN:
        Mengambil kartu pada kedalaman 'depth' beserta semua kartu di atasnya (0..depth).
        Wajib mengeluarkan minimal 2 kartu pasangan sah terlebih dahulu.
        Wajib memiliki minimal 1 Seri jika ingin mengambil Tris.
        Kartu mati (Joker gantung pembuka) dilarang diambil.
        """
        player = self.players[player_idx]
        if depth >= len(self.discard_pile) or depth >= self.config.max_discard_depth:
            return False, f"Kedalaman {depth+1} melebihi batas maksimal ({self.config.max_discard_depth}) atau kartu hangus!", []

        target_entry = self.discard_pile[depth]
        if getattr(target_entry, "is_dead", False):
            return False, "Kartu pembuka Joker Gantung adalah KARTU MATI dan dilarang diserok!", []

        target_card = target_entry.card
        other_scooped_entries = self.discard_pile[:depth]
        other_scooped_cards = [entry.card for entry in other_scooped_entries]

        # Validasi (termasuk syarat wajib punya Seri jika mau ambil Tris, dan syarat Joker dilarang kecuali untuk TUTUP)
        valid, msg, meld_cards, leftover_cards = check_discard_pickup_validity(
            player.hand, target_card, pair_from_hand, self.config,
            open_melds=player.open_melds, other_scooped_cards=other_scooped_cards,
            return_melds=True
        )
        if not valid:
            return False, msg, []

        # Sah! Kartu yang dipilih dari tangan dikeluarkan
        for c in pair_from_hand:
            player.remove_card(c)

        # Rangkaian yang terbentuk ditaruh terbuka di meja
        player.add_open_meld(meld_cards)

        # Kartu serokan yang tersisa (tidak masuk rangkaian meja) disimpan ke tangan pemain
        if leftover_cards:
            player.receive_cards(leftover_cards)

        # Potong tumpukan buangan dari depth ke belakang
        self.discard_pile = self.discard_pile[depth + 1:]

        extra_msg = f" (+{len(leftover_cards)} kartu serokan disimpan di tangan)" if leftover_cards else ""
        return True, f"Rangkaian ditaruh terbuka di meja: {' '.join(str(c) for c in meld_cards)}{extra_msg}", meld_cards + (leftover_cards or [])

    def execute_discard(self, player_idx: int, card: Card):
        """Pemain membuang 1 kartu ke tumpukan buangan (paling atas)."""
        player = self.players[player_idx]
        player.remove_card(card)
        # Kartu baru dimasukkan di posisi paling depan (index 0)
        self.discard_pile.insert(0, DiscardEntry(card=card, discarded_by=player_idx))

    def handle_round_end_tutup(
        self,
        winner_idx: int,
        closing_card: Card,
        melds: List[Meld],
        is_kocokan_win: bool,
        discarder_idx: Optional[int] = None
    ) -> Dict:
        """
        Menangani penghitungan skor saat ada yang TUTUP:
        - Tutup Kocokan: Pemenang +200, lainnya 0
        - Tutup Cekih:
          * Pemenang: +nilai tutupan (50/100/150) + poin kartu jadi (di tangan & di meja)
          * Yang buang kartu kena denda cekih: -nilai tutupan
          * Pemain kalah lainnya: poin kartu terbuka meja dikurangi denda kartu mentah tangan
        """
        winner = self.players[winner_idx]
        close_val = get_closing_card_value(closing_card, self.config)
        round_scores = {p.name: 0 for p in self.players}
        details = []

        # Cek apakah ada pemain di meja yang pernah narik dari bawah (memiliki kartu terbuka di meja)
        any_player_pulled_from_discard = any(len(p.open_melds) > 0 for p in self.players)

        # Murni Tutup Tangan: menang kocokan DAN tidak ada satupun yang narik dari buangan (meja bersih)
        is_pure_tutup_tangan = is_kocokan_win and (not any_player_pulled_from_discard)

        if is_pure_tutup_tangan:
            # TUTUP TANGAN MURNI: HANYA yang tutup tangan yang dihitung!
            win_bonus = self.config.kocokan_win_bonus
            round_scores[winner.name] = win_bonus
            winner.score += win_bonus
            details.append(f"🏆 {winner.name} TUTUP TANGAN MURNI dengan kartu kunci {closing_card}!")
            details.append(f"Karena tidak ada yang narik dari buangan (meja bersih), HANYA yang tutup tangan yang dihitung: +{win_bonus} poin (Pemain lain 0).")
        else:
            # ADA YANG NARIK DARI BAWAH ATAU TUTUP CEKIHAN:
            # Skor dihitung berdasarkan kartu untuk semua pemain!
            open_melds_objs = [Meld("TERBUKA", m) for m in winner.open_melds]
            all_winner_melds = melds + open_melds_objs
            winner_meld_pts = calculate_meld_points(all_winner_melds, self.config)

            key_discard_penalties = {}
            if is_kocokan_win:
                base_win = self.config.kocokan_win_bonus
                total_win_pts = base_win + winner_meld_pts
                round_scores[winner.name] = total_win_pts
                winner.score += total_win_pts
                details.append(f"🏆 {winner.name} TUTUP KOCOKAN dengan kartu kunci {closing_card}!")
                details.append(f"Bonus Menang: +{base_win} pt, Poin Kartu Jadi: +{winner_meld_pts} pt (Total: +{total_win_pts} pt).")
            else:
                total_win_pts = close_val + winner_meld_pts
                round_scores[winner.name] = total_win_pts
                winner.score += total_win_pts
                details.append(f"🎉 {winner.name} TUTUP CEKIHAN dengan kartu kunci {closing_card} ({closing_card.card_type}: +{close_val} pt)!")
                details.append(f"Poin Kartu Jadi Meja & Tangan: +{winner_meld_pts} pt (Total Menang: +{total_win_pts} pt).")

                # Denda yang buang kartu cekih
                if discarder_idx is not None and discarder_idx != winner_idx:
                    discarder = self.players[discarder_idx]
                    penalty = -close_val
                    round_scores[discarder.name] += penalty
                    discarder.score += penalty
                    key_discard_penalties[discarder.name] = penalty
                    details.append(f"💥 {discarder.name} KENA CEKIH! Denda buang kartu kunci: {penalty} poin.")

            # Kumpulkan seluruh rangkaian kartu yang ada di meja (termasuk milik pemenang & pemain lain)
            all_table_melds = []
            for p_m in self.players:
                all_table_melds.extend(p_m.open_melds)
            all_table_melds.extend([m.cards for m in melds])

            # Hitung skor berdasarkan kartu untuk SEMUA pemain yang kalah:
            breakdowns = {}
            for idx, p in enumerate(self.players):
                open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in p.open_melds], self.config)

                if idx == winner_idx:
                    p.layoff_indices = []
                    continue

                # Otomatis sambungkan kartu terbaik ke meja / rangkai tangan (kartu kuning)
                conn_indices, optimal_pen, hand_meld_pts, layoff_desc = find_optimal_layoffs(p.hand, all_table_melds, self.config)
                p.layoff_indices = conn_indices

                deadwood_cards = [p.hand[i] for i in range(len(p.hand)) if i not in conn_indices]
                saved_cards = [p.hand[i] for i in conn_indices]

                bd = get_deadwood_breakdown(deadwood_cards, self.config)
                bd["open_pts"] = open_pts
                bd["hand_meld_pts"] = hand_meld_pts
                bd["deadwood_pen"] = bd["total_penalty"]
                bd["saved_cards_count"] = len(saved_cards)
                bd["connected_indices"] = conn_indices
                bd["layoff_desc"] = layoff_desc
                breakdowns[p.name] = bd

                deadwood_pen = bd["total_penalty"]
                net_loser_pts = open_pts + hand_meld_pts + deadwood_pen
                round_scores[p.name] += net_loser_pts
                p.score += net_loser_pts

                desc_parts = []
                if open_pts > 0:
                    desc_parts.append(f"Kartu Terbuka di Meja = +{open_pts}")
                if hand_meld_pts > 0:
                    desc_parts.append(f"🟡 {layoff_desc} = +{hand_meld_pts}")
                elif len(saved_cards) > 0:
                    desc_parts.append(f"🟡 {len(saved_cards)} Kartu Tersambung ke Meja (Bebas Denda)")
                if deadwood_pen != 0:
                    if bd["has_joker"]:
                        desc_parts.append(f"Denda Kartu Mentah = {deadwood_pen} (⚠️ Joker Mentah: {bd['joker_pen']} pt, Kartu Lain: {deadwood_pen - bd['joker_pen']} pt)")
                    else:
                        sub_items = []
                        if bd["as_count"] > 0: sub_items.append(f"As: {bd['as_pen']}")
                        if bd["raja_count"] > 0: sub_items.append(f"Raja: {bd['raja_pen']}")
                        if bd["anak_count"] > 0: sub_items.append(f"Anak: {bd['anak_pen']}")
                        sub_str = f" ({', '.join(sub_items)})" if sub_items else ""
                        desc_parts.append(f"Denda Kartu Mentah = {deadwood_pen}{sub_str}")
                if not desc_parts:
                    desc_parts.append("Kartu 0")
                details.append(f"📊 {p.name}: {', '.join(desc_parts)} (Net: {net_loser_pts:+d} pt).")

                orig_has_joker = any(c.is_joker or c.rank == 99 for c in p.hand)
                if orig_has_joker and not bd["has_joker"]:
                    details.append(f"✨ {p.name} BERHASIL menyambungkan Joker ke meja (🟡 Kuning)! Bebas dari denda -250 pt!")
                elif bd["has_joker"]:
                    details.append(f"⚠️ {p.name} kena denda berat {bd['joker_pen']} pt karena masih memegang Joker mentah yang tidak tersambung!")

        return {
            "winner": winner.name,
            "closing_card": str(closing_card),
            "close_value": close_val,
            "is_kocokan": is_kocokan_win,
            "key_discard_penalties": key_discard_penalties,
            "is_pure_tutup_tangan": is_pure_tutup_tangan,
            "round_scores": round_scores,
            "breakdowns": breakdowns if not is_pure_tutup_tangan else {},
            "details": details
        }

    def handle_round_end_draw(self) -> Dict:
        """
        Kocokan habis tanpa ada pemain yang menutup.
        Aturan Pos Ronda:
        - Jika TIDAK ADA pemain yang menarik dari buangan (open_melds kosong semua):
          Murni CUCI TANGAN: Semua pemain mendapatkan 0 poin.
        - Jika ADA pemain yang menarik dari buangan (open_melds ada di meja):
          Skor semua pemain tetap dihitung berdasarkan kartunya:
          * Kartu terbuka di meja = poin positif
          * Kartu tangan tersambung (layoffs) = 🟡 Bebas Denda
          * Kartu mentah di tangan = denda minus
          * Net skor = Poin kartu terbuka di meja + denda kartu mentah di tangan
        """
        has_any_scoop = any(len(p.open_melds) > 0 for p in self.players)
        round_scores = {p.name: 0 for p in self.players}
        details = []

        if not has_any_scoop:
            details.append("💨 KOCOKAN HABIS! Tidak ada pemain yang tutup.")
            details.append("CUCI TANGAN MURNI: Karena tidak ada pemain yang menarik dari buangan di meja, semua pemain mendapatkan 0 poin.")
            return {
                "winner": None,
                "is_kocokan": False,
                "is_cuci_tangan": True,
                "is_pure_tutup_tangan": False,
                "round_scores": round_scores,
                "breakdowns": {},
                "details": details
            }

        # ADA PEMAIN YANG MENARIK DARI BUANGAN:
        details.append("💨 KOCOKAN HABIS! Tidak ada pemain yang tutup.")
        details.append("📊 PERHITUNGAN KARTU MEJA: Karena ada pemain yang menarik kartu buangan ke meja, skor ronde tetap dihitung berdasarkan kartu terbuka & sisa kartu mentah!")

        # Kumpulkan seluruh rangkaian kartu yang ada di meja
        all_table_melds = []
        for p_m in self.players:
            all_table_melds.extend(p_m.open_melds)

        breakdowns = {}
        for p in self.players:
            open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in p.open_melds], self.config)

            # Sambungkan kartu terbaik ke meja / rangkai tangan
            conn_indices, optimal_pen, hand_meld_pts, layoff_desc = find_optimal_layoffs(p.hand, all_table_melds, self.config)
            p.layoff_indices = conn_indices

            deadwood_cards = [p.hand[i] for i in range(len(p.hand)) if i not in conn_indices]
            saved_cards = [p.hand[i] for i in conn_indices]

            bd = get_deadwood_breakdown(deadwood_cards, self.config)
            bd["open_pts"] = open_pts
            bd["hand_meld_pts"] = hand_meld_pts
            bd["deadwood_pen"] = bd["total_penalty"]
            bd["saved_cards_count"] = len(saved_cards)
            bd["connected_indices"] = conn_indices
            bd["layoff_desc"] = layoff_desc
            breakdowns[p.name] = bd

            deadwood_pen = bd["total_penalty"]
            net_pts = open_pts + hand_meld_pts + deadwood_pen
            round_scores[p.name] = net_pts
            p.score += net_pts

            desc_parts = []
            if open_pts > 0:
                desc_parts.append(f"Kartu Terbuka di Meja = +{open_pts}")
            if hand_meld_pts > 0:
                desc_parts.append(f"🟡 {layoff_desc} = +{hand_meld_pts}")
            elif len(saved_cards) > 0:
                desc_parts.append(f"🟡 {len(saved_cards)} Kartu Tersambung ke Meja (Bebas Denda)")
            if deadwood_pen != 0:
                if bd["has_joker"]:
                    desc_parts.append(f"Denda Kartu Mentah = {deadwood_pen} (⚠️ Joker Mentah: {bd['joker_pen']} pt, Kartu Lain: {deadwood_pen - bd['joker_pen']} pt)")
                else:
                    sub_items = []
                    if bd["as_count"] > 0: sub_items.append(f"As: {bd['as_pen']}")
                    if bd["raja_count"] > 0: sub_items.append(f"Raja: {bd['raja_pen']}")
                    if bd["anak_count"] > 0: sub_items.append(f"Anak: {bd['anak_pen']}")
                    sub_str = f" ({', '.join(sub_items)})" if sub_items else ""
                    desc_parts.append(f"Denda Kartu Mentah = {deadwood_pen}{sub_str}")
            if not desc_parts:
                desc_parts.append("Kartu 0")
            details.append(f"📊 {p.name}: {', '.join(desc_parts)} (Net: {net_pts:+d} pt).")

        return {
            "winner": None,
            "is_kocokan": False,
            "is_cuci_tangan": False,
            "is_pure_tutup_tangan": False,
            "round_scores": round_scores,
            "breakdowns": breakdowns,
            "details": details
        }
