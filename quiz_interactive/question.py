#!/usr/bin/env python3

# Basic
from random import shuffle


class Question(object):
    ICONS = ['🟦', '🟧', '🟩', '🟨']
    
    def __init__(self, question, answers):
        self.question = question
        self.answers = answers
        self.message = None
        self.player_scores = dict()
        self.index_correct = None
        self.content = None
        self.content_updated = None
        self.finished = False
        self.make_content()
    
    async def send(self, ctx):
        self.message = await ctx.send(self.content)
        for icon in self.ICONS:
            await self.message.add_reaction(icon)
        return self.message.id
    
    def finish(self):
        pass
    
    def set_player_score(self, user, reaction):
        pass
    
    def make_content(self):
        # Shuffle answers
        indices = list(range(len(self.answers)))
        shuffle(indices)
        self.index_correct = indices.index(0)
        answers_shuffled = [self.answers[i] for i in indices]
        # Format question and answers
        line_quiz = f'*Secret quiz time: {self.question}*\n'
        lines_answers = []
        for i, answer in enumerate(answers_shuffled):
            lines_answers.append(f'{self.ICONS[i]}  {answer}')
        # Results
        self.content = line_quiz + '\n'.join(lines_answers)
    
    def update_content(self):
        pass
