"""
Modul Konfigurasi Aturan Remi Cekih Pos Ronda.
Di sini semua aturan bisa diubah dengan mudah (Rule Engine Config).
"""

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class GameConfig:
    # 1. Dasar Permainan
    num_players: int = 4
    cards_per_player: int = 7
    first_round_deck_only: bool = True     # Putaran 1 wajib ambil kocokan
    max_discard_depth: int = 7             # Maksimal mundur 7 kartu di tumpukan buangan

    # 2. Mode Joker
    # 'OPEN_CARD_WILD': 1 kartu bukaan pertama menentukan nilai Joker (3 kartu sejenis jadi Joker)
    # 'TWO_JOKERS': Menggunakan 2 kartu Joker fisik standar dari dek
    # 'NONE': Tanpa Joker
    joker_mode: str = "OPEN_CARD_WILD"

    # 3. Variasi Kombinasi
    allow_pip_tris: bool = False           # False: Hanya Raja (J, Q, K, A) yang boleh Tris. True: Semua angka boleh
    allow_gap_pickup: bool = False         # False: Wajib sambung ujung (2&3 ambil 4). True: Boleh sisip (2&4 ambil 3)

    # 4. Nilai Tutupan (Kartu Kunci)
    close_points: Dict[str, int] = field(default_factory=lambda: {
        "ANAK": 50,    # Angka 2 - 10
        "RAJA": 100,   # J, Q, K
        "AS": 150      # As
    })

    # Bonus jika Tutup Kocokan (Narik Sendiri)
    kocokan_win_bonus: int = 200

    # 5. Nilai Kartu Jadi (Masuk Rangkaian)
    melded_points: Dict[str, int] = field(default_factory=lambda: {
        "ANAK": 5,
        "RAJA": 10,
        "AS": 15
    })

    # 6. Denda Kartu Mentah (Sisa di Tangan yang Tidak Jadi)
    deadwood_penalty: Dict[str, int] = field(default_factory=lambda: {
        "ANAK": -5,
        "RAJA": -10,
        "AS": -15,
        "JOKER": -250
    })

    # Penalti Pemain yang Kena Cekih (minus sebesar nilai kartu tutupan)
    cekih_penalty_enabled: bool = True

    # Jika kocokan habis tanpa ada yang tutup -> Cuci Tangan (semua 0)
    deck_empty_is_draw: bool = True

    # Target skor kemenangan permainan (jika main berseri)
    target_score: int = 500


def get_default_config() -> GameConfig:
    """Konfigurasi otentik Pos Ronda."""
    return GameConfig()

def get_casual_config() -> GameConfig:
    """Konfigurasi santai: tris anak boleh, sisip boleh, 2 joker fisik."""
    return GameConfig(
        joker_mode="TWO_JOKERS",
        allow_pip_tris=True,
        allow_gap_pickup=True
    )
