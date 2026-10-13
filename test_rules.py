"""
Unit test untuk memastikan logika Remi Cekih 100% akurat sesuai contoh user.
"""

from card import Card
from config import GameConfig
from rules import (
    is_valid_seri, is_valid_tris, is_valid_meld,
    check_discard_pickup_validity, check_tutup,
    calculate_deadwood_penalty, get_closing_card_value
)

def test_all():
    config = GameConfig(
        allow_pip_tris=False,
        allow_gap_pickup=False,
        joker_mode="OPEN_CARD_WILD"
    )

    # 1. Test Tris Raja vs Anak
    tris_king = [Card(13, "SEKOP"), Card(13, "HATI"), Card(13, "KERITING")]
    tris_three = [Card(3, "SEKOP"), Card(3, "HATI"), Card(3, "KERITING")]
    assert is_valid_tris(tris_king, config) == True, "Tris Raja (K) harus sah!"
    assert is_valid_tris(tris_three, config) == False, "Tris Anak (3) dilarang jika allow_pip_tris=False!"

    # 2. Test Seri dengan Joker
    joker = Card(99, None, is_joker=True)
    seri_with_joker = [Card(6, "TAHU"), Card(7, "TAHU"), joker]
    assert is_valid_seri(seri_with_joker, config) == True, "6, 7, Joker harus sah jadi Seri!"

    # 3. Test Syarat Sisip vs Sambung Ujung
    c2 = Card(2, "TAHU")
    c3 = Card(3, "TAHU")
    c4 = Card(4, "TAHU")
    # Kasus sambung ujung: tangan pegang 2 & 3, mau ambil 4
    valid, msg = check_discard_pickup_validity([c2, c3], c4, [c2, c3], config)
    assert valid == True, f"Sambung ujung harus sah: {msg}"

    # Kasus sisip: tangan pegang 2 & 4, mau ambil 3
    valid, msg = check_discard_pickup_validity([c2, c4], c3, [c2, c4], config)
    assert valid == False, f"Sisip harus gagal saat allow_gap_pickup=False: {msg}"

    # 4. Test Kasus Contoh User:
    # Tris Raja K (3) + 6-7-8 tahu & Joker (4) + AS (1)
    # Total 8 kartu di tangan setelah narik kartu 8 tahu
    k_sekop = Card(13, "SEKOP")
    k_hati = Card(13, "HATI")
    k_tahu = Card(13, "TAHU")
    c6_tahu = Card(6, "TAHU")
    c7_tahu = Card(7, "TAHU")
    c8_tahu = Card(8, "TAHU")
    as_hati = Card(14, "HATI")

    hand_8 = [k_sekop, k_hati, k_tahu, c6_tahu, c7_tahu, c8_tahu, joker, as_hati]
    tutup_opts = check_tutup(hand_8, config)
    assert len(tutup_opts) > 0, "Harus bisa TUTUP!"
    close_card, melds = tutup_opts[0]
    assert close_card.rank == 14, "Kartu penutup harus As!"
    assert get_closing_card_value(close_card, config) == 150, "Tutupan As harus bernilai 150!"

    # 5. Test Penalti
    unmatched = [Card(3, "SEKOP"), Card(12, "HATI"), Card(14, "SEKOP"), joker]
    # Anak: -5, Raja: -10, As: -15, Joker: -250 -> Total = -280
    penalty = calculate_deadwood_penalty(unmatched, config)
    assert penalty == -280, f"Penalti harus -280, tapi dapat {penalty}"

    # 6. Test Multi-Card Discard Pickup (4-5 kartu sambung)
    hand_multi = [Card(5, "SEKOP"), Card(6, "SEKOP"), Card(7, "SEKOP")]
    target_discard = Card(8, "SEKOP")
    valid_pickup, msg_pickup = check_discard_pickup_validity(hand_multi, target_discard, hand_multi, config)
    assert valid_pickup == True, f"Serok dengan 3 kartu dari tangan (total 4 kartu) harus sah: {msg_pickup}"

    # 7. Test Cekih Gantung / Tutup dengan Joker disatukan ke Open Meld
    open_meld_existing = [[Card(5, "HATI"), Card(6, "HATI"), Card(7, "HATI")]]
    hand_with_joker_close = [joker, Card(2, "KERITING")]  # 2 kartu: 1 joker + 1 kartu kunci
    tutup_joker_opts = check_tutup(hand_with_joker_close, config, open_melds=open_meld_existing)
    assert len(tutup_joker_opts) > 0, "Joker harus bisa disatukan ke open meld meja untuk menutup!"
    assert tutup_joker_opts[0][0].rank == 2, "Kartu penutup harus 2 Keriting!"

    # 8. Test Syarat Ambil Tris (Raja JQK & As BOLEH tanpa seri; Anak WAJIB ada Seri)
    pair_as = [Card(14, "SEKOP"), Card(14, "HATI")]
    target_as = Card(14, "TAHU")
    hand_no_seri_as = pair_as + [Card(2, "SEKOP"), Card(4, "HATI"), Card(8, "KERITING")]

    # 8a: Tris As (14) & Tris Raja (11..13) bebas dari syarat Seri ("A & Raja hanya bisa di tris walaupun belum punya seri")
    valid_tris_as, msg_as = check_discard_pickup_validity(hand_no_seri_as, target_as, pair_as, config, open_melds=[])
    assert valid_tris_as == True, f"Tris As harus boleh diambil meski belum punya Seri: {msg_as}"

    pair_q = [Card(12, "SEKOP"), Card(12, "HATI")]
    target_q = Card(12, "TAHU")
    hand_no_seri_q = pair_q + [Card(2, "SEKOP"), Card(4, "HATI"), Card(8, "KERITING")]
    valid_tris_q, msg_q = check_discard_pickup_validity(hand_no_seri_q, target_q, pair_q, config, open_melds=[])
    assert valid_tris_q == True, f"Tris Raja harus boleh diambil meski belum punya Seri: {msg_q}"

    # 8b: Tris Anak (jika allow_pip_tris=True) WAJIB ada Seri terlebih dahulu
    config_pip = GameConfig(allow_pip_tris=True)
    pair_7 = [Card(7, "SEKOP"), Card(7, "HATI")]
    target_7 = Card(7, "TAHU")
    hand_no_seri_7 = pair_7 + [Card(2, "SEKOP"), Card(4, "HATI"), Card(8, "KERITING")]
    valid_tris_7_no, msg_fail = check_discard_pickup_validity(hand_no_seri_7, target_7, pair_7, config_pip, open_melds=[])
    assert valid_tris_7_no == False, "Tris Anak tanpa Seri harus ditolak!"
    assert "Seri" in msg_fail, f"Pesan error salah: {msg_fail}"

    # 8c: Tris Anak dengan Seri di tangan -> BOLEH!
    hand_seri_7 = pair_7 + [Card(2, "KERITING"), Card(3, "KERITING"), Card(4, "KERITING")]
    valid_tris_7_yes, msg_ok = check_discard_pickup_validity(hand_seri_7, target_7, pair_7, config_pip, open_melds=[])
    assert valid_tris_7_yes == True, f"Tris Anak dengan Seri harus diizinkan: {msg_ok}"

    # 9. Test Varian Joker
    from deck import Deck
    # Mode Joker Asli: tepat 2 Joker fisik
    config_asli = GameConfig(joker_mode="TWO_JOKERS")
    deck_asli = Deck(config_asli)
    jokers_asli = [c for c in deck_asli.cards if c.is_joker]
    assert len(jokers_asli) == 2, f"Mode TWO_JOKERS harus punya tepat 2 Joker, dapat: {len(jokers_asli)}"

    # Mode Joker Gantung: 1 kartu mati pembuka, 3 kartu aktif di dek
    config_gantung = GameConfig(joker_mode="OPEN_CARD_WILD")
    deck_gantung = Deck(config_gantung)
    indicator_card = [c for c in deck_gantung.cards if c.rank == 5 and c.suit == "HATI"][0]
    deck_gantung.cards.remove(indicator_card)  # Kartu pembuka ditarik keluar dari dek (menjadi kartu mati)
    deck_gantung.setup_open_card_wild(indicator_card)
    jokers_gantung = [c for c in deck_gantung.cards if c.is_joker]
    assert len(jokers_gantung) == 3, f"Mode Joker Gantung harus menyisakan tepat 3 kartu Joker aktif di dek, dapat: {len(jokers_gantung)}"

    # 10. Test Joker Tidak Boleh Jadi Pelengkap Serok Kecuali Langsung TUTUP
    # Kasus 10a: Narik kartu pakai Joker tapi belum bisa tutup -> DILARANG!
    pair_with_joker = [Card(9, "KERITING"), joker]
    target_card_8 = Card(8, "KERITING")
    hand_unclosed = pair_with_joker + [Card(2, "SEKOP"), Card(4, "HATI"), Card(7, "TAHU")]
    valid_joker_unclosed, msg_joker = check_discard_pickup_validity(hand_unclosed, target_card_8, pair_with_joker, config)
    assert valid_joker_unclosed == False, "Joker dilarang jadi pelengkap serok jika tidak langsung tutup!"
    assert "Joker dilarang" in msg_joker, f"Pesan error salah: {msg_joker}"

    # Kasus 10b: Narik kartu pakai Joker dan LANGSUNG BISA TUTUP! -> DIIZINKAN!
    # Tangan: (9 Keriting + Joker) + (Tris K) + (As Hati sebagai kartu tutup)
    hand_can_close = pair_with_joker + [k_sekop, k_hati, k_tahu, as_hati]
    valid_joker_closed, msg_joker_ok = check_discard_pickup_validity(hand_can_close, target_card_8, pair_with_joker, config)
    assert valid_joker_closed == True, f"Joker harus diizinkan jadi pelengkap serok jika langsung TUTUP! {msg_joker_ok}"

    # 11. Test Tutup Tangan Murni vs Ada Yang Narik Dari Bawah (Serok Buangan)
    from game import GameEngine
    engine = GameEngine(config, human_name="Kamu")
    engine.start_new_round()

    # Kasus 11a: Tutup Tangan Murni (meja bersih, tidak ada yang narik buangan)
    # Hanya pemenang yang dapat +200, pemain lain 0!
    res_pure = engine.handle_round_end_tutup(
        winner_idx=0,
        closing_card=as_hati,
        melds=[],
        is_kocokan_win=True
    )
    assert res_pure["is_pure_tutup_tangan"] == True, "Harus berstatus is_pure_tutup_tangan True!"
    assert res_pure["round_scores"]["Kamu"] == 200, "Pemenang tutup tangan harus dapat +200!"
    assert res_pure["round_scores"]["Pak RT"] == 0, "Pemain lain harus 0 saat Tutup Tangan Murni!"
    assert res_pure["round_scores"]["Pak RW"] == 0
    assert res_pure["round_scores"]["Pak Sukardi"] == 0

    # Kasus 11b: Ada yang narik dari bawah! (Pak RT memiliki kartu terbuka hasil serok)
    engine_b = GameEngine(config, human_name="Kamu")
    engine_b.start_new_round()
    # Pak RT punya open meld 4 kartu penuh di meja (Q-Q-Q-Q), sehingga tidak bisa disambung lagi
    engine_b.players[1].open_melds = [[Card(12, "SEKOP"), Card(12, "HATI"), Card(12, "KERITING"), Card(12, "TAHU")]]
    # Pak RW pegang Joker mentah dan 3 Sekop di tangan yang tidak bisa disambung ke meja
    engine_b.players[2].hand = [joker, Card(3, "SEKOP")]

    res_with_scoop = engine_b.handle_round_end_tutup(
        winner_idx=0,
        closing_card=as_hati,
        melds=[],
        is_kocokan_win=True
    )
    assert res_with_scoop["is_pure_tutup_tangan"] == False, "Tidak boleh murni tutup tangan jika ada yang narik dari bawah!"
    assert res_with_scoop["round_scores"]["Pak RT"] != 0, "Pak RT harus dihitung skornya berdasarkan kartu terbukanya!"
    # Pak RW kena denda Joker mentah (-250) + (-5) = -255
    assert res_with_scoop["round_scores"]["Pak RW"] <= -250, "Pak RW harus kena denda Joker mentah -250!"

    # 12. PENGUJIAN FITUR SAMBUNG KARTU KE MEJA (LAYOFF / KARTU KUNING BEBAS DENDA)
    # Jika di meja ada Seri 7-8-9 Sekop, dan pemain memegang 6 Sekop + Joker:
    # 6 Sekop dan Joker harus otomatis tersambung ke meja (kuning) dan bebas denda!
    engine_c = GameEngine(config, human_name="Kamu")
    engine_c.start_new_round()
    engine_c.players[1].open_melds = [[Card(7, "SEKOP"), Card(8, "SEKOP"), Card(9, "SEKOP")]]
    engine_c.players[2].hand = [joker, Card(6, "SEKOP"), Card(2, "HATI")] # Joker & 6 Sekop bisa nyambung, 2 Hati mentah

    res_layoff = engine_c.handle_round_end_tutup(
        winner_idx=0,
        closing_card=as_hati,
        melds=[],
        is_kocokan_win=True
    )
    # Pak RW hanya kena denda kartu 2 Hati (-5 pt), Joker dan 6 Sekop berhasil disambung (bebas denda)!
    # 13. PENGUJIAN FLEKSIBILITAS SEROK BUANGAN (Kasus contoh user: tangan 3, 4, 7, 8; buangan ada 6 & 5)
    c3_s = Card(3, "SEKOP")
    c4_s = Card(4, "SEKOP")
    c7_s = Card(7, "SEKOP")
    c8_s = Card(8, "SEKOP")
    c6_s = Card(6, "SEKOP")
    c5_s = Card(5, "SEKOP")
    hand_flex = [c3_s, c4_s, c7_s, c8_s]
    # Kasus A: Pemain memilih hanya 3 & 4 dari tangan, target 5, 6 ikut terserok
    # Hasil: 3-4-5 dibuka di meja, 6 disimpan ke tangan
    val_a, msg_a, meld_a, left_a = check_discard_pickup_validity(
        hand_flex, c5_s, [c3_s, c4_s], config, other_scooped_cards=[c6_s], return_melds=True
    )
    assert val_a == True, f"Kasus A harus sah: {msg_a}"
    assert len(meld_a) == 3 and c6_s not in meld_a, "3-4-5 harus di meja"
    assert left_a == [c6_s], f"Kartu 6 harus disimpan di tangan sebagai leftover, dapat: {left_a}"

    # Kasus B: Pemain memilih semua 3, 4, 7, 8 dari tangan, target 5, 6 ikut terserok
    # Hasil: 3-4-5-6-7-8 semuanya dibuka di meja (0 kartu tersisa di tangan)
    val_b, msg_b, meld_b, left_b = check_discard_pickup_validity(
        hand_flex, c5_s, [c3_s, c4_s, c7_s, c8_s], config, other_scooped_cards=[c6_s], return_melds=True
    )
    assert val_b == True, f"Kasus B harus sah: {msg_b}"
    assert len(meld_b) == 6, "Semua 6 kartu (3-4-5-6-7-8) harus terbuka di meja"
    assert len(left_b) == 0, "Leftover harus kosong karena 6 terserap ke meja"

    # Kasus C: Pemain memilih 7 & 8 dari tangan, target 5, 6 ikut terserok
    # Hasil: 5-6-7-8 dibuka di meja
    val_c, msg_c, meld_c, left_c = check_discard_pickup_validity(
        hand_flex, c5_s, [c7_s, c8_s], config, other_scooped_cards=[c6_s], return_melds=True
    )
    assert val_c == True, f"Kasus C harus sah: {msg_c}"
    assert len(meld_c) == 4, "5-6-7-8 harus terbuka di meja"

    # 14. TEST VALIDASI DEKLARASI CEKIH (TIDAK BOLEH ASAL / MAIN-MAIN BILANG CEKIH)
    from rules import check_is_cekih
    # Kasus 14a: Kartu acak-acakan (sama sekali belum nunggu 1 kartu tutup) -> DITOLAK
    random_hand = [Card(2, "SEKOP"), Card(4, "HATI"), Card(7, "KERITING"), Card(9, "TAHU"), Card(11, "HATI"), Card(13, "SEKOP"), Card(14, "KERITING")]
    is_c1, msg_c1, _ = check_is_cekih(random_hand, config)
    assert is_c1 == False, "Kartu acak tidak boleh dianggap Cekih!"
    assert "BELUM CEKIH" in msg_c1

    # Kasus 14b: Kartu sudah nunggu 1 kartu kunci:
    # Seri 5-6-7 Sekop (3) + Tris K (K Sekop, K Hati, K Tahu) (3) + Kartu Kunci As Hati (1) = 7 kartu!
    # Tangan ini cuma nunggu 1 kartu lagi untuk ditarik & tutup! -> SAH CEKIH!
    cekih_hand = [Card(5, "SEKOP"), Card(6, "SEKOP"), Card(7, "SEKOP"), Card(13, "SEKOP"), Card(13, "HATI"), Card(13, "TAHU"), Card(14, "HATI")]
    is_c2, msg_c2, waiting = check_is_cekih(cekih_hand, config)
    assert is_c2 == True, f"Tangan 7 kartu yang siap nunggu 1 kartu harus sah Cekih: {msg_c2}"
    assert len(waiting) > 0, "Daftar kartu yang ditunggu harus ada"

    print("SEMUA UNIT TEST RULES 100% SUKSES DAN COCOK DENGAN ATURAN POS RONDA!")

if __name__ == "__main__":
    test_all()

