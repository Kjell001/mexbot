#!/usr/bin/env python3

# Basic
from random import shuffle

# Discord
from discord.ext import commands

# API request
import requests
import json
from html import unescape


class Quiz(commands.Cog):
    OPENTDB_ENDPOINT = 'https://opentdb.com/api.php'
    NO_QUESTION = -1

    def __init__(self, bot):
        self.bot = bot

    def fetch_question(self):
        # Make request
        params = {'amount': 1, 'type': 'multiple'}
        response = requests.get(self.OPENTDB_ENDPOINT, params)
        if not 200 <= response.status_code < 300:
            raise ConnectionError(f'{self.OPENTDB_ENDPOINT} could not be reached.')
        # Gather data
        data = json.loads(response.content)
        trivia = data['results'][0]
        question = unescape(trivia['question'])
        answer_correct = unescape(trivia['correct_answer'])
        answers = [unescape(a) for a in trivia['incorrect_answers']]
        # Append correct answer to wrong answers
        answers.append(answer_correct)
        return question, answers

    def make_message(self, question, answers):
        # Format question and answers
        line_quiz = f'*Secret quiz time: {question}*\n'
        lines_answers = []
        for i, answer in enumerate(answers):
            lines_answers.append('|| {} ||  {}'.format(
                '✅' if i == len(answers) - 1 else '❌',
                answer
            ))
        # Shuffle answers
        shuffle(lines_answers)
        # Return message
        return line_quiz + '\n'.join(lines_answers)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Quiz: loaded commands')

    @commands.command('ramswoertherevival', aliases=['rwr'])
    async def quiz(self, ctx):
        try:
            question, answers = self.fetch_question()
        except ConnectionError as inst:
            print(inst)
        else:
            await ctx.send(self.make_message(question, answers))
