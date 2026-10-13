"""
Server Web API dan Static Server untuk Remi Cekih Edisi Pos Ronda.
Dibuat menggunakan modul bawaan Python (zero external dependencies).
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Pastikan path Python mencakup direktori game
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from datetime import datetime
from config import get_default_config, GameConfig
from card import Card, RANK_NAMES, SUIT_SYMBOLS
from rules import (
    check_discard_pickup_validity, check_tutup, check_is_cekih,
    calculate_meld_points, calculate_deadwood_penalty,
    get_closing_card_value, get_deadwood_breakdown,
    find_optimal_layoffs, find_all_layoff_options,
    validate_layoff_selection, Meld
)
from game import GameEngine
from bot import BotPlayer

# Konfigurasi Skin dengan Koin Emas Pos Ronda (Bukan Rupiah Langsung)
SKIN_CATALOG = {
    "tables": [
        {
            "id": "pos_ronda_wood",
            "name": "Pos Ronda Kayu & Beludru",
            "desc": "Meja kayu jati ronda dengan karpet beludru hijau hangat.",
            "price": "Gratis (Default)",
            "price_coins": 0,
            "preview_color": "#1e4620"
        },
        {
            "id": "casino_royal_gold",
            "name": "Kasino Royal Gold",
            "desc": "Karpet merah maroon mewah dengan lis ukiran emas 24 karat.",
            "price": "150 Koin Emas",
            "price_coins": 150,
            "preview_color": "#5a111b"
        },
        {
            "id": "cyber_neon_night",
            "name": "Cyber Ronda Neon",
            "desc": "Meja futuristik dark-mode dengan lampu neon cyan & magenta.",
            "price": "250 Koin Emas",
            "price_coins": 250,
            "preview_color": "#0d1b2a"
        }
    ],
    "card_backs": [
        {
            "id": "batik_ronda",
            "name": "Batik Pos Ronda",
            "desc": "Motif batik tradisional biru tua khas Nusantara.",
            "price": "Gratis (Default)",
            "price_coins": 0,
            "preview_pattern": "batik"
        },
        {
            "id": "gold_dragon",
            "name": "Golden Dragon VIP",
            "desc": "Ukiran naga emas berkilau dengan latar hitam elegan.",
            "price": "100 Koin Emas",
            "price_coins": 100,
            "preview_pattern": "gold"
        },
        {
            "id": "nusantara_red",
            "name": "Nusantara Merah Bara",
            "desc": "Ornamen wayang merah menyala dengan bingkai perak.",
            "price": "120 Koin Emas",
            "price_coins": 120,
            "preview_pattern": "red"
        }
    ],
    "victory_fx": [
        {
            "id": "petasan_ronda",
            "name": "Petasan Pos Ronda",
            "desc": "Ledakan confetti warna-warni meriah dengan tulisan Cekih!",
            "price": "Gratis (Default)",
            "price_coins": 0,
            "preview_icon": "🎆"
        },
        {
            "id": "gold_rain",
            "name": "Hujan Koin Emas",
            "desc": "Ratusan koin emas berhamburan dari atas layar.",
            "price": "180 Koin Emas",
            "price_coins": 180,
            "preview_icon": "💰"
        },
        {
            "id": "lightning_strike",
            "name": "Petir Halilintar",
            "desc": "Kilatan petir menyambar kartu tutup dengan getaran meja.",
            "price": "200 Koin Emas",
            "price_coins": 200,
            "preview_icon": "⚡"
        }
    ],
    "taunt_fx": [
        {
            "id": "batu_ronda",
            "name": "Lempar Batu Kali",
            "desc": "Lemparan batu pos ronda melayang 'BONK' bikin kaget lawan!",
            "price": "Gratis (Default)",
            "price_coins": 0,
            "preview_icon": "🪨"
        },
        {
            "id": "siram_air",
            "name": "Siram Air Segelas",
            "desc": "Guyuran air 'SPLASH' basah kuyup langsung bikin melek!",
            "price": "50 Koin Emas",
            "price_coins": 50,
            "preview_icon": "💧"
        },
        {
            "id": "sandal_jepit",
            "name": "Lempar Sandal Jepit",
            "desc": "Sandal jepit melayang 'PLAK' mendarat pas di kepala musuh!",
            "price": "50 Koin Emas",
            "price_coins": 50,
            "preview_icon": "🩴"
        }
    ]
}

ACTIVE_SKINS = {
    "table": "pos_ronda_wood",
    "card_back": "batik_ronda",
    "victory_fx": "petasan_ronda",
    "taunt_fx": "batu_ronda"
}

# Katalog Lemparan Interaktif & Emot Meja (Higgs Domino Style)
INTERACTIVE_ITEMS = [
    {
        "id": "sandal_jepit",
        "name": "Lempar Sandal Jepit",
        "icon": "🩴",
        "cost": 0,
        "desc": "Sandal swallow melayang 'PLAK!' pas di jidat lawan!",
        "sound": "smack",
        "type": "FREE"
    },
    {
        "id": "tos_gelas",
        "name": "Tos Dua Gelas",
        "icon": "🍻",
        "cost": 0,
        "desc": "Tos dua gelas kopi/teh pos ronda 'KLING!' santai bareng kawan!",
        "sound": "clink",
        "type": "FREE"
    },
    {
        "id": "batu_ronda",
        "name": "Lempar Batu Kali",
        "icon": "🪨",
        "cost": 0,
        "desc": "Batu kali pos ronda melayang 'BONK!' bikin kaget lawan!",
        "sound": "rock",
        "type": "FREE"
    },
    {
        "id": "siram_air",
        "name": "Siram Air Segelas",
        "icon": "💧",
        "cost": 0,
        "desc": "Guyuran air segelas 'SPLASH!' langsung bikin melek!",
        "sound": "water",
        "type": "FREE"
    },
    {
        "id": "batu_bata",
        "name": "Lempar Batu Bata",
        "icon": "🧱",
        "cost": 5,
        "desc": "Lempar batu bata merah 'KRAK!' bikin lawan pusing tujuh keliling!",
        "sound": "rock",
        "type": "PREMIUM"
    },
    {
        "id": "emot_cium",
        "name": "Emot Cium / Kiss",
        "icon": "💋",
        "cost": 5,
        "desc": "Kirim ciuman cinta 'MUACH!' bikin lawan salting & gemetar!",
        "sound": "kiss",
        "type": "PREMIUM"
    },
    {
        "id": "tomat_busuk",
        "name": "Lempar Tomat Busuk",
        "icon": "🍅",
        "cost": 3,
        "desc": "Tomat busuk 'BECEK!' lengket di muka lawan!",
        "sound": "water",
        "type": "PREMIUM"
    },
    {
        "id": "bunga_mawar",
        "name": "Bunga Mawar Cantik",
        "icon": "🌹",
        "cost": 3,
        "desc": "Setangkai mawar 'SWEET!' rayuan maut pos ronda!",
        "sound": "kiss",
        "type": "PREMIUM"
    },
    {
        "id": "bom_granat",
        "name": "Lempar Granat / Bom",
        "icon": "💣",
        "cost": 10,
        "desc": "Ledakan granat 'BOOM!' bikin satu pos ronda kocar-kacir!",
        "sound": "explosion",
        "type": "PREMIUM"
    }
]

# Paket Simulasi Top-Up Koin Emas (Bebas Izin OJK & Tanpa Transaksi Uang Riil)
TOPUP_PACKAGES = [
    {
        "id": "pack_warung",
        "name": "Paket Warung Kopi",
        "coins": 100,
        "bonus": 20,
        "price_label": "Gratis (Simulasi Demo)",
        "badge": "Hemat",
        "icon": "☕"
    },
    {
        "id": "pack_ronda",
        "name": "Paket Pos Ronda",
        "coins": 300,
        "bonus": 80,
        "price_label": "Gratis (Simulasi Demo)",
        "badge": "Terlaris 🔥",
        "icon": "🏮"
    },
    {
        "id": "pack_sultan",
        "name": "Paket Sultan RW",
        "coins": 1000,
        "bonus": 300,
        "price_label": "Gratis (Simulasi Demo)",
        "badge": "Sultan VIP 👑",
        "icon": "💎"
    }
]

PROFILE_FILE = os.path.join(CURRENT_DIR, "user_profile.json")

def load_user_profile():
    today_str = datetime.now().strftime("%Y-%m-%d")
    default_profile = {
        "coins": 100,
        "last_login_date": today_str,
        "daily_login_claimed_date": None,
        "unlocked_skins": ["pos_ronda_wood", "batik_ronda", "petasan_ronda", "batu_ronda", "sandal_jepit", "tos_gelas", "siram_air"],
        "quests": {
            "win_round": {"id": "win_round", "title": "Juara Ronda", "desc": "Menangkan 1 ronde pertandingan", "progress": 0, "target": 1, "reward": 20, "claimed": False},
            "scoop_discard": {"id": "scoop_discard", "title": "Tukang Serok", "desc": "Serok kartu buangan di meja", "progress": 0, "target": 2, "reward": 15, "claimed": False},
            "send_emotes": {"id": "send_emotes", "title": "Usil di Meja", "desc": "Kirim lemparan/emot ke pemain lain", "progress": 0, "target": 3, "reward": 10, "claimed": False},
            "play_rounds": {"id": "play_rounds", "title": "Nongkrong Santai", "desc": "Mainkan ronde pertandingan", "progress": 0, "target": 3, "reward": 15, "claimed": False}
        }
    }
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_profile.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return default_profile

def save_user_profile(profile):
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
    except Exception:
        pass

USER_PROFILE = load_user_profile()

def get_bot_interactive_dialog(bot_name: str, item_id: str) -> str:
    import random
    dialogs = {
        "sandal_jepit": {
            "Pak RT": ["Astaga sendal swallow melayang ke Pak RT! Siapa nih yang iseng?!", "Sendal jepit siapa ini copot talinya?!"],
            "Pak RW": ["Heh sopan dikit! Masa kepala RW lu lempar sendal jepit!", "Aduh sendal swallow bekas ronda!"],
            "Pak Sukardi": ["PLAK! Kampret bener, sendal bolong lu lempar ke jidat gua!", "Awas lu ya, gua bales pake bakiak nanti!"]
        },
        "tos_gelas": {
            "Pak RT": ["Tos dulu lur! Sruput kopi item biar ronda makin anget!", "Mantap, toss! Kopi torabika pos ronda nomor satu!"],
            "Pak RW": ["Kling! Kopi pos ronda emang paling nikmat se-kecamatan!", "Tos dulu bos! Tetep awas jangan sampai kecolongan!"],
            "Pak Sukardi": ["Mantap bos, tos dua gelas! Tapi tetep jangan cekihin gua ya!", "Srupuuut... kopi anget bikin mata melek!"]
        },
        "batu_bata": {
            "Pak RT": ["Waduh gila lu lempar bata ke Pak RT! Rusak wibawa ketua RT nih!", "KRAK! Bata merah siapa nih, benjol kepala saya!"],
            "Pak RW": ["Aduh ampun! Lempar batu bata merah, mau bangun pos ronda lu?!", "Benjol nih kepala tua Pak RW!"],
            "Pak Sukardi": ["Aduuuh! Beneran lempar bata merah! Ganas amat lu main remi!", "Sakit bego! Lu kira gua maling ronda?!"]
        },
        "emot_cium": {
            "Pak RT": ["Aduh si bos bikin salting! Jangan genit di depan Pak RW dong!", "Muach! Hahaha astaga ada-ada aja kelakuan warga!"],
            "Pak RW": ["Hahaha mata Pak RW langsung melek! Jangan genit lu anak muda!", "Waduh kena ciuman, berasa muda lagi jaman pacaran!"],
            "Pak Sukardi": ["Ihhh najis lu cium-cium! Gua normal bro, jangan deket-deket!", "Salting gua anjir, geli banget!"]
        },
        "bom_granat": {
            "Pak RT": ["BOOM! Petasan jumbo meledak! Bubar bubar, pos ronda mau rubuh!", "Allahu akbar kaget saya! Suaranya kenceng bener!"],
            "Pak RW": ["Jantung kakek-kakek mau copot denger bom meledak!", "Gempa lokal di meja pos ronda! Asapnya tebel banget!"],
            "Pak Sukardi": ["MAMPUSS! Suara petasan bikin gua latah! Copot copot copot!", "KABURRR! Meja remi bergetar kayak kena petir!"]
        },
        "siram_air": {
            "Pak RT": ["Byur! Basah kuyup sarung Pak RT!", "Dingin lur! Segelas air kopi tumpah semua!"],
            "Pak RW": ["Langsung seger mata tua ini kena cipratan air!", "Basah kuyup baju dinas RW saya!"],
            "Pak Sukardi": ["Sialan basah kuyup! Padahal rokok gua baru aja nyala!", "Dingin kampret, langsung menggigil gua!"]
        },
        "batu_ronda": {
            "Pak RT": ["Bonk! Kena peci Pak RT!", "Batu kali pos ronda melayang!"],
            "Pak RW": ["Aduh batu pos ronda kena jidat Pak RW!", "Jangan lempar-lempar batu atuh!"],
            "Pak Sukardi": ["Bonk! Dengkul gua kena batu kali!", "Aduh sakit! Kurang ajar bener!"]
        },
        "tomat_busuk": {
            "Pak RT": ["Becek muka Pak RT kena tomat busuk!", "Waduh noda tomat susah dicuci nih!"],
            "Pak RW": ["Bau tomat busuk gini, besok kerja bakti!", "Splat! Pas banget kena kacamata Pak RW!"],
            "Pak Sukardi": ["Tomat becek nempel di jidat gua!", "Asem banget bau tomatnya!"]
        },
        "bunga_mawar": {
            "Pak RT": ["Terima kasih bunganya lur, nanti saya kasih ke Bu RT!", "Wah bunga mawar merah harum bener!"],
            "Pak RW": ["Inget jaman pacaran di gardu ronda dulu!", "Mawar pos ronda, romantis juga lu!"],
            "Pak Sukardi": ["Mau nembak gua lu? Ogah ah!", "Mawar cantik tapi tetep jangan cekihin gua ya!"]
        }
    }
    bot_options = dialogs.get(item_id, {}).get(bot_name, ["Aduh kena lempar!", "Santai atuh bos!"])
    return random.choice(bot_options)

# State Global Game Engine
CONFIG = get_default_config()
GAME = GameEngine(CONFIG, human_name="Kamu")
GAME.start_new_round()

# State Giliran Pemain Manusia
TURN_STATE = {
    "step": "DRAW",              # 'DRAW', 'CHOICE_TUTUP', 'DISCARD', 'ROUND_OVER'
    "drawn_card": None,
    "is_kocokan": True,
    "discarder_idx": None,
    "last_message": "Permainan dimulai! Silakan tarik kartu dari kocokan atau serok kartu buangan.",
    "round_result": None,
    "tutup_options": []
}

def serialize_card(card: Card, index: int = -1):
    if card is None:
        return None
    rank_str = RANK_NAMES.get(card.rank, str(card.rank))
    suit_sym = SUIT_SYMBOLS.get(card.suit, "★" if card.is_joker else "?")
    return {
        "index": index,
        "rank": card.rank,
        "suit": card.suit,
        "is_joker": card.is_joker,
        "rank_name": rank_str,
        "suit_symbol": suit_sym,
        "card_type": card.card_type,
        "display": card.display(use_color=False)
    }

def get_game_state_payload():
    human = GAME.players[0]
    
    # Serialisasi Kartu Buangan
    discard_list = []
    for depth, entry in enumerate(GAME.discard_pile):
        card_data = serialize_card(entry.card)
        card_data["depth"] = depth
        is_dead = getattr(entry, "is_dead", False)
        card_data["is_dead"] = is_dead
        card_data["is_valid_depth"] = (depth < GAME.config.max_discard_depth) and (not is_dead)
        if is_dead:
            discarder_name = "Kartu Mati (Gantung)"
        elif entry.discarded_by is not None:
            discarder_name = GAME.players[entry.discarded_by].name
        else:
            discarder_name = "Bukaan Meja"
        card_data["discarded_by_name"] = discarder_name
        card_data["discarded_by_idx"] = entry.discarded_by
        discard_list.append(card_data)

    # Serialisasi Tangan Manusia
    human_conn = getattr(human, "layoff_indices", []) if TURN_STATE["step"] == "ROUND_OVER" else []
    hand_list = []
    for idx, c in enumerate(human.hand):
        c_dict = serialize_card(c, idx)
        c_dict["is_connected"] = (idx in human_conn)
        hand_list.append(c_dict)

    # Serialisasi 4 Pemain
    players_data = []
    for idx, p in enumerate(GAME.players):
        open_melds_data = []
        for m in p.open_melds:
            open_melds_data.append([serialize_card(c) for c in m])

        open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in p.open_melds], GAME.config)

        is_winner = False
        if TURN_STATE["step"] == "ROUND_OVER" and TURN_STATE.get("round_result"):
            is_winner = (TURN_STATE["round_result"].get("winner") == p.name)

        p_dict = {
            "index": idx,
            "name": p.name,
            "score": p.score,
            "open_meld_points": open_pts,
            "card_count": len(p.hand),
            "open_melds": open_melds_data,
            "is_human": p.is_human,
            "is_current": (idx == GAME.current_player_idx and TURN_STATE["step"] != "ROUND_OVER"),
            "is_winner": is_winner
        }
        if TURN_STATE["step"] == "ROUND_OVER":
            p_conn = getattr(p, "layoff_indices", [])
            rev_cards = []
            for c_idx, c in enumerate(p.hand):
                c_data = serialize_card(c, c_idx)
                c_data["is_connected"] = True if is_winner else (c_idx in p_conn)
                rev_cards.append(c_data)
            p_dict["revealed_hand"] = rev_cards
        players_data.append(p_dict)

    # Cek Opsi Tutup jika belum dibuat
    tutup_payload = []
    if TURN_STATE["tutup_options"]:
        for opt_idx, (close_c, melds) in enumerate(TURN_STATE["tutup_options"]):
            tutup_payload.append({
                "option_index": opt_idx,
                "closing_card": serialize_card(close_c),
                "close_value": get_closing_card_value(close_c, GAME.config),
                "melds_summary": [str(m) for m in melds]
            })

    human_open_melds = [[serialize_card(c) for c in m] for m in human.open_melds]

    wild_rn = RANK_NAMES.get(GAME.deck.wild_rank, str(GAME.deck.wild_rank)) if GAME.deck.wild_rank else ""
    if GAME.config.joker_mode == "OPEN_CARD_WILD":
        joker_mode_name = "Joker Gantung (3 Aktif, 1 Mati)"
        wild_indicator_text = f"★ JOKER GANTUNG: {wild_rn} (3 Aktif, 1 Mati)"
    else:
        joker_mode_name = "Joker Asli (2 Fisik)"
        wild_indicator_text = "★ JOKER ASLI: 2 Fisik (Merah & Hitam)"

    layoff_options = []
    if TURN_STATE["step"] == "ROUND_OVER":
        all_table_melds = []
        for p_m in GAME.players:
            all_table_melds.extend(p_m.open_melds)
        if TURN_STATE.get("last_winner_melds"):
            all_table_melds.extend(TURN_STATE["last_winner_melds"])
        human_open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in human.open_melds], GAME.config)
        layoff_options = find_all_layoff_options(human.hand, all_table_melds, GAME.config, open_table_pts=human_open_pts)

    return {
        "round_number": GAME.round_number,
        "deck_remaining": GAME.deck.remaining,
        "human_open_melds": human_open_melds,
        "wild_rank": GAME.deck.wild_rank,
        "wild_rank_name": wild_rn,
        "wild_indicator": wild_indicator_text,
        "joker_mode": GAME.config.joker_mode,
        "joker_mode_name": joker_mode_name,
        "allow_gap_pickup": GAME.config.allow_gap_pickup,
        "current_player_idx": GAME.current_player_idx,
        "is_human_turn": (GAME.current_player_idx == 0 and TURN_STATE["step"] != "ROUND_OVER"),
        "turn_step": TURN_STATE["step"],
        "drawn_card": serialize_card(TURN_STATE["drawn_card"]) if TURN_STATE["drawn_card"] else None,
        "discard_pile": discard_list,
        "human_hand": hand_list,
        "players": players_data,
        "tutup_options": tutup_payload,
        "layoff_options": layoff_options,
        "last_message": TURN_STATE["last_message"],
        "round_result": TURN_STATE["round_result"],
        "active_skins": ACTIVE_SKINS
    }


class RemiHttpHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Sajikan file statis dari subfolder 'web'
        web_dir = os.path.join(CURRENT_DIR, "web")
        super().__init__(*args, directory=web_dir, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self._send_json(get_game_state_payload())
        elif parsed.path == "/api/skins":
            self._send_json({
                "catalog": SKIN_CATALOG,
                "active": ACTIVE_SKINS
            })
        elif parsed.path == "/api/profile":
            today_str = datetime.now().strftime("%Y-%m-%d")
            can_claim = (USER_PROFILE.get("daily_login_claimed_date") != today_str)
            profile_data = {
                "coins": USER_PROFILE.get("coins", 100),
                "last_login_date": USER_PROFILE.get("last_login_date", today_str),
                "daily_login_claimed_date": USER_PROFILE.get("daily_login_claimed_date"),
                "can_claim_daily_login": can_claim,
                "unlocked_skins": USER_PROFILE.get("unlocked_skins", []),
                "quests": USER_PROFILE.get("quests", {}),
            }
            self._send_json({
                "profile": profile_data,
                "coins": profile_data["coins"],
                "can_claim_daily_login": can_claim,
                "unlocked_skins": profile_data["unlocked_skins"],
                "quests": profile_data["quests"],
                "interactive_items": INTERACTIVE_ITEMS,
                "topup_packages": TOPUP_PACKAGES
            })
        else:
            # Fallback ke static files (web/index.html dsb)
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = {}
        if content_length > 0:
            body_str = self.rfile.read(content_length).decode("utf-8")
            if body_str:
                try:
                    post_data = json.loads(body_str)
                except Exception:
                    pass

        global GAME, TURN_STATE, ACTIVE_SKINS

        # 1. NEW ROUND
        if parsed.path == "/api/new_round":
            # Ronde berikutnya dimulai oleh pemain dengan nilai skor tertinggi
            highest_player = max(GAME.players, key=lambda p: p.score)
            starter_idx = GAME.players.index(highest_player)

            GAME.start_new_round(starting_player_idx=starter_idx)
            GAME.current_player_idx = starter_idx
            TURN_STATE["drawn_card"] = None
            TURN_STATE["round_result"] = None
            TURN_STATE["tutup_options"] = []

            starter_name = GAME.players[starter_idx].name
            if starter_idx == 0:
                TURN_STATE["step"] = "DRAW"
                TURN_STATE["last_message"] = f"Ronde baru dimulai! Anda memiliki nilai skor tertinggi ({highest_player.score} pt) dan mulai pertama!"
            else:
                TURN_STATE["step"] = "BOT_TURN"
                TURN_STATE["last_message"] = f"Ronde baru dimulai! {starter_name} memiliki nilai skor tertinggi ({highest_player.score} pt) dan mulai pertama!"

            self._send_json(get_game_state_payload())

        # 2. DRAW FROM DECK (KOCOKAN)
        elif parsed.path == "/api/draw_deck":
            human = GAME.players[0]
            if GAME.current_player_idx != 0 or TURN_STATE["step"] != "DRAW":
                self._send_json({"error": "Bukan giliran menarik kartu!"}, status=400)
                return

            if GAME.deck.is_empty():
                result = GAME.handle_round_end_draw()
                TURN_STATE["step"] = "ROUND_OVER"
                TURN_STATE["round_result"] = result
                if result.get("is_cuci_tangan"):
                    TURN_STATE["last_message"] = "Kocokan habis! Cuci tangan murni (0 poin karena tidak ada yang menarik buangan)."
                else:
                    TURN_STATE["last_message"] = "Kocokan habis! Skor tetap dihitung dari kartu terbuka di meja & denda kartu mentah."
                self._send_json(get_game_state_payload())
                return

            drawn = GAME.draw_from_deck(human)
            TURN_STATE["drawn_card"] = drawn
            TURN_STATE["is_kocokan"] = True
            TURN_STATE["discarder_idx"] = None

            # Cek apakah langsung bisa tutup
            t_opts = check_tutup(human.hand, GAME.config, open_melds=human.open_melds)
            if t_opts:
                TURN_STATE["step"] = "CHOICE_TUTUP"
                TURN_STATE["tutup_options"] = t_opts
                TURN_STATE["last_message"] = f"Anda menarik {drawn}. Kartu Anda BISA TUTUP / CEKIH!"
            else:
                TURN_STATE["step"] = "DISCARD"
                TURN_STATE["tutup_options"] = []
                TURN_STATE["last_message"] = f"Anda menarik kartu {drawn}. Silakan pilih 1 kartu untuk dibuang."

            self._send_json(get_game_state_payload())

        # 3. SCOOP FROM DISCARD (SEROK BUANGAN)
        elif parsed.path == "/api/scoop_discard":
            human = GAME.players[0]
            if GAME.current_player_idx != 0 or TURN_STATE["step"] != "DRAW":
                self._send_json({"error": "Bukan giliran menarik kartu!"}, status=400)
                return

            if GAME.round_number == 1 and GAME.config.first_round_deck_only:
                self._send_json({"error": "Putaran pertama dilarang ambil kartu buangan!"}, status=400)
                return

            depth = post_data.get("depth", 0)
            hand_indices = post_data.get("pair_indices", [])

            if len(hand_indices) < 2:
                self._send_json({"error": "Minimal memilih 2 kartu dari tangan untuk disambung!"}, status=400)
                return

            if len(set(hand_indices)) != len(hand_indices):
                self._send_json({"error": "Kartu tangan tidak boleh ganda!"}, status=400)
                return

            if any(idx < 0 or idx >= len(human.hand) for idx in hand_indices):
                self._send_json({"error": "Indeks kartu tangan tidak valid!"}, status=400)
                return

            cards_from_hand = [human.hand[idx] for idx in hand_indices]
            target_entry = GAME.discard_pile[depth]
            target_discarder = target_entry.discarded_by

            success, msg, scooped = GAME.scoop_from_discard(0, depth, cards_from_hand)
            if not success:
                self._send_json({"error": msg}, status=400)
                return

            # Update quest "scoop_discard"
            quests = USER_PROFILE.get("quests", {})
            if "scoop_discard" in quests:
                quests["scoop_discard"]["progress"] = min(quests["scoop_discard"]["target"], quests["scoop_discard"]["progress"] + 1)
                save_user_profile(USER_PROFILE)

            TURN_STATE["drawn_card"] = None
            TURN_STATE["is_kocokan"] = False
            TURN_STATE["discarder_idx"] = target_discarder

            # Cek Tutup
            t_opts = check_tutup(human.hand, GAME.config, open_melds=human.open_melds)
            if t_opts:
                TURN_STATE["step"] = "CHOICE_TUTUP"
                TURN_STATE["tutup_options"] = t_opts
                TURN_STATE["last_message"] = f"Berhasil serok {len(scooped)} kartu! Kartu Anda BISA TUTUP / CEKIH!"
            else:
                TURN_STATE["step"] = "DISCARD"
                TURN_STATE["tutup_options"] = []
                TURN_STATE["last_message"] = f"Berhasil serok {len(scooped)} kartu! Silakan pilih 1 kartu untuk dibuang."

            self._send_json(get_game_state_payload())

        # 4. ACTION TUTUP / GANTUNG
        elif parsed.path == "/api/action_tutup":
            human = GAME.players[0]
            if TURN_STATE["step"] != "CHOICE_TUTUP":
                self._send_json({"error": "Bukan tahap pilihan tutup!"}, status=400)
                return

            action = post_data.get("action", "TUTUP")  # 'TUTUP' atau 'GANTUNG'
            opt_idx = post_data.get("option_index", 0)

            if action == "TUTUP":
                if not TURN_STATE["tutup_options"]:
                    self._send_json({"error": "Tidak ada kombinasi tutup!"}, status=400)
                    return
                close_card, melds = TURN_STATE["tutup_options"][opt_idx]
                if close_card in human.hand:
                    human.remove_card(close_card)

                res = GAME.handle_round_end_tutup(
                    winner_idx=0,
                    closing_card=close_card,
                    melds=melds,
                    is_kocokan_win=TURN_STATE["is_kocokan"],
                    discarder_idx=TURN_STATE["discarder_idx"]
                )
                TURN_STATE["step"] = "ROUND_OVER"
                TURN_STATE["round_result"] = res
                TURN_STATE["last_winner_melds"] = [m.cards for m in melds]
                TURN_STATE["last_message"] = f"🎉 SELAMAT! Anda TUTUP dengan kartu kunci {close_card}!"

                # Update quests
                quests = USER_PROFILE.get("quests", {})
                if "play_rounds" in quests:
                    quests["play_rounds"]["progress"] = min(quests["play_rounds"]["target"], quests["play_rounds"]["progress"] + 1)
                if "win_round" in quests:
                    quests["win_round"]["progress"] = min(quests["win_round"]["target"], quests["win_round"]["progress"] + 1)
                save_user_profile(USER_PROFILE)
            else:
                # GANTUNG: jika ada Joker di hand yang membentuk kombinasi/menyambung, satukan ke open_melds
                if TURN_STATE["tutup_options"]:
                    chosen_idx = opt_idx if opt_idx < len(TURN_STATE["tutup_options"]) else 0
                    _, melds = TURN_STATE["tutup_options"][chosen_idx]
                    for m in melds:
                        for c in m.cards:
                            if c.is_joker and c in human.hand:
                                human.remove_card(c)
                                # Satukan ke open_melds meja agar aman dari denda -250
                                added = False
                                for om in human.open_melds:
                                    if len(om) >= 3 and is_valid_meld(om + [c], GAME.config)[0]:
                                        om.append(c)
                                        added = True
                                        break
                                if not added:
                                    human.add_open_meld([c])
                TURN_STATE["step"] = "DISCARD"
                TURN_STATE["last_message"] = "🎲 Anda memilih CEKIH GANTUNG! (Joker diamankan/disatukan). Silakan buang 1 kartu."

            self._send_json(get_game_state_payload())

        # 5. DISCARD CARD
        elif parsed.path == "/api/discard":
            human = GAME.players[0]
            if GAME.current_player_idx != 0 or TURN_STATE["step"] != "DISCARD":
                self._send_json({"error": "Bukan giliran membuang kartu!"}, status=400)
                return

            card_idx = post_data.get("card_index", -1)
            if card_idx < 0 or card_idx >= len(human.hand):
                self._send_json({"error": "Kartu yang dipilih tidak valid!"}, status=400)
                return

            card_to_discard = human.hand[card_idx]
            if card_to_discard.is_joker:
                has_non_joker = any(not c.is_joker for c in human.hand)
                if has_non_joker:
                    self._send_json({"error": "Dilarang membuang Joker! Joker tidak boleh dibuang (Denda -250)."}, status=400)
                    return

            GAME.execute_discard(0, card_to_discard)

            # Giliran beralih ke bot berikutnya
            GAME.current_player_idx = 1
            TURN_STATE["step"] = "BOT_TURN"
            TURN_STATE["drawn_card"] = None
            TURN_STATE["last_message"] = f"Anda membuang kartu {card_to_discard}. Giliran Pak RT..."
            self._send_json(get_game_state_payload())

        # 6. BOT STEP
        elif parsed.path == "/api/bot_step":
            current_idx = GAME.current_player_idx
            if current_idx == 0:
                # Sudah giliran human
                TURN_STATE["step"] = "DRAW"
                self._send_json(get_game_state_payload())
                return

            if GAME.deck.is_empty():
                result = GAME.handle_round_end_draw()
                TURN_STATE["step"] = "ROUND_OVER"
                TURN_STATE["round_result"] = result
                if result.get("is_cuci_tangan"):
                    TURN_STATE["last_message"] = "Kocokan habis! Cuci tangan murni (0 poin karena tidak ada yang menarik buangan)."
                else:
                    TURN_STATE["last_message"] = "Kocokan habis! Skor tetap dihitung dari kartu terbuka di meja & denda kartu mentah."
                self._send_json(get_game_state_payload())
                return

            bot: BotPlayer = GAME.players[current_idx]  # type: ignore
            discard_cards = GAME.get_discard_cards()
            action, depth, pair = bot.decide_draw(
                discard_cards,
                is_first_round=(GAME.round_number == 1 and GAME.config.first_round_deck_only),
                config=GAME.config
            )

            is_kocokan = True
            discarder_idx = None
            bot_msg = ""

            if action == "DISCARD" and depth is not None and pair is not None:
                target_entry = GAME.discard_pile[depth]
                discarder_idx = target_entry.discarded_by
                success, msg, scooped = GAME.scoop_from_discard(current_idx, depth, pair)
                if success:
                    is_kocokan = False
                    bot_msg = f"{bot.name} MENYEROK {len(scooped)} kartu buangan dengan kartu {target_entry.card}!"
                else:
                    GAME.draw_from_deck(bot)
                    bot_msg = f"{bot.name} menarik 1 kartu dari kocokan."
            else:
                GAME.draw_from_deck(bot)
                bot_msg = f"{bot.name} menarik 1 kartu dari kocokan."

            # Cek Tutup Bot
            t_opts = check_tutup(bot.hand, GAME.config, open_melds=bot.open_melds)
            if t_opts:
                should_tutup, close_c, melds = bot.decide_tutup_or_gantung(t_opts, GAME.deck.remaining)
                if should_tutup:
                    if close_c in bot.hand:
                        bot.remove_card(close_c)
                    res = GAME.handle_round_end_tutup(
                        winner_idx=current_idx,
                        closing_card=close_c,
                        melds=melds,
                        is_kocokan_win=is_kocokan,
                        discarder_idx=discarder_idx
                    )
                    TURN_STATE["step"] = "ROUND_OVER"
                    TURN_STATE["round_result"] = res
                    TURN_STATE["last_winner_melds"] = [m.cards for m in melds]
                    TURN_STATE["last_message"] = f"🏆 {bot.name} BERTERIAK TUTUP dengan kartu kunci {close_c}!"
                    quests = USER_PROFILE.get("quests", {})
                    if "play_rounds" in quests:
                        quests["play_rounds"]["progress"] = min(quests["play_rounds"]["target"], quests["play_rounds"]["progress"] + 1)
                        save_user_profile(USER_PROFILE)
                    self._send_json(get_game_state_payload())
                    return

            # Bot Buang Kartu
            discard_c = bot.decide_discard(GAME.config)
            GAME.execute_discard(current_idx, discard_c)
            bot_msg += f" Lalu membuang kartu {discard_c}."

            # Maju ke pemain berikutnya
            GAME.current_player_idx = (current_idx + 1) % 4
            if GAME.current_player_idx == 0:
                GAME.round_number += 1
                TURN_STATE["step"] = "DRAW"
                TURN_STATE["last_message"] = f"{bot_msg} Giliran Anda sekarang!"
            else:
                next_bot_name = GAME.players[GAME.current_player_idx].name
                TURN_STATE["step"] = "BOT_TURN"
                TURN_STATE["last_message"] = f"{bot_msg} Giliran {next_bot_name}..."

            self._send_json(get_game_state_payload())

        # 7. SELECT SKIN
        elif parsed.path == "/api/skins/select":
            cat = post_data.get("category")
            skin_id = post_data.get("skin_id")
            if cat in ACTIVE_SKINS:
                ACTIVE_SKINS[cat] = skin_id
            self._send_json({"success": True, "active": ACTIVE_SKINS})

        # 8. TAUNT / GERTAK CEKIH KE PEMAIN SEBELUM KITA
        elif parsed.path == "/api/taunt":
            target_bot_idx = 3  # Pak Sukardi (pemain tepat sebelum kita)
            target_bot = GAME.players[target_bot_idx]
            taunt_type = ACTIVE_SKINS.get("taunt_fx", "batu_ronda")

            taunt_dict = {
                "batu_ronda": {"desc": "Lempar Batu Kali 🪨", "sound": "rock", "icon": "🪨"},
                "siram_air": {"desc": "Siram Air Segelas 💧", "sound": "water", "icon": "💧"},
                "sandal_jepit": {"desc": "Lempar Sandal Jepit 🩴", "sound": "smack", "icon": "🩴"}
            }
            item = taunt_dict.get(taunt_type, taunt_dict["batu_ronda"])

            import random
            bot_dialogs = [
                "Ampun bos, jangan di-cekihin!",
                "Waduh beneran nih nunggu buangan gua?!",
                "Gemetar nih tangan gua, kartu apa ya yang aman?",
                "Santai atuh, jangan lempar-lempar!"
            ]
            bot_reply = random.choice(bot_dialogs)
            TURN_STATE["last_message"] = f"🚨 ANDA {item['desc'].upper()} KE {target_bot.name.upper()}! {target_bot.name}: '{bot_reply}'"

            self._send_json({
                "success": True,
                "target_idx": target_bot_idx,
                "target_name": target_bot.name,
                "bot_reply": bot_reply,
                "taunt_type": taunt_type,
                "icon": item["icon"],
                "desc": item["desc"],
                "state": get_game_state_payload()
            })

        # 9. GANTI MODE JOKER (JOKER GANTUNG VS JOKER ASLI)
        elif parsed.path == "/api/set_joker_mode":
            mode = post_data.get("mode")
            if mode in ("OPEN_CARD_WILD", "TWO_JOKERS"):
                GAME.config.joker_mode = mode
                GAME.start_new_round(starting_player_idx=0)
                GAME.current_player_idx = 0
                mode_label = "Joker Gantung (3 Aktif, 1 Mati)" if mode == "OPEN_CARD_WILD" else "Joker Asli (2 Fisik)"
                TURN_STATE["step"] = "DRAW"
                TURN_STATE["drawn_card"] = None
                TURN_STATE["tutup_options"] = []
                TURN_STATE["round_result"] = None
                TURN_STATE["last_message"] = f"🎲 Mode Joker diganti ke: {mode_label}. Ronde baru dimulai!"
                self._send_json(get_game_state_payload())
        # 10. MULAI MATCH DENGAN ATURAN AWAL YANG DISEPAKATI
        elif parsed.path == "/api/start_match_with_rules":
            joker_mode = post_data.get("joker_mode", "OPEN_CARD_WILD")
            allow_gap_pickup = post_data.get("allow_gap_pickup", False)
            player_name = post_data.get("player_name", "Kamu")
            custom_players = post_data.get("players", None)

            if joker_mode in ("OPEN_CARD_WILD", "TWO_JOKERS"):
                GAME.config.joker_mode = joker_mode
            GAME.config.allow_gap_pickup = bool(allow_gap_pickup)

            # Atur nama-nama pemain di meja
            if custom_players and len(custom_players) == 4:
                for idx, p_info in enumerate(custom_players):
                    GAME.players[idx].name = p_info.get("name", GAME.players[idx].name)
            else:
                GAME.players[0].name = player_name
                GAME.players[1].name = "Pak RT"
                GAME.players[2].name = "Pak RW"
                GAME.players[3].name = "Pak Sukardi"

            # Reset skor semua pemain ke 0 untuk match baru
            for p in GAME.players:
                p.score = 0

            GAME.start_new_round(starting_player_idx=0)
            GAME.current_player_idx = 0
            TURN_STATE["step"] = "DRAW"
            TURN_STATE["drawn_card"] = None
            TURN_STATE["tutup_options"] = []
            TURN_STATE["round_result"] = None
            mode_lbl = "Joker Gantung (3+1 Mati)" if GAME.config.joker_mode == "OPEN_CARD_WILD" else "Joker Asli (2 Fisik)"
            gap_lbl = "Tarik Sisip Boleh" if GAME.config.allow_gap_pickup else "Wajib Gandeng (Dilarang Sisip)"
            TURN_STATE["last_message"] = f"Meja 4 pemain dibuka! Aturan: {mode_lbl} | {gap_lbl}. Giliran {GAME.players[0].name}!"
            self._send_json(get_game_state_payload())

        # 11. UPDATE LAYOFFS (Pemain menentukan kartu mana yang mau disambung ke meja)
        elif parsed.path == "/api/update_layoffs":
            if TURN_STATE["step"] != "ROUND_OVER":
                self._send_json({"error": "Hanya bisa menyambung kartu saat permainan berakhir!"}, status=400)
                return

            human = GAME.players[0]
            selected_indices = post_data.get("selected_indices", [])

            # Kumpulkan seluruh rangkaian terbuka di meja
            all_table_melds = []
            for p in GAME.players:
                all_table_melds.extend(p.open_melds)
            if TURN_STATE.get("last_winner_melds"):
                all_table_melds.extend(TURN_STATE["last_winner_melds"])

            is_valid, msg, hand_meld_pts, pen, meld_name = validate_layoff_selection(human.hand, selected_indices, all_table_melds, GAME.config)
            if not is_valid:
                self._send_json({"error": msg}, status=400)
                return

            human.layoff_indices = selected_indices

            # Hitung ulang skor ronde untuk Human
            rr = TURN_STATE.get("round_result")
            if rr and not rr.get("is_pure_tutup_tangan"):
                open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in human.open_melds], GAME.config)
                key_pen = rr.get("key_discard_penalties", {}).get("Kamu", 0)
                old_round_pts = rr["round_scores"].get("Kamu", 0)
                new_round_pts = open_pts + hand_meld_pts + pen + key_pen
                human.score = human.score - old_round_pts + new_round_pts
                rr["round_scores"]["Kamu"] = new_round_pts

                deadwood_cards = [human.hand[i] for i in range(len(human.hand)) if i not in selected_indices]
                bd = get_deadwood_breakdown(deadwood_cards, GAME.config)
                bd["open_pts"] = open_pts
                bd["hand_meld_pts"] = hand_meld_pts
                bd["deadwood_pen"] = pen
                bd["saved_cards_count"] = len(selected_indices)
                bd["connected_indices"] = selected_indices
                bd["layoff_desc"] = meld_name
                if "breakdowns" in rr:
                    rr["breakdowns"]["Kamu"] = bd

            self._send_json({
                "success": True,
                "message": msg,
                "state": get_game_state_payload()
            })

        # 12. AUTO LAYOFFS (Sambung otomatis rekomendasi terbaik)
        elif parsed.path == "/api/auto_layoffs":
            if TURN_STATE["step"] != "ROUND_OVER":
                self._send_json({"error": "Hanya bisa menyambung kartu saat permainan berakhir!"}, status=400)
                return

            human = GAME.players[0]
            all_table_melds = []
            for p in GAME.players:
                all_table_melds.extend(p.open_melds)
            if TURN_STATE.get("last_winner_melds"):
                all_table_melds.extend(TURN_STATE["last_winner_melds"])

            best_indices, pen, hand_meld_pts, meld_name = find_optimal_layoffs(human.hand, all_table_melds, GAME.config)
            human.layoff_indices = best_indices

            rr = TURN_STATE.get("round_result")
            if rr and not rr.get("is_pure_tutup_tangan"):
                open_pts = calculate_meld_points([Meld("TERBUKA", m) for m in human.open_melds], GAME.config)
                key_pen = rr.get("key_discard_penalties", {}).get("Kamu", 0)
                old_round_pts = rr["round_scores"].get("Kamu", 0)
                new_round_pts = open_pts + hand_meld_pts + pen + key_pen
                human.score = human.score - old_round_pts + new_round_pts
                rr["round_scores"]["Kamu"] = new_round_pts

                deadwood_cards = [human.hand[i] for i in range(len(human.hand)) if i not in best_indices]
                bd = get_deadwood_breakdown(deadwood_cards, GAME.config)
                bd["open_pts"] = open_pts
                bd["hand_meld_pts"] = hand_meld_pts
                bd["deadwood_pen"] = pen
                bd["saved_cards_count"] = len(best_indices)
                bd["connected_indices"] = best_indices
                bd["layoff_desc"] = meld_name
                if "breakdowns" in rr:
                    rr["breakdowns"]["Kamu"] = bd

            self._send_json({
                "success": True,
                "message": f"Otomatis menyambungkan {meld_name} ke meja (+{hand_meld_pts} pt)!",
                "state": get_game_state_payload()
            })

        # 12. KLAIM BONUS LOGIN HARIAN (+20 KOIN EMAS)
        elif parsed.path == "/api/claim_daily_login":
            today_str = datetime.now().strftime("%Y-%m-%d")
            if USER_PROFILE.get("daily_login_claimed_date") == today_str:
                self._send_json({"error": "Bonus login harian sudah diklaim hari ini! Datang lagi besok."}, status=400)
                return
            USER_PROFILE["coins"] = USER_PROFILE.get("coins", 100) + 20
            USER_PROFILE["daily_login_claimed_date"] = today_str
            save_user_profile(USER_PROFILE)
            self._send_json({
                "success": True,
                "message": "Selamat! Anda mendapatkan +20 Koin Emas bonus login harian!",
                "coins": USER_PROFILE["coins"],
                "can_claim_daily_login": False
            })

        # 13. KLAIM HADIAH MISI HARIAN
        elif parsed.path == "/api/claim_quest":
            q_id = post_data.get("quest_id")
            quests = USER_PROFILE.get("quests", {})
            if q_id not in quests:
                self._send_json({"error": "Misi tidak ditemukan!"}, status=400)
                return
            q = quests[q_id]
            if q.get("claimed"):
                self._send_json({"error": "Hadiah misi ini sudah diklaim!"}, status=400)
                return
            if q.get("progress", 0) < q.get("target", 1):
                self._send_json({"error": "Misi belum selesai!"}, status=400)
                return
            reward = q.get("reward", 10)
            USER_PROFILE["coins"] = USER_PROFILE.get("coins", 100) + reward
            q["claimed"] = True
            save_user_profile(USER_PROFILE)
            self._send_json({
                "success": True,
                "message": f"Berhasil klaim +{reward} Koin Emas!",
                "coins": USER_PROFILE["coins"],
                "quests": quests
            })

        # 14. TOP-UP KOIN EMAS (SIMULASI BEBAS OJK & SANDBOX DEMO)
        elif parsed.path == "/api/topup":
            pack_id = post_data.get("package_id")
            pack = next((p for p in TOPUP_PACKAGES if p["id"] == pack_id), None)
            if not pack:
                self._send_json({"error": "Paket top-up tidak ditemukan!"}, status=400)
                return
            added_coins = pack["coins"] + pack.get("bonus", 0)
            USER_PROFILE["coins"] = USER_PROFILE.get("coins", 100) + added_coins
            save_user_profile(USER_PROFILE)
            self._send_json({
                "success": True,
                "message": f"Top-Up Simulasi Sukses! +{added_coins} Koin Emas telah ditambahkan ke dompet Anda.",
                "coins": USER_PROFILE["coins"],
                "package": pack
            })

        # 15. INTERAKSI KLIK PEMAIN & KIRIM EMOT / LEMPARAN (HIGGS DOMINO STYLE)
        elif parsed.path == "/api/interact_player":
            target_idx = post_data.get("target_idx", 3)
            item_id = post_data.get("item_id", "sandal_jepit")
            item = next((it for it in INTERACTIVE_ITEMS if it["id"] == item_id), None)
            if not item:
                self._send_json({"error": "Item interaksi tidak valid!"}, status=400)
                return
            if target_idx < 1 or target_idx >= len(GAME.players):
                self._send_json({"error": "Target pemain tidak valid!"}, status=400)
                return
            target_bot = GAME.players[target_idx]
            cost = item.get("cost", 0)
            current_coins = USER_PROFILE.get("coins", 100)
            if cost > 0:
                if current_coins < cost:
                    self._send_json({"error": f"Koin emas tidak cukup! Butuh {cost} Koin (Saldo Anda: {current_coins} Koin)."}, status=400)
                    return
                USER_PROFILE["coins"] = current_coins - cost
                save_user_profile(USER_PROFILE)

            # Update misi "send_emotes"
            quests = USER_PROFILE.get("quests", {})
            if "send_emotes" in quests:
                quests["send_emotes"]["progress"] = min(quests["send_emotes"]["target"], quests["send_emotes"]["progress"] + 1)
                save_user_profile(USER_PROFILE)

            reply = get_bot_interactive_dialog(target_bot.name, item_id)
            TURN_STATE["last_message"] = f"🎯 ANDA {item['name'].upper()} KE {target_bot.name.upper()}! {target_bot.name}: '{reply}'"

            self._send_json({
                "success": True,
                "target_idx": target_idx,
                "target_name": target_bot.name,
                "bot_reply": reply,
                "item": item,
                "coins_left": USER_PROFILE.get("coins", 100),
                "state": get_game_state_payload()
            })

        # 16. DEKLARASI RESMI CEKIH (DENGAN VALIDASI ATURAN)
        elif parsed.path == "/api/declare_cekih":
            human = GAME.players[0]
            is_cekih, msg, waiting = check_is_cekih(human.hand, GAME.config, open_melds=human.open_melds)
            if not is_cekih:
                self._send_json({
                    "success": False,
                    "is_cekih": False,
                    "message": msg
                })
                return

            waiting_display = [serialize_card(c) for c in waiting[:6]]
            TURN_STATE["last_message"] = f"🚨 {human.name} RESMI BERTERIAK CEKIH! 'Gua Cekih nih, nunggu kartu kunci!'"
            self._send_json({
                "success": True,
                "is_cekih": True,
                "message": msg,
                "waiting_cards": waiting_display,
                "state": get_game_state_payload()
            })

        # 17. BELI SKIN DENGAN KOIN EMAS
        elif parsed.path == "/api/skins/buy":
            cat = post_data.get("category")
            skin_id = post_data.get("skin_id")
            found_item = None
            for c_key, items in SKIN_CATALOG.items():
                for it in items:
                    if it["id"] == skin_id:
                        found_item = it
                        break
                if found_item:
                    break
            if not found_item:
                self._send_json({"error": "Skin tidak ditemukan!"}, status=400)
                return
            price_coins = found_item.get("price_coins", 0)
            unlocked = USER_PROFILE.setdefault("unlocked_skins", [])
            if skin_id not in unlocked and price_coins > 0:
                current_coins = USER_PROFILE.get("coins", 100)
                if current_coins < price_coins:
                    self._send_json({"error": f"Koin emas tidak cukup! Butuh {price_coins} Koin (Saldo Anda: {current_coins} Koin)."}, status=400)
                    return
                USER_PROFILE["coins"] = current_coins - price_coins
                unlocked.append(skin_id)
                save_user_profile(USER_PROFILE)

            if cat in ACTIVE_SKINS:
                ACTIVE_SKINS[cat] = skin_id
            self._send_json({
                "success": True,
                "active": ACTIVE_SKINS,
                "unlocked_skins": unlocked,
                "coins": USER_PROFILE.get("coins", 100)
            })

        else:
            self._send_json({"error": "Endpoint tidak ditemukan"}, status=404)


def run_server(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, RemiHttpHandler)
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"🃏 SERVER REMI CEKIH BERJALAN DI: {url}")
    print(f"Membuka browser otomatis...")
    print(f"Tekan Ctrl + C di terminal ini untuk berhenti.")
    print(f"=======================================================\n")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
