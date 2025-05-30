import os
import asyncio
import discord
from discord.ext import commands, tasks
import re
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

# ========== EMBED BUILDER BOT ==========
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
    count = 0
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))
            count += 1
        if count == 25:
            break
    if not options:
        options.append(discord.SelectOption(label="No channels available", value="0"))
    return options

# ---------- Modal Classes ----------
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
            self.state.color = 0x00ff00  # fallback to green
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

# ---------- View Class ----------
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

# ========== ORDER MANAGER BOT ==========
bot2 = commands.Bot(command_prefix="!", intents=intents)

MONTHS = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

# --- Helper: Get category name in "27april orders" format ---
def get_order_category_name(day, month):
    return f"{day}{month.lower()} orders"

# --- Helper: Parse order info from channel name ---
def parse_order_info_from_channel(name):
    match = re.match(r"(\d{1,2})([a-zA-Z]+)", name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2).lower()
        for month in MONTHS:
            if month_raw.startswith(month[:3]):
                return day, month
    return None, None

# --- Helper: Is an "order date" category ---
def is_order_category(cat):
    return re.match(r"\d{1,2}[a-z]+ orders$", cat.name)

# --- Helper: Sort key for order categories (chronological) ---
def category_sort_key(cat):
    match = re.match(r"(\d{1,2})([a-z]+) orders$", cat.name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2)
        for idx, month in enumerate(MONTHS):
            if month_raw == month[:len(month_raw)]:
                return (idx, day)
    return (99, 99)

# --- Command: !order ---
@bot2.command()
@commands.has_permissions(manage_channels=True)
async def order(ctx, *, order_name):
    # Only rename the channel, don't move or arrange here
    await ctx.channel.edit(name=order_name)
    # Arranger task will handle placement silently

# --- Command: !editorder ---
@bot2.command()
@commands.has_permissions(manage_channels=True)
async def editorder(ctx, *, new_name):
    # Only rename, don't move or arrange
    await ctx.channel.edit(name=new_name)
    # Arranger task will handle placement silently

# --- Arranger Task: keep all orders sorted and placed correctly ---
@bot2.event
async def on_ready():
    arranger.start()

@tasks.loop(seconds=15)
async def arranger():
    for guild in bot2.guilds:
        categories = list(guild.categories)
        # Find all order date categories
        order_cats = [cat for cat in categories if is_order_category(cat)]
        manual_cats = [cat for cat in categories if not is_order_category(cat)]

        # Check all channels: move any order channel into correct category
        for channel in guild.text_channels:
            day, month = parse_order_info_from_channel(channel.name)
            if day and month:
                order_cat_name = get_order_category_name(day, month)
                cat = discord.utils.get(order_cats, name=order_cat_name)
                # If category doesn't exist, make it
                if not cat:
                    cat = await guild.create_category(order_cat_name)
                    order_cats.append(cat)
                # Move channel if not already in right cat
                if channel.category != cat:
                    await channel.edit(category=cat)
        # Delete empty order categories
        for cat in order_cats:
            if len(cat.channels) == 0:
                await cat.delete()
        # Sort all order categories by date, leaving manual cats in their places
        sorted_orders = sorted([cat for cat in guild.categories if is_order_category(cat)], key=category_sort_key)
        insert_index = 0
        for i, cat in enumerate(guild.categories):
            if not is_order_category(cat):
                insert_index = i + 1
        # Insert after last manual
        for idx, cat in enumerate(sorted_orders):
            # Only move if not already at desired position
            pos = insert_index + idx
            if cat.position != pos:
                await cat.edit(position=pos)

# --- START BOTH BOTS TOGETHER ---
async def main():
    await asyncio.gather(
        bot1.start(os.environ['DISCORD_TOKEN']),
        bot2.start(os.environ['DISCORD_TOKEN_ORDER'])
    )

if __name__ == "__main__":
    asyncio.run(main())
