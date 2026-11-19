from copy import deepcopy

FILES = "abcdefgh"
RANKS = "87654321"

UNICODE_PIECES = {
    "k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙",
    "K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟",
}


class ChessGame:
    def __init__(self):
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.turn = "w"  # 'w' for White, 'b' for Black
        self.castling = {"K": True, "Q": True, "k": True, "q": True}
        self.en_passant = None  # Target square tuple (row, col) or None

    def display(self):
        print("\n    a b c d e f g h")
        print("  +-----------------+")
        for r in range(8):
            row_str = f"{8 - r} | "
            for c in range(8):
                piece = self.board[r][c]
                row_str += (UNICODE_PIECES.get(piece, ".") + " ")
            print(row_str + f"| {8 - r}")
        print("  +-----------------+")
        print("    a b c d e f g h\n")

    @staticmethod
    def parse_square(sq: str) -> tuple[int, int] | None:
        if len(sq) != 2 or sq[0] not in FILES or sq[1] not in RANKS:
            return None
        return RANKS.index(sq[1]), FILES.index(sq[0])

    @staticmethod
    def is_own_piece(piece: str, side: str) -> bool:
        return piece.isupper() if side == "w" else piece.islower()

    @staticmethod
    def is_enemy_piece(piece: str, side: str) -> bool:
        if piece == ".":
            return False
        return piece.islower() if side == "w" else piece.isupper()

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def pseudo_legal_moves(self, r: int, c: int, board=None, castling=None, en_passant=None) -> list[tuple[int, int]]:
        board = board if board is not None else self.board
        castling = castling if castling is not None else self.castling
        en_passant = en_passant if en_passant is not None else self.en_passant

        piece = board[r][c]
        if piece == ".":
            return []

        side = "w" if piece.isupper() else "b"
        kind = piece.upper()
        moves = []

        if kind == "P":
            direction = -1 if side == "w" else 1
            start_row = 6 if side == "w" else 1

            # Forward 1
            if self.in_bounds(r + direction, c) and board[r + direction][c] == ".":
                moves.append((r + direction, c))
                # Forward 2 from starting rank
                if r == start_row and board[r + 2 * direction][c] == ".":
                    moves.append((r + 2 * direction, c))

            # Captures and en passant
            for dc in (-1, 1):
                nr, nc = r + direction, c + dc
                if self.in_bounds(nr, nc):
                    if self.is_enemy_piece(board[nr][nc], side) or (nr, nc) == en_passant:
                        moves.append((nr, nc))

        elif kind == "N":
            for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc) and not self.is_own_piece(board[nr][nc], side):
                    moves.append((nr, nc))

        elif kind in ("B", "R", "Q"):
            directions = []
            if kind in ("B", "Q"):
                directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            if kind in ("R", "Q"):
                directions += [(-1, 0), (1, 0), (0, -1), (0, 1)]

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                while self.in_bounds(nr, nc):
                    target = board[nr][nc]
                    if target == ".":
                        moves.append((nr, nc))
                    elif self.is_enemy_piece(target, side):
                        moves.append((nr, nc))
                        break
                    else:
                        break
                    nr += dr
                    nc += dc

        elif kind == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self.in_bounds(nr, nc) and not self.is_own_piece(board[nr][nc], side):
                        moves.append((nr, nc))

            # Castling
            home_row = 7 if side == "w" else 0
            k_flag = "K" if side == "w" else "k"
            q_flag = "Q" if side == "w" else "q"
            if r == home_row and c == 4:
                if castling.get(k_flag) and board[home_row][5] == "." and board[home_row][6] == ".":
                    moves.append((home_row, 6))
                if (
                    castling.get(q_flag)
                    and board[home_row][3] == "."
                    and board[home_row][2] == "."
                    and board[home_row][1] == "."
                ):
                    moves.append((home_row, 2))

        return moves

    def find_king(self, side: str, board=None) -> tuple[int, int]:
        board = board if board is not None else self.board
        king = "K" if side == "w" else "k"
        for r in range(8):
            for c in range(8):
                if board[r][c] == king:
                    return (r, c)
        raise ValueError("King not found on board")

    def is_square_attacked(self, target_r: int, target_c: int, by_side: str, board=None) -> bool:
        board = board if board is not None else self.board
        no_castling = {"K": False, "Q": False, "k": False, "q": False}
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if self.is_own_piece(piece, by_side):
                    if piece.upper() == "P":
                        direction = -1 if by_side == "w" else 1
                        if (r + direction, c - 1) == (target_r, target_c) or (r + direction, c + 1) == (target_r, target_c):
                            return True
                    else:
                        if (target_r, target_c) in self.pseudo_legal_moves(r, c, board, no_castling, None):
                            return True
        return False

    def in_check(self, side: str, board=None) -> bool:
        board = board if board is not None else self.board
        kr, kc = self.find_king(side, board)
        enemy = "b" if side == "w" else "w"
        return self.is_square_attacked(kr, kc, enemy, board)

    def apply_move_to_board(self, src: tuple[int, int], dst: tuple[int, int], board, castling, en_passant, promo="Q"):
        sr, sc = src
        dr, dc = dst
        piece = board[sr][sc]
        side = "w" if piece.isupper() else "b"
        kind = piece.upper()
        new_en_passant = None

        # En passant capture
        if kind == "P" and (dr, dc) == en_passant:
            board[sr][dc] = "."

        # Double pawn push sets en passant target
        if kind == "P" and abs(dr - sr) == 2:
            new_en_passant = ((sr + dr) // 2, sc)

        # Castling rook movement
        if kind == "K" and abs(dc - sc) == 2:
            if dc == 6:  # Kingside
                board[sr][5] = board[sr][7]
                board[sr][7] = "."
            elif dc == 2:  # Queenside
                board[sr][3] = board[sr][0]
                board[sr][0] = "."

        # Move piece
        board[dr][dc] = piece
        board[sr][sc] = "."

        # Pawn promotion
        if kind == "P" and dr in (0, 7):
            promo_piece = promo.upper() if promo.upper() in ("Q", "R", "B", "N") else "Q"
            board[dr][dc] = promo_piece if side == "w" else promo_piece.lower()

        # Update castling rights
        if piece == "K":
            castling["K"] = castling["Q"] = False
        elif piece == "k":
            castling["k"] = castling["q"] = False
        if src == (7, 0) or dst == (7, 0):
            castling["Q"] = False
        if src == (7, 7) or dst == (7, 7):
            castling["K"] = False
        if src == (0, 0) or dst == (0, 0):
            castling["q"] = False
        if src == (0, 7) or dst == (0, 7):
            castling["k"] = False

        return new_en_passant

    def legal_moves_for_piece(self, r: int, c: int) -> list[tuple[int, int]]:
        piece = self.board[r][c]
        if not self.is_own_piece(piece, self.turn):
            return []

        enemy = "b" if self.turn == "w" else "w"
        legal = []

        for dst in self.pseudo_legal_moves(r, c):
            # Castling cannot pass through or start in check
            if piece.upper() == "K" and abs(dst[1] - c) == 2:
                if self.in_check(self.turn):
                    continue
                step_col = 5 if dst[1] == 6 else 3
                if self.is_square_attacked(r, step_col, enemy):
                    continue

            sim_board = deepcopy(self.board)
            sim_castling = dict(self.castling)
            self.apply_move_to_board((r, c), dst, sim_board, sim_castling, self.en_passant)

            if not self.in_check(self.turn, sim_board):
                legal.append(dst)

        return legal

    def has_any_legal_moves(self) -> bool:
        for r in range(8):
            for c in range(8):
                if self.is_own_piece(self.board[r][c], self.turn):
                    if self.legal_moves_for_piece(r, c):
                        return True
        return False

    def make_move(self, move_str: str) -> tuple[bool, str]:
        parts = move_str.strip().lower().split()
        if len(parts) == 1 and len(parts[0]) in (4, 5):
            raw = parts[0]
            src_str, dst_str = raw[:2], raw[2:4]
            promo = raw[4] if len(raw) == 5 else "q"
        elif len(parts) == 2:
            src_str, dst_str = parts
            promo = "q"
        else:
            return False, "Use coordinate notation like 'e2 e4' or 'e7e8q'."

        src = self.parse_square(src_str)
        dst = self.parse_square(dst_str)
        if src is None or dst is None:
            return False, "Invalid square coordinates."

        if dst not in self.legal_moves_for_piece(*src):
            return False, "Illegal move."

        self.en_passant = self.apply_move_to_board(src, dst, self.board, self.castling, self.en_passant, promo)
        self.turn = "b" if self.turn == "w" else "w"
        return True, "OK"


def play():
    game = ChessGame()
    print("Terminal Chess (enter moves as 'e2 e4' or 'e7e8q' for promotion; 'quit' to exit)")

    while True:
        game.display()
        side_name = "White" if game.turn == "w" else "Black"

        if not game.has_any_legal_moves():
            if game.in_check(game.turn):
                winner = "Black" if game.turn == "w" else "White"
                print(f"Checkmate! {winner} wins.")
            else:
                print("Stalemate! The game is a draw.")
            break

        if game.in_check(game.turn):
            print(f"{side_name} is in check!")

        cmd = input(f"{side_name} to move: ").strip()
        if cmd.lower() in ("quit", "exit"):
            print("Game ended.")
            break

        ok, msg = game.make_move(cmd)
        if not ok:
            print(f"Error: {msg}")


if __name__ == "__main__":
    play()
