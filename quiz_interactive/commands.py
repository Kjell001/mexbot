#!/usr/bin/env python3


# Basic
from .question import *
from .controllers import *
import ftp_instance

# Discord
from discord.ext import commands

# API request
import requests
import json
from html import unescape

HOME_GUILD_ID = 800402178673213450


class Quiz(commands.Cog):
    OPENTDB_ENDPOINT = 'https://opentdb.com/api.php'
    
    def __init__(self, bot, ftp_host, ftp_usr, ftp_pwd):
        self.bot = bot
        self.guild_controllers = dict()
        self.ftp = ftp_instance.Connector(ftp_host, ftp_usr, ftp_pwd)
        self.questions = dict()
        self.emojis = None
    
    def store_guild_controller(self, guild_id):
        guild_con = self.guild_controllers.get(guild_id)
        assert guild_con, "No guild controller for this context."
        fname = f'quiz_{guild_id}.pickle'
        try:
            self.ftp.store_instance(guild_con, fname)
            print(f'Stored controller to {fname} on {self.ftp.host}')
        except ConnectionError:
            warn(f'Could not store {fname} to {self.ftp.host} due to a '
                 f'connection error')
    
    def restore_guild_controller(self, guild_id):
        fname = f'quiz_{guild_id}.pickle'
        try:
            if self.ftp.file_exists(fname):
                guild_con = self.ftp.load_instance(fname)
                print(f'Restored controller from {fname} on {self.ftp.host}')
                return guild_con
        except ConnectionError:
            warn(f'Could not attempt to restore {fname} from {self.ftp.host} '
                 f'due to a connection error')
        return None
    
    def add_guild_controller(self, guild_id):
        guild_con = self.restore_guild_controller(guild_id)
        if not guild_con:
            guild_con = GuildController()
        self.guild_controllers[guild_id] = guild_con
    
    def get_guild_controller(self, guild_id):
        if guild_id not in self.guild_controllers:
            self.add_guild_controller(guild_id)
        return self.guild_controllers[guild_id]
    
    def fetch_question(self):
        # Make request
        params = {'amount': 1, 'type': 'multiple'}
        response = requests.get(self.OPENTDB_ENDPOINT, params)
        if not 200 <= response.status_code < 300:
            raise ConnectionError(
                f'{self.OPENTDB_ENDPOINT} could not be reached.')
        # Gather data
        data = json.loads(response.content)
        trivia = data['results'][0]
        question = unescape(trivia['question']).strip()
        answer_correct = unescape(trivia['correct_answer'])
        answers_incorrect = [unescape(a) for a in trivia['incorrect_answers']]
        # Append correct answer to wrong answers
        answers = [answer_correct] + answers_incorrect
        return question, answers
    
    def remove_question(self, message_id):
        del self.questions[message_id]
    
    def process_scores(self, scores, guild_id):
        guild_con = self.get_guild_controller(guild_id)
        guild_con.add_scores(scores)
    
    def cleanup(self):
        for guild_id in self.guild_controllers:
            self.store_guild_controller(guild_id)
            
    async def cleanup2(self):
        [await q.finish() for q in self.questions.values()]
        for guild_id in self.guild_controllers:
            self.store_guild_controller(guild_id)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('Quiz: loaded commands')
        home_guild_emojis = self.bot.get_guild(HOME_GUILD_ID).emojis
        self.emojis = dict((e.name, str(e)) for e in home_guild_emojis)
        print('Quiz: loaded emojis')

    @commands.group(
        'ramswoertherevival',
        aliases=['rwr'],
        invoke_without_command=True
    )
    async def quiz(self, ctx):
        # Fetch trivia
        try:
            question, answers = self.fetch_question()
        except ConnectionError as inst:
            print(inst)
            return
        # Send message
        question = Question(question, answers, ctx.author, self.emojis)
        message_id = await question.send(ctx)
        self.questions[message_id] = question
    
    @quiz.group('score', aliases=['scores', 'tussenstand'])
    async def show_scores(self, ctx):
        guild_con = self.get_guild_controller(ctx.guild.id)
        await ctx.send(guild_con.get_scores_content())
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.questions:
            if user.id == self.bot.user.id:
                return
            await reaction.remove(user)
            question = self.questions[reaction.message.id]
            scores = await question.process_reaction(reaction, user)
            if scores:
                guild_id = reaction.message.guild.id
                self.process_scores(scores, guild_id)
