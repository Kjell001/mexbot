#!/usr/bin/env python3


# Basic
from .question import *

# Discord
from discord.ext import commands

# API request
import requests
import json
from html import unescape


class Quiz(commands.Cog):
    OPENTDB_ENDPOINT = 'https://opentdb.com/api.php'
    
    def __init__(self, bot):
        self.bot = bot
        self.questions = dict()
    
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
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('QuizInteractive: loaded commands')

    @commands.command('ramswoertherevival', aliases=['rwr'])
    async def quiz(self, ctx):
        # Fetch trivia
        try:
            question, answers = self.fetch_question()
        except ConnectionError as inst:
            print(inst)
            return
        # Send message
        question = Question(question, answers)
        message_id = await question.send(ctx)
        self.questions[message_id] = question
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.questions:
            if user.id == self.bot.user.id:
                print('My reaction!')
                return
            await reaction.remove(user)
            question = self.questions[reaction.message.id]
            question.set_player_score(user, reaction)
