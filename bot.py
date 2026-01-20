import os, uuid, json
import discord
from discord import app_commands
from dotenv import load_dotenv

from engine.models import GameState, PlayerState, shuffle_deck
from engine.duel import Action, apply_action

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Stockage en mémoire pour MVP (à remplacer par Postgres/Redis)
DUELS: dict[str, GameState] = {}

def load_deck(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["cards"]

def render_duel_embed(state: GameState) -> discord.Embed:
    e = discord.Embed(title=f"Duel #{state.duel_id}")
    e.add_field(name="Tour / Phase", value=f"{state.turn} / {state.phase}", inline=True)
    e.add_field(name="Actif", value=state.active, inline=True)
    e.add_field(name="LP", value=f"{state.player.name}: {state.player.lp}\n{state.bot.name}: {state.bot.lp}", inline=False)
    e.add_field(name="Main (joueur)", value=f"{len(state.player.hand)} cartes (détails en DM)", inline=True)
    e.add_field(name="Main (bot)", value=f"{len(state.bot.hand)} cartes", inline=True)

    last_logs = "\n".join(state.log[-8:]) if state.log else "—"
    e.add_field(name="Log", value=last_logs, inline=False)
    return e

class DuelView(discord.ui.View):
    def __init__(self, duel_id: str):
        super().__init__(timeout=None)
        self.duel_id = duel_id

    @discord.ui.button(label="Draw (actif)", style=discord.ButtonStyle.primary)
    async def draw_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = DUELS.get(self.duel_id)
        if not state:
            return await interaction.response.send_message("Duel introuvable.", ephemeral=True)

        # sécurité simple : seul le joueur peut cliquer (MVP)
        if interaction.user.id != state.player.user_id:
            return await interaction.response.send_message("Tu n'es pas le joueur de ce duel.", ephemeral=True)

        state = apply_action(state, Action(kind="DRAW_STEP", actor="player"))
        DUELS[self.duel_id] = state

        await interaction.response.edit_message(embed=render_duel_embed(state), view=self)

        # renvoyer la main du joueur en DM
        try:
            dm = await interaction.user.create_dm()
            await dm.send(f"Ta main ({len(state.player.hand)}): " + ", ".join(state.player.hand))
        except:
            pass

    @discord.ui.button(label="End Phase", style=discord.ButtonStyle.secondary)
    async def endphase_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = DUELS.get(self.duel_id)
        if not state:
            return await interaction.response.send_message("Duel introuvable.", ephemeral=True)
        if interaction.user.id != state.player.user_id:
            return await interaction.response.send_message("Tu n'es pas le joueur de ce duel.", ephemeral=True)

        state = apply_action(state, Action(kind="END_PHASE", actor="player"))
        DUELS[self.duel_id] = state
        await interaction.response.edit_message(embed=render_duel_embed(state), view=self)

@tree.command(name="duel_start", description="Démarre un duel contre le bot")
async def duel_start(interaction: discord.Interaction):
    duel_id = str(uuid.uuid4())[:8]

    # decks exemple (tu crées data/decks/k9.json etc.)
    player_deck = shuffle_deck(load_deck("data/decks/k9.json"))
    bot_deck = shuffle_deck(load_deck("data/decks/maliss.json"))

    player = PlayerState(user_id=interaction.user.id, name=interaction.user.display_name, deck=player_deck)
    bot = PlayerState(user_id=0, name="Bot", deck=bot_deck)

    state = GameState(
        duel_id=duel_id,
        channel_id=interaction.channel_id,
        player=player,
        bot=bot,
        phase="DRAW",
        active="player",
        log=["Duel créé. Pioche de départ..."]
    )

    # main de départ
    for _ in range(5):
        state.player.hand.append(state.player.deck.pop(0))
        state.bot.hand.append(state.bot.deck.pop(0))
    state.log.append("Chaque joueur pioche 5.")

    DUELS[duel_id] = state

    # message public
    await interaction.response.send_message(embed=render_duel_embed(state), view=DuelView(duel_id))

    # DM main joueur
    try:
        dm = await interaction.user.create_dm()
        await dm.send("Ta main de départ: " + ", ".join(state.player.hand))
    except:
        pass

@client.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {client.user}")

client.run(TOKEN)

