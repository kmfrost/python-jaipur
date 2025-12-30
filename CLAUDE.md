# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python implementation of Jaipur, a 2-player trading card game. The project is structured for game play and AI/RL experimentation.

## Running the Game

```bash
python3 play.py
```

This starts an interactive game with Player 1 as human (keyboard input) and Player 2 as RandomPlayer (AI).

## Dependencies

- `numpy` - Array operations
- `pygame` - GUI rendering (GUIPlayer)
- `gym` - RL environment interface (incomplete)

No setup.py/pyproject.toml exists - pure Python with manual dependency installation.

## Package Management

Use `uv` for packag management within the `.venv` virtual environment.

## Architecture

### Core Classes

**GameEngine** (`GameEngine.py`) - Central game state and rules manager:
- Manages deck, market (5 visible cards), player hands, tokens, bonus tokens
- Inner class `PlayerState` tracks per-player state
- Four action types: Take Camels (`c`), Grab card (`g`), Sell cards (`s`), Trade (`t`)
- Seven card types: leather, spice, cloth, silver, gold, diamond, camel (indices 0-6)
- Actions return `(success: bool, info: dict)`

**Player hierarchy**:
```
Player (base, interactive human)
├── RandomPlayer (valid random moves, working AI)
├── GUIPlayer (pygame UI, incomplete)
└── DQNPlayer (empty skeleton)
```

**JaipurEnv** (`rl_scripts/JaipurEnv.py`) - OpenAI Gym environment wrapper (incomplete)

### Game Flow

```
play.py → GameEngine.start_game() → alternating player.take_action() → game end
```

Game state accessed via `GameEngine.get_state()` which returns sanitized state dict.

### Key Patterns

- Type indices 0-6 used throughout instead of named constants
- Action codes: `"c"`, `"s"`, `"g"`, `"t"`
- Private methods prefixed with `_`
- List-based hand representation, sorted after modifications
- Market positions referenced by integer index (0-4)

## Development Status

**Complete**: Game engine, text player, RandomPlayer, scoring with tiebreakers

**Incomplete/Skeleton**: GUIPlayer (render stubs), DQNPlayer (empty), JaipurEnv (stubs), `rl_scripts/train.py` (empty)

## Game Rules Quick Reference

- Market: 5 cards (starts with 3 camels + 2 random)
- Hand limit: 7 non-camel cards
- Sell constraints: high-tier goods (silver/gold/diamond) require minimum 2 cards
- End conditions: 3+ token stacks depleted OR deck empty
- Camel majority bonus: +5 points
