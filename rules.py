"""
Modul Rules Engine untuk Remi Cekih Pos Ronda.
Menangani:
- Validasi Seri (Run / Straight Flush) & Tris (Set) dengan Joker
- Pengecekan syarat ambil buangan (Serok Buangan)
- Pengecekan kondisi Tutup (Cekih / Tutup Kocokan) & Cekih Gantung
- Perhitungan skor kartu jadi, denda kartu mentah, dan penalti cekih
"""

from typing import List, Tuple, Optional, Dict, Set
from collections import Counter
from itertools import combinations
from card import Card
from config import GameConfig

class Meld:
    def __init__(self, meld_type: str, cards: List[Card]):
        self.meld_type = meld_type  # 'SERI' atau 'TRIS'
        self.cards = cards

    def __repr__(self):
        return f"{self.meld_type}({', '.join(str(c) for c in self.cards)})"


def is_valid_tris(cards: List[Card], config: GameConfig) -> bool:
    """
    Validasi Tris (Set): 3 atau 4 kartu berangka sama dengan kembang berbeda.
    Joker bisa menggantikan kartu yang kurang.
    Jika allow_pip_tris == False, hanya kartu Raja (J, Q, K, A) yang boleh Tris.
    """
    if len(cards) not in (3, 4):
        return False

    non_jokers = [c for c in cards if not c.is_joker and c.rank != 99]
    num_jokers = len(cards) - len(non_jokers)

    if not non_jokers:
        # Semua joker? Di remi pos ronda tidak ada tris full joker
        return False

    target_rank = non_jokers[0].rank
    # Cek apakah semua non-joker punya angka yang sama
    if not all(c.rank == target_rank for c in non_jokers):
        return False

    # Cek kembang non-joker harus berbeda
    suits = [c.suit for c in non_jokers]
    if len(suits) != len(set(suits)):
        return False

    # Cek aturan Raja-only vs Pip-Tris
    if not config.allow_pip_tris:
        # Hanya J (11), Q (12), K (13), A (14) yang boleh
        if target_rank not in (11, 12, 13, 14):
            return False

    return True


def is_valid_seri(cards: List[Card], config: GameConfig) -> bool:
    """
    Validasi Seri (Straight Flush): minimal 3 kartu berurutan kembang sama.
    Aturan Pos Ronda Remi Cekih:
    - Seri Anak: rentang angka 2 sampai 10 (kembang sama).
    - Seri Raja: J - Q - K (rank 11, 12, 13, kembang sama).
    - As (A / rank 14) dilarang ikut Seri ("A hanya bisa di tris... karena A tidak ada temen nya lagi").
    - Dilarang mencampur kartu Anak dan Raja (misal 9-10-J atau 10-J-Q dilarang).
    """
    if len(cards) < 3:
        return False

    non_jokers = [c for c in cards if not c.is_joker and c.rank != 99]
    num_jokers = len(cards) - len(non_jokers)

    if not non_jokers:
        return False

    # As (14) dilarang ikut seri
    if any(c.rank == 14 for c in non_jokers):
        return False

    # Semua non-joker harus memiliki kembang yang sama
    target_suit = non_jokers[0].suit
    if not all(c.suit == target_suit for c in non_jokers):
        return False

    # Cek apakah campuran Anak (2..10) dan Raja (11..13)
    has_anak = any(2 <= c.rank <= 10 for c in non_jokers)
    has_raja = any(11 <= c.rank <= 13 for c in non_jokers)
    if has_anak and has_raja:
        return False  # Dilarang campur anak dan raja!

    if has_raja:
        # Seri Raja: J (11), Q (12), K (13) kembang sama (maksimal 3 kartu)
        if len(cards) != 3:
            return False
        ranks = [c.rank for c in non_jokers]
        # Tidak boleh ada rank kembar
        if len(ranks) != len(set(ranks)):
            return False
        # Semua rank non-joker harus di rentang 11..13
        if not all(11 <= r <= 13 for r in ranks):
            return False
        return True

    # Seri Anak: rentang 2..10
    if not all(2 <= c.rank <= 10 for c in non_jokers):
        return False

    # Cek sequence berurutan di rentang 2..10
    unique_ranks = sorted(list(set(c.rank for c in non_jokers)))
    if len(unique_ranks) != len(non_jokers):
        return False

    min_r = unique_ranks[0]
    max_r = unique_ranks[-1]
    span = max_r - min_r + 1
    missing = span - len(unique_ranks)

    if missing > num_jokers:
        return False

    total_len = len(cards)
    if total_len > 9:  # Rentang 2..10 maksimal 9 kartu
        return False

    extra_jokers = num_jokers - missing
    # Ruang ekspansi ke kiri = min_r - 2
    # Ruang ekspansi ke kanan = 10 - max_r
    if extra_jokers > (min_r - 2) + (10 - max_r):
        return False

    return True


def is_valid_meld(cards: List[Card], config: GameConfig) -> Tuple[bool, str]:
    """Cek apakah sekumpulan kartu merupakan kombinasi sah (Seri atau Tris)."""
    if is_valid_seri(cards, config):
        return True, "SERI"
    if is_valid_tris(cards, config):
        return True, "TRIS"
    return False, ""


def find_scoop_combination(
    cards_from_hand: List[Card],
    target_card: Card,
    other_scooped_cards: Optional[List[Card]],
    config: GameConfig
) -> Tuple[Optional[List[Card]], Optional[List[Card]], Optional[str]]:
    """
    Mencari kombinasi meld yang sah saat serok buangan.
    Memberi fleksibilitas penuh kepada pemain:
    1. Coba meld HANYA dari cards_from_hand + target_card (sisa other_scooped_cards masuk tangan)
    2. Coba meld dari cards_from_hand + target_card + semua other_scooped_cards (semua keluar ke meja)
    3. Coba meld dari cards_from_hand + target_card + subset other_scooped_cards (yang nyambung keluar ke meja, sisanya masuk tangan)
    """
    others = list(other_scooped_cards or [])
    base = list(cards_from_hand) + [target_card]

    # Opsi 1: Hanya kartu pilihan tangan + target buangan
    valid1, type1 = is_valid_meld(base, config)
    if valid1:
        return base, others, type1

    # Opsi 2: Gabungkan dengan semua kartu serokan yang ikut terbawa
    if others:
        full = base + others
        valid2, type2 = is_valid_meld(full, config)
        if valid2:
            return full, [], type2

        # Opsi 3: Cari subset terpanjang dari kartu serokan yang ikut menyambung
        for k in range(len(others) - 1, 0, -1):
            for combo in combinations(others, k):
                candidate = base + list(combo)
                valid_k, type_k = is_valid_meld(candidate, config)
                if valid_k:
                    leftover = [c for c in others if c not in combo]
                    return candidate, leftover, type_k

    return None, None, None


def check_discard_pickup_validity(
    hand: List[Card],
    target_card: Card,
    cards_from_hand: List[Card],
    config: GameConfig,
    open_melds: Optional[List[List[Card]]] = None,
    other_scooped_cards: Optional[List[Card]] = None,
    return_melds: bool = False
):
    """
    Validasi saat pemain ingin mengambil kartu buangan:
    - cards_from_hand: minimal 2 kartu dari tangan
    - target_card: kartu buangan yang mau diambil
    - other_scooped_cards: kartu buangan yang ikut terserok di atas target
    - return_melds: jika True, mengembalikan (valid, msg, meld_cards, leftover_cards)
    """
    if len(cards_from_hand) < 2:
        res = (False, "Minimal mengeluarkan 2 kartu dari tangan!")
        return res + (None, None) if return_melds else res

    for c in cards_from_hand:
        if c not in hand:
            res = (False, f"Kartu {c} tidak ada di tangan pemain!")
            return res + (None, None) if return_melds else res

    meld_cards, leftover_cards, meld_type = find_scoop_combination(
        cards_from_hand, target_card, other_scooped_cards, config
    )

    if not meld_cards or not meld_type:
        res = (False, f"Kartu yang dipilih dari tangan dan buangan tidak membentuk Seri (anak 2..10) atau Tris yang sah!")
        return res + (None, None) if return_melds else res

    # SYARAT JOKER: Dilarang jadi pelengkap serok kartu di bawah kecuali langsung untuk TUTUP
    has_joker_companion = any(c.is_joker for c in cards_from_hand)
    if has_joker_companion:
        simulated_hand = [c for c in hand if c not in cards_from_hand]
        if leftover_cards:
            simulated_hand.extend(leftover_cards)
        simulated_open_melds = [list(om) for om in (open_melds or [])] + [meld_cards]
        tutup_opts = check_tutup(simulated_hand, config, open_melds=simulated_open_melds)
        if not tutup_opts:
            res = (False, "Joker dilarang dijadikan pelengkap menarik kartu buangan di bawah, kecuali jika serokan tersebut langsung untuk TUTUP (Cekih atau Tutup Tangan)!")
            return res + (None, None) if return_melds else res

    # Pengecekan aturan Sisip vs Gandeng jika 2 kartu tangan
    if meld_type == "SERI" and len(cards_from_hand) == 2 and not config.allow_gap_pickup:
        c1, c2 = cards_from_hand
        if not c1.is_joker and not c2.is_joker:
            r1, r2 = sorted([c1.rank, c2.rank])
            is_adjacent = (r2 - r1 == 1)
            if not is_adjacent:
                res = (False, f"Aturan melarang sisip/jepit! Kartu {c1} dan {c2} harus gandeng berurutan (Aktifkan opsi Tarik Sisip di aturan jika ingin memperbolehkan).")
                return res + (None, None) if return_melds else res

    # SYARAT KHUSUS TRIS:
    # "raja jqk dan A hanya bisa di tris walaupun belum punya seri karena A tidak ada temen nya lagi"
    if meld_type == "TRIS":
        non_jokers = [c for c in meld_cards if not c.is_joker and c.rank != 99]
        target_rank = non_jokers[0].rank if non_jokers else 0

        # Khusus As (14) dan Raja (11, 12, 13) yang jalurnya Tris:
        # Boleh diambil langsung dari bawah walaupun belum punya rangkaian Seri!
        is_exempt_from_seri = (target_rank in (11, 12, 13, 14))

        if not is_exempt_from_seri:
            has_seri = False
            if open_melds:
                for om in open_melds:
                    if is_valid_seri(om, config):
                        has_seri = True
                        break

            if not has_seri:
                remaining_hand = [c for c in hand if c not in cards_from_hand]
                for k in range(3, min(len(remaining_hand) + 1, 8)):
                    for combo in combinations(remaining_hand, k):
                        if is_valid_seri(list(combo), config):
                            has_seri = True
                            break
                    if has_seri:
                        break

            if not has_seri:
                res = (False, "Dilarang mengambil Tris! Wajib memiliki minimal 1 rangkaian Seri terlebih dahulu (baik sudah terbuka di meja atau tersusun di tangan).")
                return res + (None, None) if return_melds else res

    extra_msg = f" (+{len(leftover_cards)} kartu serokan disimpan di tangan)" if leftover_cards else ""
    success_msg = f"Sah! Membentuk {meld_type} ({len(meld_cards)} kartu terbuka di meja){extra_msg}."
    if return_melds:
        return True, success_msg, meld_cards, leftover_cards
    return True, success_msg


def partition_into_melds(cards: List[Card], config: GameConfig) -> Optional[List[Meld]]:
    """
    Mencoba mempartisi semua kartu dalam list menjadi kumpulan Meld yang sah (ukuran >= 3 s/d 7).
    Menggunakan algoritma backtracking efisien.
    """
    if not cards:
        return []

    if len(cards) < 3:
        return None

    # Helper recursive
    def solve(remaining: List[Card]) -> Optional[List[Meld]]:
        if not remaining:
            return []
        if len(remaining) < 3:
            return None

        first_card = remaining[0]
        rest = remaining[1:]

        # Coba buat meld ukuran 3, 4, 5, 6, 7 yang melibatkan first_card
        for meld_size in (3, 4, 5, 6, 7):
            if meld_size > len(remaining):
                continue
            for combo in combinations(rest, meld_size - 1):
                candidate = [first_card] + list(combo)
                valid, m_type = is_valid_meld(candidate, config)
                if valid:
                    next_remaining = remaining.copy()
                    for c in candidate:
                        next_remaining.remove(c)
                    sub_result = solve(next_remaining)
                    if sub_result is not None:
                        return [Meld(m_type, candidate)] + sub_result
        return None

    # Urutkan kartu untuk deterministic search
    sorted_cards = sorted(cards, key=lambda c: (c.suit or "", c.rank))
    return solve(sorted_cards)


def check_tutup(
    hand: List[Card],
    config: GameConfig,
    open_melds: Optional[List[List[Card]]] = None
) -> List[Tuple[Card, List[Meld]]]:
    """
    Mengecek apakah kartu di tangan bisa TUTUP.
    Kondisi tutup: SEMUA kartu di tangan kecuali TEPAT 1 KARTU dapat dipartisi
    menjadi kombinasi (meld) yang sah, atau disambung ke open_melds yang sudah ada (misal Joker disatuin).
    Mengembalikan daftar opsi: [(kartu_tutup, [daftar_meld_terbentuk])]
    """
    valid_tutup_options = []
    seen_closing_cards = set()

    for i, candidate_close_card in enumerate(hand):
        if candidate_close_card in seen_closing_cards:
            continue
        seen_closing_cards.add(candidate_close_card)

        # Coba pisahkan candidate_close_card, sisa kartu harus bisa dipartisi penuh
        other_cards = hand[:i] + hand[i+1:]
        melds = partition_into_melds(other_cards, config)
        if melds is not None:
            valid_tutup_options.append((candidate_close_card, melds))
        elif open_melds:
            # Coba satukan sisa kartu (seperti Joker atau kartu sambungan) ke open_melds di meja
            for k in range(1, len(other_cards) + 1):
                found_match = False
                for attach_subset in combinations(other_cards, k):
                    attach_list = list(attach_subset)
                    rem_hand = [c for c in other_cards if c not in attach_list]
                    for om in open_melds:
                        expanded_meld = list(om) + attach_list
                        valid, m_type = is_valid_meld(expanded_meld, config)
                        if valid:
                            if not rem_hand:
                                valid_tutup_options.append((candidate_close_card, [Meld(m_type, expanded_meld)]))
                                found_match = True
                                break
                            sub_melds = partition_into_melds(rem_hand, config)
                            if sub_melds is not None:
                                valid_tutup_options.append((candidate_close_card, [Meld(m_type, expanded_meld)] + sub_melds))
                                found_match = True
                                break
                    if found_match:
                        break
                if found_match:
                    break

    return valid_tutup_options


def check_is_cekih(
    hand: List[Card],
    config: GameConfig,
    open_melds: Optional[List[List[Card]]] = None
) -> Tuple[bool, str, List[Card]]:
    """
    Validasi resmi deklarasi CEKIH:
    Pemain hanya boleh teriak 'CEKIH' jika:
    1. Kartunya sudah siap tutup (menunggu kartu kunci), ATAU
    2. Ada kartu di dek yang jika masuk ke tangan langsung membuat tangan TUTUP.
    Jika tidak memenuhi, dilarang main-main atau bohong bilang Cekih!
    """
    waiting_cards = []
    seen_keys = set()
    test_deck = [Card(r, s) for r in range(2, 15) for s in ["HATI", "SEKOP", "KERITING", "TAHU"]]
    test_deck.append(Card(99, None, is_joker=True))

    # Cek kartu apa saja yang jika ditarik langsung membuat tangan TUTUP
    for candidate in test_deck:
        opts = check_tutup(hand + [candidate], config, open_melds)
        if opts:
            key = (candidate.rank, candidate.suit, candidate.is_joker)
            if key not in seen_keys:
                seen_keys.add(key)
                waiting_cards.append(candidate)

    # Cek juga apakah tangan saat ini sudah memiliki kombinasi tutup mandiri
    direct_opts = check_tutup(hand, config, open_melds)
    if direct_opts:
        for close_card, _ in direct_opts:
            key = (close_card.rank, close_card.suit, close_card.is_joker)
            if key not in seen_keys:
                seen_keys.add(key)
                waiting_cards.append(close_card)

    if waiting_cards:
        waiting_sample = ", ".join(str(c) for c in waiting_cards[:4])
        more = f" (+{len(waiting_cards) - 4} kartu lainnya)" if len(waiting_cards) > 4 else ""
        msg = f"SAH CEKIH! Anda resmi nunggu kartu kunci: {waiting_sample}{more}."
        return True, msg, waiting_cards

    return False, "Kartu Anda BELUM CEKIH! Masih butuh menyusun rangkaian lagi dan belum berjarak 1 kartu dari tutup. Dilarang main-main bilang cekih!", []


def calculate_meld_points(melds: List[Meld], config: GameConfig) -> int:
    """
    Menghitung total poin kartu yang sudah jadi (masuk rangkaian).
    Aturan Pos Ronda:
    - Rangkaian As (As murni atau As + Joker): Tiap kartu dinilai 15 pt (3 kartu = 45 pt).
    - Rangkaian Raja (J, Q, K atau Raja + Joker): Tiap kartu dinilai 10 pt (3 kartu = 30 pt).
    - Rangkaian Anak (2..10 atau Anak + Joker): Tiap kartu dinilai 5 pt (3 kartu = 15 pt).
    Joker mengambil nilai setara kartu dalam rangkaian tersebut.
    """
    total = 0
    for m in melds:
        non_jokers = [c for c in m.cards if not c.is_joker and c.rank != 99]
        if not non_jokers:
            meld_type = "ANAK"
        elif any(c.rank == 14 for c in non_jokers):
            meld_type = "AS"
        elif any(c.rank in (11, 12, 13) for c in non_jokers):
            meld_type = "RAJA"
        else:
            meld_type = "ANAK"

        pts_per_card = config.melded_points.get(meld_type, 5)
        for c in m.cards:
            if c.is_joker:
                total += pts_per_card
            elif c.rank == 14:
                total += config.melded_points["AS"]
            elif c.rank in (11, 12, 13):
                total += config.melded_points["RAJA"]
            else:
                total += config.melded_points["ANAK"]
    return total


def calculate_deadwood_penalty(cards: List[Card], config: GameConfig) -> int:
    """Menghitung total minus kartu mentah yang tersisa di tangan."""
    penalty = 0
    for c in cards:
        if c.is_joker or c.rank == 99:
            penalty += config.deadwood_penalty["JOKER"]  # -250
        elif c.rank == 14:
            penalty += config.deadwood_penalty["AS"]     # -15
        elif c.rank in (11, 12, 13):
            penalty += config.deadwood_penalty["RAJA"]   # -10
        else:
            penalty += config.deadwood_penalty["ANAK"]   # -5
    return penalty


def get_deadwood_breakdown(cards: List[Card], config: GameConfig) -> Dict:
    """Menghitung rincian denda kartu mentah per kategori kartu."""
    joker_cards = []
    as_cards = []
    raja_cards = []
    anak_cards = []

    for c in cards:
        if c.is_joker or c.rank == 99:
            joker_cards.append(c)
        elif c.rank == 14:
            as_cards.append(c)
        elif c.rank in (11, 12, 13):
            raja_cards.append(c)
        else:
            anak_cards.append(c)

    joker_pen = len(joker_cards) * config.deadwood_penalty["JOKER"]
    as_pen = len(as_cards) * config.deadwood_penalty["AS"]
    raja_pen = len(raja_cards) * config.deadwood_penalty["RAJA"]
    anak_pen = len(anak_cards) * config.deadwood_penalty["ANAK"]
    total = joker_pen + as_pen + raja_pen + anak_pen

    return {
        "total_penalty": total,
        "joker_count": len(joker_cards),
        "joker_pen": joker_pen,
        "as_count": len(as_cards),
        "as_pen": as_pen,
        "raja_count": len(raja_cards),
        "raja_pen": raja_pen,
        "anak_count": len(anak_cards),
        "anak_pen": anak_pen,
        "has_joker": len(joker_cards) > 0
    }


def get_closing_card_value(closing_card: Card, config: GameConfig) -> int:
    """Mendapatkan nilai tutupan (kartu kunci): Anak: 50, Raja: 100, As: 150."""
    card_type = closing_card.card_type
    return config.close_points.get(card_type, 50)


def can_partition_layoffs(subset_cards: List[Card], table_melds: List[List[Card]], config: GameConfig) -> bool:
    """
    Mengecek secara rekursif apakah sekumpulan kartu (subset_cards) dapat dihabiskan dengan:
    1. Membentuk rangkaian sah mandiri (Seri atau Tris ukuran >= 3)
    2. Disambungkan/ditempelkan ke salah satu meld terbuka di table_melds
    """
    if not subset_cards:
        return True

    # 1. Coba bentuk meld mandiri dari subset
    for k in (3, 4, 5, 6, 7):
        if k > len(subset_cards):
            break
        for m_comb in combinations(subset_cards, k):
            m_list = list(m_comb)
            valid, _ = is_valid_meld(m_list, config)
            if valid:
                rem = [c for c in subset_cards if c not in m_list]
                if can_partition_layoffs(rem, table_melds, config):
                    return True

    # 2. Coba sambungkan ke salah satu rangkaian meja
    for m_idx, om in enumerate(table_melds):
        for k in range(1, len(subset_cards) + 1):
            for att_comb in combinations(subset_cards, k):
                att_list = list(att_comb)
                valid, _ = is_valid_meld(om + att_list, config)
                if valid:
                    rem = [c for c in subset_cards if c not in att_list]
                    new_table = [om + att_list if i == m_idx else m for i, m in enumerate(table_melds)]
                    if can_partition_layoffs(rem, new_table, config):
                        return True

    return False


def evaluate_hand_subset(sub_cards: List[Card], table_melds: List[List[Card]], config: GameConfig) -> Tuple[bool, List[Meld], int, str]:
    """
    Mengevaluasi sekumpulan kartu tangan apakah membentuk rangkaian sah mandiri atau menyambung ke meja.
    Mengembalikan (is_valid, formed_melds, hand_meld_pts, description).
    """
    if not sub_cards:
        return False, [], 0, ""

    # 1. Cek meld langsung (Tris atau Seri ukuran 3..7)
    valid, m_type = is_valid_meld(sub_cards, config)
    if valid:
        m = Meld(m_type, sub_cards)
        pts = calculate_meld_points([m], config)
        non_jokers = [c for c in sub_cards if not c.is_joker and c.rank != 99]
        rn = non_jokers[0].rank_name if non_jokers else "Joker"
        desc = f"Tris {rn}" if m_type == "TRIS" else f"Seri {sub_cards[0].suit}"
        return True, [m], pts, desc

    # 2. Cek apakah partisi ke beberapa meld
    pm = partition_into_melds(sub_cards, config)
    if pm:
        pts = calculate_meld_points(pm, config)
        desc = " + ".join(m.meld_type for m in pm)
        return True, pm, pts, desc

    # 3. Cek apakah menyambung/menempel ke salah satu open meld di meja
    for om in table_melds:
        valid_att, m_type_att = is_valid_meld(om + sub_cards, config)
        if valid_att:
            temp_meld = Meld(m_type_att, sub_cards)
            pts = calculate_meld_points([temp_meld], config)
            desc = f"Sambung Meja ({len(sub_cards)} kartu)"
            return True, [temp_meld], pts, desc

    # 4. Cek kombinasi campuran via can_partition_layoffs
    if can_partition_layoffs(sub_cards, table_melds, config):
        pts = sum(15 if c.rank == 14 else (10 if c.rank in (11, 12, 13) else 5) for c in sub_cards)
        return True, [Meld("SAMBUNG", sub_cards)], pts, "Kombinasi Meja"

    return False, [], 0, ""


def find_all_layoff_options(
    hand: List[Card],
    table_melds: List[List[Card]],
    config: GameConfig,
    open_table_pts: int = 0
) -> List[Dict]:
    """
    Mencari SELURUH opsi sambungan kartu tangan yang sah saat permainan berakhir (Showdown).
    Memberikan kebebasan penuh kepada pemain untuk memilih:
    misal pilih AA + Joker (Tris As) vs JJ + Joker (Tris Jack)!
    Mengembalikan daftar opsi terurut dari yang menghasilkan total skor tertinggi.
    """
    n = len(hand)
    options = []
    seen_combos = set()

    # Opsi dasar: Tidak ada kartu yang disambung (semua simpan di tangan)
    pen_0 = calculate_deadwood_penalty(hand, config)
    options.append({
        "id": "opt_none",
        "indices": [],
        "cards": [],
        "title": "Simpan Semua di Tangan (Tanpa Sambung)",
        "hand_meld_pts": 0,
        "deadwood_pen": pen_0,
        "net_pts": pen_0,
        "total_score": open_table_pts + pen_0,
        "is_recommended": False
    })

    # Telusuri semua kombinasi subset kartu tangan
    for size in range(1, n + 1):
        for combo in combinations(range(n), size):
            combo_tuple = tuple(sorted(combo))
            if combo_tuple in seen_combos:
                continue

            sub = [hand[i] for i in combo_tuple]
            rem = [hand[i] for i in range(n) if i not in combo_tuple]
            ok, melds, meld_pts, desc = evaluate_hand_subset(sub, table_melds, config)
            if ok:
                seen_combos.add(combo_tuple)
                pen = calculate_deadwood_penalty(rem, config) if rem else 0
                net = meld_pts + pen
                card_labels = [c.rank_name for c in sub]
                title = f"{desc} ({', '.join(card_labels)})"
                options.append({
                    "id": f"opt_{len(options)}",
                    "indices": list(combo_tuple),
                    "cards": [str(c) for c in sub],
                    "title": title,
                    "hand_meld_pts": meld_pts,
                    "deadwood_pen": pen,
                    "net_pts": net,
                    "total_score": open_table_pts + net,
                    "is_recommended": False
                })

    # Urutkan berdasarkan total score tertinggi
    options.sort(key=lambda o: (o["total_score"], o["hand_meld_pts"]), reverse=True)
    if options:
        options[0]["is_recommended"] = True

    return options


def find_optimal_layoffs(
    hand: List[Card],
    table_melds: List[List[Card]],
    config: GameConfig
) -> Tuple[List[int], int, int, str]:
    """
    Mencari kombinasi sambungan terbaik dari kartu di tangan yang memaksimalkan total skor.
    Mengembalikan (best_indices, deadwood_pen, hand_meld_pts, title).
    """
    opts = find_all_layoff_options(hand, table_melds, config, open_table_pts=0)
    if opts:
        best = opts[0]
        return best["indices"], best["deadwood_pen"], best["hand_meld_pts"], best["title"]
    return [], calculate_deadwood_penalty(hand, config), 0, "Simpan Semua di Tangan"


def validate_layoff_selection(
    hand: List[Card],
    selected_indices: List[int],
    table_melds: List[List[Card]],
    config: GameConfig
) -> Tuple[bool, str, int, int, str]:
    """
    Memvalidasi apakah kartu-kartu yang dipilih manual oleh pemain sah untuk disambung ke meja.
    Mengembalikan (is_valid, pesan, hand_meld_pts, sisa_denda_deadwood, meld_title).
    """
    if not selected_indices:
        pen = calculate_deadwood_penalty(hand, config)
        return True, "Semua kartu disimpan di tangan.", 0, pen, "Simpan Semua di Tangan"

    valid_indices = [i for i in selected_indices if 0 <= i < len(hand)]
    sub = [hand[i] for i in valid_indices]
    rem = [hand[i] for i in range(len(hand)) if i not in valid_indices]

    ok, melds, meld_pts, desc = evaluate_hand_subset(sub, table_melds, config)
    if ok:
        pen = calculate_deadwood_penalty(rem, config) if rem else 0
        card_labels = [c.rank_name for c in sub]
        title = f"{desc} ({', '.join(card_labels)})"
        return True, f"Sah! {title} berhasil dibentuk (+{meld_pts} pt, denda {pen} pt)!", meld_pts, pen, title
    else:
        pen = calculate_deadwood_penalty(hand, config)
        return False, "Kombinasi kartu yang dipilih tidak cocok disambung ke meja atau tidak membentuk rangkaian sah!", 0, pen, ""

