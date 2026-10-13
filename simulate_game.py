"""
Skrip simulasi otomatis: Menjalankan permainan dengan 4 bot
untuk memverifikasi semua alur dan kalkulasi skor berjalan mulus tanpa error.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import get_default_config
from game import GameEngine
from bot import BotPlayer

def run_simulation(rounds=3):
    config = get_default_config()
    game = GameEngine(config, human_name="Sim-Player")
    # Ganti human player dengan Bot agar bisa jalan otomatis
    game.players[0] = BotPlayer(name="Pak Lurah", personality="imbang")

    print(f"=== MEMULAI SIMULASI {rounds} RONDE REMI CEKIH ===")
    for r in range(1, rounds + 1):
        print(f"\n--- SIMULASI RONDE {r} ---")
        game.start_new_round()
        round_over = False
        result = None

        turn_limit = 100
        turns = 0
        while not round_over and turns < turn_limit:
            turns += 1
            if game.deck.is_empty():
                result = game.handle_round_end_draw()
                round_over = True
                break

            current_idx = game.current_player_idx
            bot = game.players[current_idx]
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
                success, msg, scooped = game.scoop_from_discard(current_idx, depth, pair)
                if success:
                    is_kocokan = False
                else:
                    game.draw_from_deck(bot)
            else:
                game.draw_from_deck(bot)

            from rules import check_tutup
            tutup_opts = check_tutup(bot.hand, game.config)
            if tutup_opts:
                should_tutup, close_card, melds = bot.decide_tutup_or_gantung(tutup_opts, game.deck.remaining)
                if should_tutup:
                    bot.remove_card(close_card)
                    result = game.handle_round_end_tutup(
                        winner_idx=current_idx,
                        closing_card=close_card,
                        melds=melds,
                        is_kocokan_win=is_kocokan,
                        discarder_idx=discarder_idx
                    )
                    round_over = True
                    break

            card_to_discard = bot.decide_discard(game.config)
            game.execute_discard(current_idx, card_to_discard)

            game.current_player_idx = (game.current_player_idx + 1) % 4
            if game.current_player_idx == 0:
                game.round_number += 1

        print("Hasil:")
        for line in result["details"]:
            print("  ", line)

    print("\n=== HASIL AKHIR SIMULASI ===")
    for p in sorted(game.players, key=lambda x: x.score, reverse=True):
        print(f"  {p.name:<15}: {p.score} poin")
    print("\nSIMULASI SELESAI DENGAN SUKSES!")

if __name__ == "__main__":
    run_simulation(3)
