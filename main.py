import os
import asyncio
import random
import re
from datetime import timedelta
import discord
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput, button
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.members = True

# ---------------- EMBED BUILDER BOT ---------------- #
bot1 = commands.Bot(command_prefix="!", intents=intents)

class EmbedBuilderState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.title = ""
        self.description = ""
        self.image_url = ""
        self.color = 0x00ff00
        self.channel_id = None
        self.thumbnail_url = ""
    def build_embed(self):
        embed = discord.Embed(
            title=self.title or "No Title",
            description=self.description or "No Description",
            color=self.color
        )
        if self.image_url:
            embed.set_image(url=self.image_url)
        if self.thumbnail_url:
            embed.set_thumbnail(url=self.thumbnail_url)
        return embed

user_states = {}
def get_channel_options(guild):
    options = []
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))
        if len(options) == 25:
            break
    if not options:
        options.append(discord.SelectOption(label="No channels available", value="0"))
    return options

class SetTitleModal(discord.ui.Modal, title="Set Embed Title"):
    new_title = discord.ui.TextInput(label="Title", max_length=256)
    def __init__(self, state, preview_message, channel_options):
        super().__init__()
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
    async def on_submit(self, interaction: discord.Interaction):
        self.state.title = self.new_title.value
        await self.preview_message.edit(
            embed=self.state.build_embed(),
            view=EmbedBuilderView(self.state, self.preview_message, self.channel_options)
        )
        await interaction.response.send_message("Title updated!", ephemeral=True)

class SetDescriptionModal(discord.ui.Modal, title="Set Embed Description"):
    new_desc = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=2048)
    def __init__(self, state, preview_message, channel_options):
        super().__init__()
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
    async def on_submit(self, interaction: discord.Interaction):
        self.state.description = self.new_desc.value
        await self.preview_message.edit(
            embed=self.state.build_embed(),
            view=EmbedBuilderView(self.state, self.preview_message, self.channel_options)
        )
        await interaction.response.send_message("Description updated!", ephemeral=True)

class SetImageModal(discord.ui.Modal, title="Set Image URL"):
    image_url = discord.ui.TextInput(label="Direct Image URL", placeholder="https://...", max_length=1024)
    def __init__(self, state, preview_message, channel_options):
        super().__init__()
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
    async def on_submit(self, interaction: discord.Interaction):
        self.state.image_url = self.image_url.value
        await self.preview_message.edit(
            embed=self.state.build_embed(),
            view=EmbedBuilderView(self.state, self.preview_message, self.channel_options)
        )
        await interaction.response.send_message("Image updated!", ephemeral=True)

class SetColorModal(discord.ui.Modal, title="Set Embed Color"):
    color_hex = discord.ui.TextInput(label="Hex Color (e.g., 0xff5733 or #ff5733)", max_length=10)
    def __init__(self, state, preview_message, channel_options):
        super().__init__()
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
    async def on_submit(self, interaction: discord.Interaction):
        color_str = self.color_hex.value.strip().replace("#", "0x")
        try:
            color_val = int(color_str, 16)
            self.state.color = color_val
        except Exception:
            self.state.color = 0x00ff00
        await self.preview_message.edit(
            embed=self.state.build_embed(),
            view=EmbedBuilderView(self.state, self.preview_message, self.channel_options)
        )
        await interaction.response.send_message("Color updated!", ephemeral=True)

class SetThumbnailModal(discord.ui.Modal, title="Set Thumbnail (Logo) URL"):
    thumbnail_url = discord.ui.TextInput(label="Direct Thumbnail/Logo URL", placeholder="https://...", max_length=1024)
    def __init__(self, state, preview_message, channel_options):
        super().__init__()
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
    async def on_submit(self, interaction: discord.Interaction):
        self.state.thumbnail_url = self.thumbnail_url.value
        await self.preview_message.edit(
            embed=self.state.build_embed(),
            view=EmbedBuilderView(self.state, self.preview_message, self.channel_options)
        )
        await interaction.response.send_message("Thumbnail updated!", ephemeral=True)

class EmbedBuilderView(discord.ui.View):
    def __init__(self, state, preview_message, channel_options):
        super().__init__(timeout=None)
        self.state = state
        self.preview_message = preview_message
        self.channel_options = channel_options
        self.select_channel.options = channel_options
    @discord.ui.button(label="Set Title", style=discord.ButtonStyle.primary)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        await interaction.response.send_modal(SetTitleModal(self.state, self.preview_message, self.channel_options))
    @discord.ui.button(label="Set Description", style=discord.ButtonStyle.primary)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        await interaction.response.send_modal(SetDescriptionModal(self.state, self.preview_message, self.channel_options))
    @discord.ui.button(label="Set Image URL", style=discord.ButtonStyle.secondary)
    async def set_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        await interaction.response.send_modal(SetImageModal(self.state, self.preview_message, self.channel_options))
    @discord.ui.button(label="Set Color", style=discord.ButtonStyle.secondary)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        await interaction.response.send_modal(SetColorModal(self.state, self.preview_message, self.channel_options))
    @discord.ui.button(label="Set Thumbnail (Logo)", style=discord.ButtonStyle.secondary)
    async def set_thumbnail(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        await interaction.response.send_modal(SetThumbnailModal(self.state, self.preview_message, self.channel_options))
    @discord.ui.select(
        placeholder="Select Channel to Send Embed...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't edit this embed!", ephemeral=True)
        self.state.channel_id = int(select.values[0])
        await interaction.response.send_message(f"Embed will be sent to <#{self.state.channel_id}>", ephemeral=True)
    @discord.ui.button(label="Send Embed!", style=discord.ButtonStyle.success)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.state.user_id:
            return await interaction.response.send_message("You can't send this embed!", ephemeral=True)
        if not self.state.channel_id:
            return await interaction.response.send_message("Please select a channel!", ephemeral=True)
        channel = interaction.guild.get_channel(self.state.channel_id)
        if not channel:
            return await interaction.response.send_message("Selected channel not found.", ephemeral=True)
        await channel.send(embed=self.state.build_embed())
        await interaction.response.send_message(f"Embed sent to {channel.mention}!", ephemeral=True)
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.preview_message:
            await self.preview_message.edit(view=self)
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.state.user_id

@bot1.command()
async def embedbuilder(ctx):
    state = EmbedBuilderState(ctx.author.id)
    user_states[ctx.author.id] = state
    channel_options = get_channel_options(ctx.guild)
    embed = state.build_embed()
    view = EmbedBuilderView(state, None, channel_options)
    view.select_channel.options = channel_options
    msg = await ctx.send(embed=embed, view=view)
    view.preview_message = msg

# ---------------- ORDER MANAGER BOT ---------------- #
bot2 = commands.Bot(command_prefix="!", intents=intents)

MONTHS = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

def get_order_category_name(day, month):
    return f"{day}{month.lower()} orders"

def parse_order_info_from_channel(name):
    match = re.match(r"(\d{1,2})([a-zA-Z]+)", name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2).lower()
        for month in MONTHS:
            if month_raw.startswith(month[:3]):
                return day, month
    return None, None

def is_order_category(cat):
    return re.match(r"\d{1,2}[a-z]+ orders$", cat.name)

def category_sort_key(cat):
    match = re.match(r"(\d{1,2})([a-z]+) orders$", cat.name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2)
        for idx, month in enumerate(MONTHS):
            if month_raw == month[:len(month_raw)]:
                return (idx, day)
    return (99, 99)

@bot2.command()
@commands.has_permissions(manage_channels=True)
async def order(ctx, *, order_name):
    await ctx.channel.edit(name=order_name)

@bot2.command()
@commands.has_permissions(manage_channels=True)
async def editorder(ctx, *, new_name):
    await ctx.channel.edit(name=new_name)

@tasks.loop(seconds=15)
async def arranger():
    for guild in bot2.guilds:
        categories = list(guild.categories)
        order_cats = [cat for cat in categories if is_order_category(cat)]
        for channel in guild.text_channels:
            day, month = parse_order_info_from_channel(channel.name)
            if day and month:
                order_cat_name = get_order_category_name(day, month)
                cat = discord.utils.get(order_cats, name=order_cat_name)
                if not cat:
                    cat = await guild.create_category(order_cat_name)
                    order_cats.append(cat)
                if channel.category != cat:
                    await channel.edit(category=cat)
        for cat in order_cats:
            if len(cat.channels) == 0:
                await cat.delete()
        sorted_orders = sorted([cat for cat in guild.categories if is_order_category(cat)], key=category_sort_key)
        pos = max([cat.position for cat in guild.categories if not is_order_category(cat)], default=-1) + 1
        for idx, cat in enumerate(sorted_orders):
            if cat.position != pos + idx:
                await cat.edit(position=pos + idx)

@bot2.event
async def on_ready():
    print("Order Manager bot is online!")
    if not arranger.is_running():
        arranger.start()

# ---------------- GIVEAWAY BOT ---------------- #
bot3 = commands.Bot(command_prefix="!", intents=intents)

GIVEAWAY_CONFIG = {}
GIVEAWAY_ENTRANTS = set()
GIVEAWAY_MESSAGE_ID = None
GIVEAWAY_EMOJI = None
GIVEAWAY_WINNERS = []
GIVEAWAY_TIMER = None

class GiveawaySetupModal(Modal):
    def __init__(self, admin_ctx):
        super().__init__(title="Giveaway Setup")
        self.admin_ctx = admin_ctx
        self.title_input = TextInput(label="Giveaway Title", placeholder="1000 Member Giveaway", max_length=80)
        self.desc_input = TextInput(label="Giveaway Description", placeholder="Description...", style=discord.TextStyle.paragraph, max_length=400)
        self.emoji_input = TextInput(label="Prize Emoji", placeholder="🎉", max_length=2)
        self.winner_count_input = TextInput(label="How many winners? (max 10)", placeholder="5", max_length=2)
        self.duration_input = TextInput(label="Duration (e.g. 1d, 30m, 30s)", placeholder="30s", max_length=8)
        self.add_item(self.title_input)
        self.add_item(self.desc_input)
        self.add_item(self.emoji_input)
        self.add_item(self.winner_count_input)
        self.add_item(self.duration_input)

    async def on_submit(self, interaction: discord.Interaction):
        admin_id = self.admin_ctx.user.id if hasattr(self.admin_ctx, "user") else self.admin_ctx.author.id
        # Field checks
        title = self.title_input.value.strip()
        desc = self.desc_input.value.strip()
        emoji = self.emoji_input.value.strip()
        winner_count_str = self.winner_count_input.value.strip()
        duration = self.duration_input.value.strip()
        if not (title and desc and emoji and winner_count_str and duration):
            await interaction.response.send_message("All fields are required.", ephemeral=True)
            return
        try:
            winner_count = int(winner_count_str)
            if winner_count < 1 or winner_count > 10:
                raise ValueError
        except Exception:
            await interaction.response.send_message("Winner count must be a number (1-10).", ephemeral=True)
            return
        # Save config for this admin
        GIVEAWAY_CONFIG[admin_id] = {
            "title": title,
            "description": desc,
            "emoji": emoji,
            "winner_count": winner_count,
            "winner_names": [],  # Will set later
            "duration": duration,
            "end_message": "",
            "admin_id": admin_id,
            "channel_id": self.admin_ctx.channel.id if hasattr(self.admin_ctx, "channel") else self.admin_ctx.channel_id
        }
        await interaction.response.send_message(
            "Giveaway setup received!\n"
            "Now DM me a comma-separated list of winners (e.g., @user1, @user2, ...), then the end message.",
            ephemeral=True)


@bot3.event
async def on_message(message):
    # Complete setup by DM after modal
    if message.guild is None and message.author != bot3.user:
        config = GIVEAWAY_CONFIG.get(message.author.id)
        if config and not config["winner_names"]:
            winner_list = [n.strip() for n in message.content.split(",") if n.strip()]
            config["winner_names"] = winner_list
            await message.channel.send("Now, reply with the end message for the giveaway (e.g., 'Congratulations!').")
        elif config and config["winner_names"] and not config["end_message"]:
            config["end_message"] = message.content
            await message.channel.send("Giveaway config complete! You can now run !startgiveaway in the server.")
    await bot3.process_commands(message)


from discord import app_commands

@bot3.tree.command(name="setupgiveaway", description="Setup a new giveaway.")
@app_commands.checks.has_permissions(administrator=True)
async def setupgiveaway_slash(interaction: discord.Interaction):
    modal = GiveawaySetupModal(interaction)
    await interaction.response.send_modal(modal)



@bot3.command()
@commands.has_permissions(administrator=True)
async def startgiveaway(ctx):
    admin_id = ctx.author.id
    config = GIVEAWAY_CONFIG.get(admin_id)
    if not config:
        await ctx.send("No giveaway config found! Use !setupgiveaway first.")
        return
    channel = ctx.guild.get_channel(config["channel_id"]) or ctx.channel
    embed = discord.Embed(title=config["title"], description=config["description"])
    view = GiveawayEnterView(config["emoji"])
    msg = await channel.send(embed=embed, view=view)
    try:
        await msg.add_reaction(config["emoji"])
    except Exception:
        await channel.send("Failed to add emoji, please make sure it's a valid emoji.")
        return
    global GIVEAWAY_MESSAGE_ID, GIVEAWAY_EMOJI, GIVEAWAY_ENTRANTS, GIVEAWAY_WINNERS, GIVEAWAY_TIMER
    GIVEAWAY_MESSAGE_ID = msg.id
    GIVEAWAY_EMOJI = config["emoji"]
    GIVEAWAY_ENTRANTS = set()
    GIVEAWAY_WINNERS = config["winner_names"]
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    overwrites.external_emojis = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
    GIVEAWAY_TIMER = asyncio.create_task(run_giveaway_timer(ctx, msg, config))
    await ctx.send("Giveaway started!")

class GiveawayEnterView(View):
    def __init__(self, emoji):
        super().__init__(timeout=None)
        self.emoji = emoji
    @button(label="Enter Giveaway", style=discord.ButtonStyle.success)
    async def enter_giveaway(self, interaction: discord.Interaction, button):
        if interaction.user.id in GIVEAWAY_ENTRANTS:
            await interaction.response.send_message("You are already entered!", ephemeral=True)
        else:
            GIVEAWAY_ENTRANTS.add(interaction.user.id)
            await interaction.response.send_message("You have entered the giveaway!", ephemeral=True)
    @button(label="Leave Giveaway", style=discord.ButtonStyle.danger)
    async def leave_giveaway(self, interaction: discord.Interaction, button):
        if interaction.user.id in GIVEAWAY_ENTRANTS:
            GIVEAWAY_ENTRANTS.remove(interaction.user.id)
            await interaction.response.send_message("You have left the giveaway.", ephemeral=True)
        else:
            await interaction.response.send_message("You were not entered!", ephemeral=True)

def parse_duration(duration):
    duration = duration.strip().lower()
    num = int(re.match(r"\d+", duration).group())
    if "d" in duration:
        return timedelta(days=num)
    elif "h" in duration:
        return timedelta(hours=num)
    elif "m" in duration:
        return timedelta(minutes=num)
    elif "s" in duration:
        return timedelta(seconds=num)
    return timedelta(minutes=1)

async def run_giveaway_timer(ctx, msg, config):
    delta = parse_duration(config["duration"])
    await asyncio.sleep(delta.total_seconds())
    channel = msg.channel
    winner_count = min(config["winner_count"], len(config["winner_names"]))
    fake_winners = config["winner_names"][:winner_count]
    result_msg = await channel.send("Giveaway has ended! Choosing winners:")
    await asyncio.sleep(1)
    for idx, winner in enumerate(fake_winners):
        roll_list = fake_winners[:]
        for _ in range(6):
            random.shuffle(roll_list)
            await asyncio.sleep(0.2)
            await result_msg.edit(content="Giveaway has ended! Choosing winners:\n"
                                  + '\n'.join(roll_list)
                                  + '\n' + '\n'.join([f"{i+1}." for i in range(idx)]))
        await asyncio.sleep(1)
        await result_msg.edit(content="Giveaway has ended! Choosing winners:\n"
                              + '\n'.join([f"{i+1}. {fake_winners[i]}" if i <= idx else f"{i+1}." for i in range(winner_count)]))
    await asyncio.sleep(1)
    await result_msg.edit(content="Giveaway has ended! Winners:\n"
                          + '\n'.join([f"{i+1}. {w}" for i, w in enumerate(fake_winners)])
                          + f"\n\n{config['end_message']}")

@bot1.event
async def on_ready():
    print("Embed bot is online!")

@bot2.event
async def on_ready():
    print("Order Manager bot is online!")
    if not arranger.is_running():
        arranger.start()

@bot3.event
async def on_ready():
    print("Giveaway bot is online!")
    try:
        synced = await bot3.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def main():
    await asyncio.gather(
        bot1.start(os.environ['DISCORD_TOKEN']),
        bot2.start(os.environ['DISCORD_TOKEN_ORDER']),
        bot3.start(os.environ['DISCORD_TOKEN_GIVEAWAY']),
    )

if __name__ == "__main__":
    asyncio.run(main())
