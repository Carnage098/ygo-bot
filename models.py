from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import random

Phase = Literal["DRAW", "STANDBY", "MAIN1", "BATTLE", "MAIN2", "END"]

class PlayerState(BaseModel):
    user_id: int
    name: str
    deck: List[str] = Field(default_factory=list)
    hand: List[str] = Field(default_factory=list)
    gy: List[str] = Field(default_factory=list)
    field_mz: List[Optional[str]] = Field(default_factory=lambda: [None]*5)
    field_st: List[Optional[str]] = Field(default_factory=lambda: [None]*5)
    lp: int = 8000

class GameState(BaseModel):
    duel_id: str
    channel_id: int
    player: PlayerState
    bot: PlayerState
    turn: int = 1
    active: Literal["player", "bot"] = "player"
    phase: Phase = "DRAW"
    log: List[str] = Field(default_factory=list)

def shuffle_deck(cards: List[str]) -> List[str]:
    cards = cards[:]
    random.shuffle(cards)
    return cards

