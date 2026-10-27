# atomheart

A Python chess library providing a unified interface for chess board operations and move handling.

## Release 0.3.0

This release requires Python 3.14 and the published `valanga==0.3.0`. It preserves
the validated Morpion rules, canonical identities, checkpoints, and core game
behavior, with precise generic state and undo-token contracts. The base package
remains installable without either optional chess backend.

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
pip install atomheart==0.3.0
pip install 'atomheart[chess]==0.3.0'
pip install 'atomheart[chess-rust]==0.3.0'
pip install 'atomheart[all]==0.3.0'
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
uv pip install -e '.[test,dev,all]'
source .venv/bin/activate
tox
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

Tests, lint, and typing install `valanga==0.3.0` from PyPI. CI and release
workflows use the same published dependency through tox. The optional Rust
binding has no established published CPython 3.14 wheel; a local source build
was validated on Linux, and availability on other platforms is not guaranteed.
