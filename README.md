# atomheart

A Python chess library providing a unified interface for chess board operations and move handling.

## Features

- Chess board representation and manipulation
- Move generation and validation
- Board modification tracking
- Support for both Python-chess and Rust-based backends
- FEN notation support
- Morpion Solitaire environment (5T and 5D variants)

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
pip install atomheart[chess]
pip install atomheart[chess-rust]
pip install atomheart[all]
```

The base install keeps the lightweight core games available. Chess support is
optional, and the Rust-backed chess board is enabled by the `chess-rust` extra.

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

## Python 3.14 development

```bash
uv venv --python 3.14
# Install the migrated Valanga wheel before resolving Atomheart.
uv pip install /path/to/valanga-0.2.5-py3-none-any.whl
uv pip install -e '.[test,dev,all]'
source .venv/bin/activate
VALANGA_WHEEL=/path/to/valanga-0.2.5-py3-none-any.whl tox
```

Core annotations use Python 3.14 deferred evaluation with runtime imports needed
by `typing.get_type_hints`. The lazy chess/Rust factories retain string
annotations so optional native types need not be imported. For these factories,
`annotationlib.get_annotations(..., format=annotationlib.Format.STRING)` can
inspect annotations without loading the optional backend.

The acting-role state classes retain their type-checking-only protocol bases to
preserve slotted dataclass layout. Morpion rules, canonical move identities,
checkpoint payloads and stable hashing are unchanged.

`shakmaty_python_binding==0.1.5` currently needs a source build on CPython 3.14
on Linux; its published binary wheel targets CPython 3.11. The complete chess
suite must be run against the actual compiled binding.

Tox requires `VALANGA_WHEEL` so tests, lint and typing cannot silently resolve a
published Valanga wheel. CI builds that wheel from the pinned Valanga migration
commit; push the Valanga commit before running the Atomheart workflow remotely.
