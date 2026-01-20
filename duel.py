from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
from .models import GameState

@dataclass(frozen=True)
class Action:
    kind: str
    actor: Literal["player", "bot"]
    card: Optional[str] = None  # id carte si besoin

def draw(state: GameState, who: Literal["player","bot"], n: int = 1) -> None:
    p = state.player if who == "player" else state.bot
    for _ in range(n):
        if not p.deck:
            state.log.append(f"{p.name} n'a plus de cartes : défaite (deck out).")
            return
        p.hand.append(p.deck.pop(0))

def next_phase(phase: str) -> str:
    order = ["DRAW","STANDBY","MAIN1","BATTLE","MAIN2","END"]
    i = order.index(phase)
    return order[(i+1) % len(order)]

def apply_action(state: GameState, action: Action) -> GameState:
    # Copie pydantic “soft” (mutations ok pour MVP). Plus tard: immutabilité.
    if action.kind == "END_PHASE":
        old = state.phase
        state.phase = next_phase(state.phase)
        state.log.append(f"Phase: {old} -> {state.phase}")

        # fin de tour si on passe de END à DRAW
        if old == "END" and state.phase == "DRAW":
            state.turn += 1
            state.active = "bot" if state.active == "player" else "player"
            state.log.append(f"Tour {state.turn}. Joueur actif: {state.active}")
        return state

    if action.kind == "DRAW_STEP":
        if state.phase != "DRAW":
            state.log.append("Impossible : pas en DRAW.")
            return state
        draw(state, state.active, 1)
        state.log.append(f"{state.active} pioche 1 carte.")
        return state

    state.log.append("Action inconnue.")
    return state

