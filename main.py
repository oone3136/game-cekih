"""
Aplikasi Game Terminal: REMI CEKIH POS RONDA
Game kartu otentik 4 pemain dengan bot bapak-bapak pos ronda.
"""

import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from typing import List, Optional
from config import GameConfig, get_default_config, get_casual_config
from card import Card, RANK_NAMES, COLOR_BOLD, COLOR_RESET, COLOR_YELLOW, COLOR_CYAN
from rules import check_tutup, check_discard_pickup_validity, Meld
from game import GameEngine

# Aktifkan dukungan warna ANSI di Windows PowerShell / CMD
os.system("")

def clear_screen():
    print("\n" + "=" * 60 + "\n")

def print_header(text: str):
    print(f"\n{COLOR_CYAN}{COLOR_BOLD}=== {text} ==={COLOR_RESET}")

def print_rules_info(config: GameConfig):
    clear_screen()
    print_header("PANDUAN & ATURAN REMI CEKIH")
    print(f"1. Pemain: 4 orang (Kamu vs Pak RT, Pak RW, Pak Sukardi)")
    print(f"2. Awal: Masing-masing pegang {config.cards_per_player} kartu. 1 kartu dibuka ke buangan.")
    print(f"3. Putaran 1: Wajib ambil kocokan (dilarang ambil buangan).")
    print(f"4. Mode Joker: {config.joker_mode}")
    print(f"   * OPEN_CARD_WILD: Nilai kartu bukaan pertama menentukan 3 joker liar.")
    print(f"5. Tris (Set): {'Semua angka boleh' if config.allow_pip_tris else 'HANYA RAJA (J, Q, K, A) yang boleh Tris'}")
    print(f"6. Ambil Buangan (Serok):")
    print(f"   * Maksimal jangkauan: {config.max_discard_depth} kartu terakhir (lebih dari itu hangus).")
    print(f"   * Wajib buka 2 kartu pasangan sah dari tangan.")
    print(f"   * Mode Sambung: {'Boleh Sisip (2&4 ambil 3)' if config.allow_gap_pickup else 'Wajib Sambung Ujung (2&3 ambil 4)'}")
    print(f"   * Semua kartu di atas kartu target ikut terserok ke tangan!")
    print(f"7. Poin & Denda:")
    print(f"   * Tutup Kocokan (Narik Sendiri): +{config.kocokan_win_bonus} poin (lainnya 0).")
    print(f"   * Tutup Cekih: Anak +{config.close_points['ANAK']}, Raja +{config.close_points['RAJA']}, As +{config.close_points['AS']}.")
    print(f"   * Denda yang di-Cekih: Minus sebesar nilai kartu tutupan pemenang!")
    print(f"   * Denda Kartu Mentah: Anak -5, Raja -10, As -15, JOKER -250.")
    print(f"   * Kocokan Habis: Cuci Tangan (semua 0).")
    print("=" * 60)
    input("\nTekan Enter untuk kembali ke menu...")

def configure_rules_menu(config: GameConfig):
    while True:
        clear_screen()
        print_header("PENGATURAN ATURAN PERMAINAN (RULE ENGINE)")
        print(f"1. Mode Joker       : [{config.joker_mode}] (OPEN_CARD_WILD / TWO_JOKERS / NONE)")
        print(f"2. Boleh Tris Anak  : [{'YA' if config.allow_pip_tris else 'TIDAK (Hanya Raja J,Q,K,A)'}]")
        print(f"3. Ambil Buangan    : [{'BOLEH SISIP/JEPIT' if config.allow_gap_pickup else 'WAJIB SAMBUNG UJUNG'}]")
        print(f"4. Batas Serok      : [{config.max_discard_depth} kartu terakhir]")
        print(f"5. Target Skor Game : [{config.target_score} poin]")
        print(f"6. Kembalikan ke Standar Pos Ronda Asli")
        print(f"0. Selesai & Kembali ke Menu Utama")
        print("-" * 60)

        choice = input("Pilih nomor yang ingin diubah (0-6): ").strip()
        if choice == "1":
            opts = ["OPEN_CARD_WILD", "TWO_JOKERS", "NONE"]
            curr_idx = opts.index(config.joker_mode)
            config.joker_mode = opts[(curr_idx + 1) % len(opts)]
        elif choice == "2":
            config.allow_pip_tris = not config.allow_pip_tris
        elif choice == "3":
            config.allow_gap_pickup = not config.allow_gap_pickup
        elif choice == "4":
            val = input("Masukkan batas kedalaman serok buangan (misal 5 atau 7): ").strip()
            if val.isdigit() and int(val) > 0:
                config.max_discard_depth = int(val)
        elif choice == "5":
            val = input("Masukkan target skor akhir game (misal 500 atau 1000): ").strip()
            if val.isdigit() and int(val) > 0:
                config.target_score = int(val)
        elif choice == "6":
            default = get_default_config()
            config.joker_mode = default.joker_mode
            config.allow_pip_tris = default.allow_pip_tris
            config.allow_gap_pickup = default.allow_gap_pickup
            config.max_discard_depth = default.max_discard_depth
            print("Aturan dikembalikan ke Preset Otentik Pos Ronda!")
            time.sleep(1)
        elif choice == "0":
            break

def display_game_status(game: GameEngine):
    print("\n" + "=" * 65)
    print(f"🃏 REMI CEKIH POS RONDA | PUTARAN KE-{game.round_number} | Sisa Kocokan: {game.deck.remaining} kartu")
    if game.deck.wild_rank is not None:
        rank_str = RANK_NAMES.get(game.deck.wild_rank, str(game.deck.wild_rank))
        print(f"★ JOKER LIAR RONDE INI: Angka [{rank_str}] (Semua kartu angka {rank_str} adalah Joker!)")

    # Papan Skor Sementara
    score_line = " | ".join(f"{p.name}: {p.score} pt" for p in game.players)
    print(f"📊 SKOR: {score_line}")
    print("-" * 65)

    # Tumpukan Buangan
    print("🗑️  KARTU BUANGAN (Dibeber memanjang, #1 paling baru):")
    if not game.discard_pile:
        print("   (Belum ada kartu buangan)")
    else:
        dis_str_list = []
        for idx, entry in enumerate(game.discard_pile):
            num = idx + 1
            who = game.players[entry.discarded_by].name if entry.discarded_by is not None else "Meja"
            if idx < game.config.max_discard_depth:
                dis_str_list.append(f"{num}:{entry.card.display()} ({who})")
            else:
                dis_str_list.append(f"[Hangus {num}:{entry.card}]")
        # Cetak per baris rapi
        print("   " + "  ".join(dis_str_list[:game.config.max_discard_depth]))
        if len(dis_str_list) > game.config.max_discard_depth:
            print("   " + "  ".join(dis_str_list[game.config.max_discard_depth:]))

    print("-" * 65)

def human_turn(game: GameEngine) -> Optional[dict]:
    human = game.players[0]
    display_game_status(game)

    print(f"\n👉 GILIRAN ANDA ({human.name}):")
    print(f"Kartu di Tangan ({len(human.hand)} kartu):")
    print("   " + human.display_hand(show_indices=True))

    drawn_card: Optional[Card] = None
    is_kocokan = True
    discarder_idx = None

    # STEP 1: PILIH DRAW (KOCOKAN vs SEROK BUANGAN)
    if game.round_number == 1 and game.config.first_round_deck_only:
        print(f"\nℹ️  Putaran pertama: Wajib menarik dari kocokan tertutup.")
        input("Tekan Enter untuk tarik kartu dari kocokan...")
        drawn_card = game.draw_from_deck(human)
        print(f"Anda menarik kartu: {drawn_card.display()}")
    else:
        while True:
            print("\nPilih Aksi Ambil Kartu:")
            print("[1] Tarik 1 kartu dari Kocokan Tertutup")
            print("[2] Serok Kartu dari Buangan Meja")
            choice = input("Pilihan Anda (1/2): ").strip()

            if choice == "1":
                drawn_card = game.draw_from_deck(human)
                print(f"Anda menarik kartu: {drawn_card.display()}")
                is_kocokan = True
                break
            elif choice == "2":
                if not game.discard_pile:
                    print("Tumpukan buangan masih kosong!")
                    continue
                max_depth = min(len(game.discard_pile), game.config.max_discard_depth)
                depth_in = input(f"Pilih nomor kartu buangan yang mau diserok (1 s/d {max_depth}, 0 untuk batal): ").strip()
                if not depth_in.isdigit() or int(depth_in) < 1 or int(depth_in) > max_depth:
                    if depth_in == "0":
                        continue
                    print("Nomor urutan tidak valid!")
                    continue

                target_idx = int(depth_in) - 1
                target_card = game.discard_pile[target_idx].card
                target_discarder = game.discard_pile[target_idx].discarded_by

                print(f"Kartu target: {target_card.display()}")
                print("Keluarkan 2 nomor kartu dari tangan Anda untuk membuktikan kombinasi:")
                print("   " + human.display_hand(show_indices=True))
                pair_in = input("Masukkan 2 nomor kartu dipisah spasi (misal: '1 2' atau 0 untuk batal): ").strip()
                if pair_in == "0":
                    continue
                parts = pair_in.split()
                if len(parts) != 2 or not all(p.isdigit() for p in parts):
                    print("Input harus 2 angka dipisah spasi!")
                    continue

                idx1, idx2 = int(parts[0]) - 1, int(parts[1]) - 1
                if idx1 == idx2 or idx1 < 0 or idx1 >= len(human.hand) or idx2 < 0 or idx2 >= len(human.hand):
                    print("Nomor kartu di tangan tidak valid!")
                    continue

                pair_cards = [human.hand[idx1], human.hand[idx2]]
                success, msg, scooped = game.scoop_from_discard(0, target_idx, pair_cards)
                if not success:
                    print(f"❌ Gagal serok: {msg}")
                    continue
                else:
                    print(f"✅ {msg}")
                    print(f"Kartu yang ikut terangkat: {' '.join(c.display() for c in scooped)}")
                    is_kocokan = False
                    discarder_idx = target_discarder
                    break
            else:
                print("Pilihan tidak valid!")

    # STEP 2: CEK KONDISI TUTUP (CEKIH / TUTUP KOCOKAN)
    tutup_opts = check_tutup(human.hand, game.config)
    if tutup_opts:
        print(f"\n{COLOR_YELLOW}{COLOR_BOLD}🎉🎉 KARTU ANDA BISA TUTUP / CEKIH! 🎉🎉{COLOR_RESET}")
        print("Opsi Tutupan yang tersedia:")
        for idx_opt, (close_card, melds) in enumerate(tutup_opts):
            print(f"  [{idx_opt+1}] Tutup dengan kartu kunci {close_card.display()} (Tipe: {close_card.card_type})")
            print(f"      Rangkaian: {melds}")

        while True:
            action = input("\nApakah ingin [T] Tutup Sekarang atau [G] Cekih Gantung (Lanjut Main)? (T/G): ").strip().upper()
            if action == "T":
                chosen_opt_idx = 0
                if len(tutup_opts) > 1:
                    opt_in = input(f"Pilih opsi nomor tutupan (1-{len(tutup_opts)}): ").strip()
                    if opt_in.isdigit() and 1 <= int(opt_in) <= len(tutup_opts):
                        chosen_opt_idx = int(opt_in) - 1
                close_card, melds = tutup_opts[chosen_opt_idx]
                # Buang kartu penutup
                human.remove_card(close_card)
                # Proses kemenangan
                return game.handle_round_end_tutup(
                    winner_idx=0,
                    closing_card=close_card,
                    melds=melds,
                    is_kocokan_win=is_kocokan,
                    discarder_idx=discarder_idx
                )
            elif action == "G":
                print("🎲 Anda memilih CEKIH GANTUNG! Permainan dilanjutkan...")
                break
            else:
                print("Ketik 'T' untuk Tutup atau 'G' untuk Gantung!")

    # STEP 3: PILIH KARTU BUANGAN
    print(f"\nKartu di Tangan Anda Sekarang ({len(human.hand)} kartu):")
    print("   " + human.display_hand(show_indices=True))
    while True:
        card_in = input(f"Pilih nomor kartu yang ingin dibuang (1 s/d {len(human.hand)}): ").strip()
        if card_in.isdigit() and 1 <= int(card_in) <= len(human.hand):
            chosen_card = human.hand[int(card_in) - 1]
            if chosen_card.is_joker:
                confirm = input("⚠️ Yakin mau buang JOKER? Denda joker mentah sangat besar! (y/n): ").strip().lower()
                if confirm != "y":
                    continue
            game.execute_discard(0, chosen_card)
            print(f"Anda membuang kartu: {chosen_card.display()}")
            break
        print("Nomor kartu tidak valid!")

    return None

def bot_turn(game: GameEngine, bot_idx: int) -> Optional[dict]:
    bot: BotPlayer = game.players[bot_idx]  # type: ignore
    print(f"\n🤖 Giliran {bot.name}...")
    time.sleep(0.8)

    discard_cards = game.get_discard_cards()
    action, depth, pair = bot.decide_draw(
        discard_cards,
        is_first_round=(game.round_number == 1 and game.config.first_round_deck_only),
        config=game.config
    )

    is_kocokan = True
    discarder_idx = None

    if action == "DISCARD" and depth is not None and pair is not None:
        target_entry = game.discard_pile[depth]
        discarder_idx = target_entry.discarded_by
        success, msg, scooped = game.scoop_from_discard(bot_idx, depth, pair)
        if success:
            pair_str = " ".join(c.display() for c in pair)
            print(f"⚡ {bot.name} MENYEROK {len(scooped)} kartu buangan!")
            print(f"   Menunjukkan pasangan: {pair_str} untuk kartu {target_entry.card.display()}")
            is_kocokan = False
        else:
            drawn = game.draw_from_deck(bot)
            print(f"{bot.name} menarik 1 kartu dari kocokan tertutup.")
    else:
        drawn = game.draw_from_deck(bot)
        print(f"{bot.name} menarik 1 kartu dari kocokan tertutup.")

    # Cek Tutup Bot
    tutup_opts = check_tutup(bot.hand, game.config)
    if tutup_opts:
        should_tutup, close_card, melds = bot.decide_tutup_or_gantung(tutup_opts, game.deck.remaining)
        if should_tutup:
            bot.remove_card(close_card)
            print(f"\n{COLOR_YELLOW}{COLOR_BOLD}🏆 {bot.name} BERTERIAK TUTUP! 🏆{COLOR_RESET}")
            return game.handle_round_end_tutup(
                winner_idx=bot_idx,
                closing_card=close_card,
                melds=melds,
                is_kocokan_win=is_kocokan,
                discarder_idx=discarder_idx
            )
        else:
            print(f"👀 {bot.name} memilih CEKIH GANTUNG (Lanjut main)!")

    # Buang kartu
    card_to_discard = bot.decide_discard(game.config)
    game.execute_discard(bot_idx, card_to_discard)
    print(f"{bot.name} membuang kartu: {card_to_discard.display()}")
    time.sleep(0.5)

    return None

def play_one_round(game: GameEngine, round_number: int = 1):
    if round_number > 1:
        highest_player = max(game.players, key=lambda p: p.score)
        starter_idx = game.players.index(highest_player)
        print(f"\n📢 Ronde {round_number} dimulai! {highest_player.name} memiliki nilai skor tertinggi ({highest_player.score} pt) dan berhak mulai pertama!")
        game.start_new_round(starting_player_idx=starter_idx)
    else:
        game.start_new_round(starting_player_idx=0)

    round_over = False
    result = None

    while not round_over:
        # Cek apakah kocokan habis
        if game.deck.is_empty():
            result = game.handle_round_end_draw()
            break

        # Giliran pemain
        current_idx = game.current_player_idx
        if current_idx == 0:
            result = human_turn(game)
        else:
            result = bot_turn(game, current_idx)

        if result is not None:
            round_over = True
            break

        # Maju ke pemain berikutnya
        game.current_player_idx = (game.current_player_idx + 1) % 4
        if game.current_player_idx == 0:
            game.round_number += 1

    # Tampilkan Hasil Ronde
    clear_screen()
    print_header("HASIL RONDE INI")
    for line in result["details"]:
        print(line)

    print("\n" + "=" * 45)
    print("📊 KLASEMEN TOTAL SKOR SAAT INI:")
    for p in sorted(game.players, key=lambda x: x.score, reverse=True):
        print(f"  • {p.name:<15}: {p.score:>5} poin")
    print("=" * 45)
    input("\nTekan Enter untuk lanjut...")

def main():
    config = get_default_config()

    while True:
        clear_screen()
        print(f"{COLOR_YELLOW}{COLOR_BOLD}")
        print(r"""
  ____  _____ __  __ ___    ____ _____ _  _____ _   _ 
 |  _ \| ____|  \/  |_ _|  / ___| ____| |/ /_ _| | | |
 | |_) |  _| | |\/| || |  | |   |  _| | ' / | || |_| |
 |  _ <| |___| |  | || |  | |___| |___| . \ | ||  _  |
 |_| \_\_____|_|  |_|___|  \____|_____|_|\_\___|_| |_|
        --- EDISI POS RONDA (4 PEMAIN) ---
        """)
        print(f"{COLOR_RESET}")
        print("1. Mulai Permainan Baru")
        print("2. Atur Variasi Aturan (Rule Engine)")
        print("3. Lihat Panduan & Skor")
        print("4. Keluar")
        print("-" * 55)

        choice = input("Pilih menu (1-4): ").strip()
        if choice == "1":
            name = input("Masukkan nama Anda (kosongkan untuk 'Kamu'): ").strip()
            if not name:
                name = "Kamu"
            game = GameEngine(config, human_name=name)

            # Loop ronde pertandingan sampai target skor tercapai
            current_round_num = 1
            while True:
                play_one_round(game, round_number=current_round_num)
                current_round_num += 1
                # Cek apakah ada yang tembus target skor
                leaders = [p for p in game.players if p.score >= config.target_score]
                if leaders:
                    winner = max(game.players, key=lambda p: p.score)
                    print(f"\n🎉 SELAMAT! {winner.name} MEMENANGKAN PERTANDINGAN DENGAN {winner.score} POIN! 🎉")
                    input("Tekan Enter untuk kembali ke menu utama...")
                    break

                lagi = input("\nLanjut ke ronde berikutnya? (y/n): ").strip().lower()
                if lagi != "y":
                    break
        elif choice == "2":
            configure_rules_menu(config)
        elif choice == "3":
            print_rules_info(config)
        elif choice == "4":
            print("\nTerima kasih sudah nongkrong di pos ronda! Sampai jumpa!\n")
            sys.exit(0)

if __name__ == "__main__":
    main()
