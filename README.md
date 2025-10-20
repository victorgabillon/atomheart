# atomheart

A Python chess library providing a unified interface for chess board operations and move handling.

## Features

- Chess board representation and manipulation
- Move generation and validation
- Board modification tracking
- Support for both Python-chess and Rust-based backends
- FEN notation support

## About

atomheart is a wrapper library that provides a unified interface over popular chess engines:
- [python-chess](https://github.com/niklasf/python-chess) - Pure Python chess library
- [shakmaty](https://github.com/niklasf/shakmaty) - Rust chess library via Python bindings

This unified interface is designed for use in chess search algorithms and AI agents, allowing seamless switching between backends for optimal performance.

See the repos
- [chipiron](github.com/victorgabillon/chipiron) - Lear AI agents for chess (and maybe later other games).
- [anemone](github.com/victorgabillon/anemone) - Tree search library

## Installation

```bash
pip install atomheart
```

## Quick Start

```python
from atomheart.board import create_board
from atomheart.board.utils import FenPlusHistory

# Create a chess board
board = create_board(
    fen_with_history=FenPlusHistory(current_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    use_rust_boards=True
)

# Make a move
move_key = board.get_move_key_from_uci("e2e4")
board_modification = board.play_move_key(move_key)
```
