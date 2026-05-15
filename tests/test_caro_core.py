import unittest

from source.ai import alpha_beta, minimax
from source.board import AI, PLAYER, Board


class BoardRulesTest(unittest.TestCase):
    def test_win_is_four_in_a_row(self):
        board = Board()
        for col in range(4):
            board.place(2, col, PLAYER)

        self.assertEqual(board.game_over(), PLAYER)

    def test_draw_when_board_is_full_without_winner(self):
        board = Board(9)
        pattern = [
            [1, 1, -1, 1, 1, -1, 1, 1, -1],
            [1, -1, -1, 1, -1, -1, 1, -1, -1],
            [-1, -1, 1, -1, -1, 1, -1, -1, 1],
            [1, 1, -1, 1, 1, -1, 1, 1, -1],
            [1, -1, -1, 1, -1, -1, 1, -1, -1],
            [-1, -1, 1, -1, -1, 1, -1, -1, 1],
            [1, 1, -1, 1, 1, -1, 1, 1, -1],
            [1, -1, -1, 1, -1, -1, 1, -1, -1],
            [-1, -1, 1, -1, -1, 1, -1, -1, 1],
        ]
        for r, row in enumerate(pattern):
            for c, player in enumerate(row):
                board.place(r, c, player)

        self.assertEqual(board.game_over(), 0)

    def test_undo_restores_previous_last_move(self):
        board = Board()
        board.place(4, 4, PLAYER)
        board.place(4, 5, AI)
        board.undo(4, 5)

        self.assertEqual(board.last_move, (4, 4))
        self.assertEqual(board.last_player, PLAYER)
        self.assertEqual(board.empty_cells, board.n * board.n - 1)


class SearchTest(unittest.TestCase):
    def test_ai_takes_immediate_win(self):
        board = Board()
        for col in (3, 4, 5):
            board.place(4, col, AI)
        board.place(1, 1, PLAYER)
        board.place(2, 2, PLAYER)

        result = alpha_beta(board, depth=1, is_maximizing=False)

        self.assertIn(result.move, {(4, 2), (4, 6)})

    def test_ai_blocks_immediate_player_win(self):
        board = Board()
        board.place(4, 2, AI)
        for col in (3, 4, 5):
            board.place(4, col, PLAYER)
        board.place(2, 2, AI)

        result = alpha_beta(board, depth=1, is_maximizing=False)

        self.assertEqual(result.move, (4, 6))

    def test_search_does_not_mutate_board_state(self):
        board = Board()
        board.place(4, 4, PLAYER)
        board.place(4, 5, AI)
        before_grid = [row[:] for row in board.grid]
        before_last_move = board.last_move
        before_last_player = board.last_player
        before_empty = board.empty_cells

        minimax(board, depth=2, is_maximizing=False)
        alpha_beta(board, depth=2, is_maximizing=False)

        self.assertEqual(board.grid, before_grid)
        self.assertEqual(board.last_move, before_last_move)
        self.assertEqual(board.last_player, before_last_player)
        self.assertEqual(board.empty_cells, before_empty)


if __name__ == "__main__":
    unittest.main()
