import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load the token from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # Needed for channel listing

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- State Class ----------------
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

user_states = {}  # Holds state for each user

# Helper to get channel select options (limit to 25)
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

# ---------------- Modals ----------------
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

# ---------------- View with Buttons and Select ----------------
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

@bot.command()
async def embedbuilder(ctx):
    state = EmbedBuilderState(ctx.author.id)
    user_states[ctx.author.id] = state

    channel_options = get_channel_options(ctx.guild)
    embed = state.build_embed()
    view = EmbedBuilderView(state, None, channel_options)
    view.select_channel.options = channel_options

    msg = await ctx.send(embed=embed, view=view)
    view.preview_message = msg

bot.run(TOKEN)






