import os
import discord
from discord.ext import commands
import re

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

MONTHS = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]

def parse_date_from_name(name):
    match = re.match(r"(\d{1,2})([A-Za-z]+)", name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2).lower()
        for month in MONTHS:
            if month_raw.startswith(month[:3]):
                return (day, month.capitalize(), f"{day}{month.capitalize()}")
    return None

def category_sort_key(cat):
    match = re.match(r"(\d{1,2})([A-Za-z]+)", cat.name)
    if match:
        day = int(match.group(1))
        month_raw = match.group(2).lower()
        for idx, month in enumerate(MONTHS):
            if month_raw.startswith(month[:3]):
                return (idx, day)
    return (99, 99)

async def move_category_to_bottom(guild, cat):
    cats = [c for c in guild.categories]
    order_cats = [c for c in cats if parse_date_from_name(c.name)]
    other_cats = [c for c in cats if not parse_date_from_name(c.name)]
    sorted_orders = sorted(order_cats, key=category_sort_key)
    bottom_pos = len(other_cats) + len(sorted_orders) - 1
    await cat.edit(position=bottom_pos)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def order(ctx, *, order_name):
    channel = ctx.channel
    guild = ctx.guild
    parsed = parse_date_from_name(order_name)
    if not parsed:
        return await ctx.send("Couldn't parse date from order name. Use format like 26April2Airpods.")
    day, month, cat_name = parsed
    await channel.edit(name=order_name)
    category = discord.utils.get(guild.categories, name=cat_name)
    if not category:
        category = await guild.create_category(cat_name)
    await channel.edit(category=category)
    await move_category_to_bottom(guild, category)
    await ctx.send(f"Order set: {order_name}, moved to category {cat_name}")
    await delete_empty_order_categories(guild)
    await reorder_order_categories(guild)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def editorder(ctx, *, new_name):
    channel = ctx.channel
    guild = ctx.guild
    old_parsed = parse_date_from_name(channel.name)
    new_parsed = parse_date_from_name(new_name)
    if not new_parsed:
        return await ctx.send("Couldn't parse date from new order name. Use format like 27April2Airpods.")
    day, month, new_cat_name = new_parsed
    await channel.edit(name=new_name)
    if not old_parsed or old_parsed[2] != new_cat_name:
        category = discord.utils.get(guild.categories, name=new_cat_name)
        if not category:
            category = await guild.create_category(new_cat_name)
        await channel.edit(category=category)
        await move_category_to_bottom(guild, category)
        await ctx.send(f"Channel moved to category {new_cat_name}")
    await delete_empty_order_categories(guild)
    await reorder_order_categories(guild)

async def delete_empty_order_categories(guild):
    for cat in guild.categories:
        if parse_date_from_name(cat.name) and len(cat.channels) == 0:
            await cat.delete()

async def reorder_order_categories(guild):
    cats = [c for c in guild.categories]
    order_cats = [c for c in cats if parse_date_from_name(c.name)]
    sorted_orders = sorted(order_cats, key=category_sort_key)
    other_cats = [c for c in cats if not parse_date_from_name(c.name)]
    for i, cat in enumerate(sorted_orders):
        new_position = len(other_cats) + i
        await cat.edit(position=new_position)

# Use a custom token for this bot to avoid conflicts
bot.run(os.environ.get('DISCORD_TOKEN_ORDER'))

