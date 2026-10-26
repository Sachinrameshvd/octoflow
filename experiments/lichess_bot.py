"""OctopusBrain Live Lichess BOT Driver.

Connects the decentralized-centralized OctopusBrain directly to Lichess.org:
1. Streams incoming challenges and auto-accepts them.
2. Slices the 8x8 chessboard into 8 files (Files A-H) mapped to the 8 arm ganglia.
3. Coordinates multi-file moves using lateral message passing and central coalition attention.
4. Transmits live UCI moves (e.g. e2e4, g1f3) back to Lichess via the Bot API.
5. Displays real-time ASCII board and biological semantic chatter in the terminal.

Usage:
    python experiments/lichess_bot.py --token lip_xxxxxxxxxxxxxxxxxxxx
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import httpx
import chess

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from octopus_brain.adapter import OctopusGymAdapter
from octopus_brain.config import OctopusBrainConfig


LICHESS_API_BASE = "https://lichess.org"

PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.2,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}


def encode_board_to_arms(board: chess.Board, is_white: bool) -> list:
    """Encode 8x8 chess board into (8, 16) sensory patches for the 8 arms.

    File A -> Arm 0, File B -> Arm 1 ... File H -> Arm 7.
    Each arm observes:
    - Dims 0-7: Piece values on ranks 1-8 of its file (+ friendly, - opponent).
    - Dims 8-9: Friendly piece count & opponent piece count on this file.
    - Dims 10-11: Attackers attacking this file & defenders defending this file.
    - Dims 12-13: Open file status & center control bonus.
    - Dims 14-15: King proximity & check flag.
    """
    obs = []
    king_sq = board.king(chess.WHITE if is_white else chess.BLACK)
    king_file = chess.square_file(king_sq) if king_sq is not None else 4

    for file_idx in range(8):
        arm_features = [0.0] * 16
        friendly_count = 0
        opponent_count = 0

        # Ranks 1 to 8 (from player's perspective)
        for rank_idx in range(8):
            sq = chess.square(file_idx, rank_idx)
            piece = board.piece_at(sq)
            if piece is not None:
                val = PIECE_VALUES.get(piece.piece_type, 1.0) / 9.0
                if piece.color == (chess.WHITE if is_white else chess.BLACK):
                    arm_features[rank_idx] = val
                    friendly_count += 1
                else:
                    arm_features[rank_idx] = -val
                    opponent_count += 1

        arm_features[8] = friendly_count / 4.0
        arm_features[9] = opponent_count / 4.0
        arm_features[10] = 0.5 if (friendly_count > 0 and opponent_count > 0) else 0.0
        arm_features[11] = 1.0 if (file_idx in [3, 4]) else 0.0  # Center files (D, E)
        arm_features[12] = 1.0 if (friendly_count == 0 and opponent_count == 0) else 0.0  # Fully open file
        arm_features[13] = 1.0 if (friendly_count == 0 and opponent_count > 0) else 0.0  # Half-open file
        arm_features[14] = 1.0 / (1.0 + abs(file_idx - king_file))  # King distance
        arm_features[15] = 1.0 if board.is_check() else 0.0

        obs.append(arm_features)

    return obs


class OctopusLichessBot:
    """Live Lichess BOT controller powered by OctopusBrain."""

    def __init__(self, token: str, checkpoint_path: str = "checkpoints/top1_octopus_brain.pt"):
        self.token = token.strip()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.adapter = OctopusGymAdapter(checkpoint_path=checkpoint_path)
        self.username: str = ""
        self.verify_and_upgrade_account()

    def verify_and_upgrade_account(self):
        """Check account details and upgrade to BOT if needed."""
        url = f"{LICHESS_API_BASE}/api/account"
        res = httpx.get(url, headers=self.headers)
        if res.status_code == 401:
            print("❌ Error: Invalid Lichess token. Please double-check your token.")
            sys.exit(1)
        res.raise_for_status()
        data = res.json()
        self.username = data["username"]
        is_bot = data.get("title") == "BOT"

        print("=" * 80)
        print(f"🐙 OCTOPUSBRAIN LICHESS BOT ACTIVE: @{self.username}")
        print(f"• Account Status: {'Official BOT Account ✅' if is_bot else 'Upgrading to BOT...'}")
        print(f"• Profile URL: https://lichess.org/@/{self.username}")
        print("=" * 80)

        if not is_bot:
            upgrade_url = f"{LICHESS_API_BASE}/api/bot/account/upgrade"
            u_res = httpx.post(upgrade_url, headers=self.headers)
            if u_res.status_code == 200:
                print("✅ Successfully upgraded account to official BOT status!")
            else:
                print(f"ℹ️ Note: Account upgrade response: {u_res.text}")

    def run(self):
        """Main event loop: stream incoming challenges and games."""
        print("\n--> Listening for live challenges on Lichess. Send a challenge in your browser!")
        print(f"--> Go to: https://lichess.org/@/{self.username} and click 'Challenge to a game'\n")

        stream_url = f"{LICHESS_API_BASE}/api/stream/event"
        while True:
            try:
                with httpx.stream("GET", stream_url, headers=self.headers, timeout=90.0) as resp:
                    for line in resp.iter_lines():
                        if line:
                            line_str = line if isinstance(line, str) else line.decode("utf-8")
                            if line_str.strip():
                                event = json.loads(line_str)
                                self.handle_event(event)
            except httpx.HTTPError as e:
                print(f"--> Stream reconnecting ({e})...")
                time.sleep(3)

    def handle_event(self, event: dict):
        event_type = event.get("type")
        if event_type == "challenge":
            challenge = event["challenge"]
            ch_id = challenge["id"]
            challenger = challenge["challenger"]["name"]
            variant = challenge["variant"]["key"]
            speed = challenge["speed"]
            print(f"\n⚡ [INCOMING CHALLENGE] From @{challenger} ({speed}, variant: {variant})")

            # Accept challenge
            accept_url = f"{LICHESS_API_BASE}/api/challenge/{ch_id}/accept"
            res = httpx.post(accept_url, headers=self.headers)
            if res.status_code == 200:
                print(f"✅ Challenge accepted! Entering game room...")
            else:
                print(f"❌ Failed to accept challenge: {res.text}")

        elif event_type == "gameStart":
            game_id = event["game"]["gameId"]
            print(f"\n🎮 [GAME STARTED] Room: https://lichess.org/{game_id}")
            self.play_game(game_id)

    def play_game(self, game_id: str):
        """Handle a single live chess game until completion."""
        game_url = f"{LICHESS_API_BASE}/api/bot/game/stream/{game_id}"
        self.adapter.reset()
        board = chess.Board()
        is_my_turn = False
        my_color_is_white = True

        with httpx.stream("GET", game_url, headers=self.headers, timeout=None) as stream:
            for line in stream.iter_lines():
                if not line:
                    continue
                line_str = line if isinstance(line, str) else line.decode("utf-8")
                if not line_str.strip():
                    continue
                data = json.loads(line_str)
                msg_type = data.get("type")

                if msg_type == "gameFull":
                    white_player = data["white"].get("name", "Unknown")
                    black_player = data["black"].get("name", "Unknown")
                    my_color_is_white = (white_player.lower() == self.username.lower())
                    print(f"  • White: @{white_player} | Black: @{black_player}")
                    print(f"  • OctopusBrain plays: {'WHITE ⚪' if my_color_is_white else 'BLACK ⚫'}")

                    # Catch up moves
                    moves_str = data["state"]["moves"]
                    board = chess.Board()
                    if moves_str:
                        for m in moves_str.split():
                            board.push_uci(m)

                    is_my_turn = (board.turn == chess.WHITE and my_color_is_white) or (board.turn == chess.BLACK and not my_color_is_white)
                    if is_my_turn and not board.is_game_over():
                        self.make_move(game_id, board, my_color_is_white)

                elif msg_type == "gameState":
                    moves_str = data.get("moves", "")
                    board = chess.Board()
                    if moves_str:
                        for m in moves_str.split():
                            board.push_uci(m)

                    status = data.get("status")
                    if status != "started":
                        winner = data.get("winner", "Draw")
                        print(f"\n🏁 [GAME OVER] Status: {status} | Winner: {winner}")
                        print("=" * 80)
                        return

                    is_my_turn = (board.turn == chess.WHITE and my_color_is_white) or (board.turn == chess.BLACK and not my_color_is_white)
                    if is_my_turn and not board.is_game_over():
                        self.make_move(game_id, board, my_color_is_white)

                elif msg_type == "chatLine":
                    pass

    def make_move(self, game_id: str, board: chess.Board, my_color_is_white: bool):
        """Evaluate board using OctopusBrain and submit move to Lichess."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return

        # 1. Encode 8 files to (8, 16) observation
        obs = encode_board_to_arms(board, my_color_is_white)

        # 2. Query OctopusBrain via universal adapter
        actions, info = self.adapter.predict(obs, deterministic=True)

        # 3. Select best legal move:
        # Prioritize moves from arms with high gating / coalition formation, captures, and checks
        best_move = legal_moves[0]
        best_score = -999.0

        for move in legal_moves:
            score = 0.0
            from_file = chess.square_file(move.from_square)
            to_file = chess.square_file(move.to_square)

            # Preference if origin arm gated a report to central brain
            if info["report_events"][from_file]:
                score += 2.5

            # Preference if origin and destination arms form a coalition team
            for c in info["coalition_clusters"]:
                if from_file in c and to_file in c:
                    score += 4.0

            # Capture bonus
            if board.is_capture(move):
                target_piece = board.piece_at(move.to_square)
                score += 3.0 + (PIECE_VALUES.get(target_piece.piece_type, 1.0) if target_piece else 1.0)

            # Check bonus
            board.push(move)
            if board.is_check():
                score += 2.0
            board.pop()

            # Center advancement bonus
            if move.to_square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                score += 1.5

            if score > best_score:
                best_score = score
                best_move = move

        uci_move = best_move.uci()
        from_arm = chess.square_file(best_move.from_square)

        # 4. Transmit move to Lichess API
        move_url = f"{LICHESS_API_BASE}/api/bot/game/{game_id}/move/{uci_move}"
        res = httpx.post(move_url, headers=self.headers)

        # 5. Display real-time telemetry and ASCII board
        report_str = "".join(["●" if r else "○" for r in info["report_events"]])
        coalitions = info["coalition_clusters"]
        coalition_str = ", ".join([f"({','.join(map(str, c))})" for c in coalitions]) if coalitions else "None"

        print(f"\n  [Move {board.fullmove_number}] OctopusBrain plays: {uci_move.upper()} (Arm #{from_arm} / File {chr(ord('A')+from_arm)})")
        print(f"  • Gating: [{report_str}] ({info['report_rate']*100:2.0f}%) | Coalitions: {coalition_str}")

        # Active biological semantic thoughts
        active_intents = [it for it in info["decoded_intents"] if it["is_reporting"]]
        if active_intents:
            for it in active_intents[:2]:
                print(f"    🗣 Arm #{it['arm_index']}: {it['icon']} {it['label']} ({it['confidence']*100:.0f}%) -> {it['description']}")

        # Mini ASCII board
        print(f"\n{board}\n")


def main():
    parser = argparse.ArgumentParser(description="OctopusBrain Lichess Bot")
    parser.add_argument("--token", type=str, required=True, help="Lichess API personal token")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/top1_octopus_brain.pt", help="Checkpoint path")
    args = parser.parse_args()

    bot = OctopusLichessBot(token=args.token, checkpoint_path=args.checkpoint)
    bot.run()


if __name__ == "__main__":
    main()
