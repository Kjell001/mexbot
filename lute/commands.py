#!/usr/bin/env python3

# Basic
import re

# Discord
from discord.ext import commands
from discord import Embed

# Opregte Unlocker
import opregte

HOME_GUILD_ID = 800402178673213450


class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def make_embed(article):
        embed = Embed(
            title=article.title,
            description=article.lead,
            color=0x007fff
        )
        # Add elements for article info
        if article.published:
            embed.add_field(name='\u200b', value=article.published.strftime('%d %B %Y'))
        if article.authors:
            embed.add_field(name='\u200b', value=article.authors[0])
        if article.image:
            embed.set_image(url=article.image)
        # Add non-inline field for each paragraph
        for paragraph in article.paragraphs:
            if not paragraph.text:
                continue
            if paragraph.header:
                embed.add_field(name=paragraph.header, value=paragraph.text, inline=False)
            else:
                embed.add_field(name='\u200b', value=paragraph.text, inline=False)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        print('Opregte Unlocker: loaded commands')

    @commands.command('unlock', aliases=['opregte'])
    async def unlock(self, ctx, url):
        # Clean URL
        url = re.sub("^<|^>|<$|>$", "", url)
        # Get article
        try:
            article = opregte.Article(url)
        except AssertionError:
            await ctx.message.add_reaction('🦟')  # Mosquito
            return
        except ConnectionError:
            await ctx.message.add_reaction('🦟')  # Mosquito
            await ctx.message.add_reaction('⚠')  # Warning
            return
        # Build message
        embed = self.make_embed(article)
        # Send message
        await ctx.send(embed=embed)
