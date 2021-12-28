#!/usr/bin/env python3

# Basic
from random import shuffle


class Phrases(object):
    SEPARATOR = '-  -  -  -  -  -  -  -  -  -'


class Question(object):
    ICONS_CHOICES = (
        'choice_1',
        'choice_2',
        'choice_3',
        'choice_4'
    )
    ICON_FINISH = 'end_question'
    ICON_CORRECT = 'choice_correct'
    ICON_INCORRECT = 'choice_incorrect'
    POINTS_CORRECT = 3
    POINTS_INCORRECT = -1
    
    def __init__(self, question, answers, user_request, emojis):
        self.question = question
        self.answers = answers
        self.player_request = user_request.mention
        self.emojis = emojis
        self.player_scores = dict()
        self.answers_shuffled = None
        self.index_correct = None
        self.shuffle_answers()
        self.content = None
        self.make_content()
        self.message = None
    
    def get_guild_id(self):
        if self.message:
            return self.message.guild.id
        return None
    
    def shuffle_answers(self):
        indices = list(range(len(self.answers)))
        shuffle(indices)
        self.index_correct = indices.index(0)
        self.answers_shuffled = [self.answers[i] for i in indices]
    
    async def process_reaction(self, reaction, user):
        player = user.mention
        icon = reaction.emoji
        if icon.name == self.ICON_FINISH:
            return await self.finish(player)
        elif icon.name in self.ICONS_CHOICES:
            self.set_player_score(player, icon)
    
    def set_player_score(self, player, icon):
        # Only first answer counts
        if player in self.player_scores:
            return
        # Check if legal choice
        index_choice = self.ICONS_CHOICES.index(icon.name)
        if index_choice >= len(self.answers):
            return
        # Check answer
        if index_choice == self.index_correct:
            self.player_scores[player] = self.POINTS_CORRECT
        else:
            self.player_scores[player] = self.POINTS_INCORRECT
    
    async def finish(self, player=None):
        # Only requesting player can finish
        if player and player != self.player_request:
            return
        # Requesting player gets incorrect if not chosen answer
        if self.player_request not in self.player_scores:
            self.player_scores[self.player_request] = self.POINTS_INCORRECT
        # Show results
        self.update_content()
        await self.send()
        return self.player_scores
    
    def make_content(self):
        # Format question and answers
        line_quiz = f'{self.emojis["buzz"]} **Quiz time!** {self.question}'
        lines_answers = []
        # Indicate choices with colour icons
        for i, answer in enumerate(self.answers_shuffled):
            icon = self.emojis[self.ICONS_CHOICES[i]]
            lines_answers.append(f'{icon}  {answer}')
        # Collect content lines
        lines = [line_quiz] + lines_answers
        self.content = '\n'.join(lines)
    
    def update_content(self):
        # Format question and answers
        line_quiz = f'{self.emojis["buzz"]} **Quiz time!** {self.question}'
        lines_answers = []
        # Indicate choices correctness with icons
        for i, answer in enumerate(self.answers_shuffled):
            if i == self.index_correct:
                icon = self.emojis[self.ICON_CORRECT]
            else:
                icon = self.emojis[self.ICON_INCORRECT]
            lines_answers.append(f'{icon}  {answer}')
        # Summarise quiz results
        winners = [p for p, s in self.player_scores.items() if s > 0]
        losers = [p for p, s in self.player_scores.items() if s <= 0]
        line_losers = f'` {self.POINTS_INCORRECT:+1d} pts ` {", ".join(losers)}'
        line_winners = f'` {self.POINTS_CORRECT:+1d} pts ` {", ".join(winners)}'
        # Collect appropriate content lines
        lines = [line_quiz] + lines_answers + [Phrases.SEPARATOR]
        if winners:
            lines.append(line_winners)
        if losers:
            lines.append(line_losers)
        self.content = '\n'.join(lines)
    
    async def send(self, ctx=None):
        if self.message:
            # Message exists, update with new content
            await self.message.edit(content=self.content)
            # Remove all reactions
            await self.message.clear_reactions()
        else:
            # No message exists yet
            assert ctx, "No context was provided."
            self.message = await ctx.send(self.content)
            # Add reactions
            for i in range(len(self.answers)):
                icon = self.emojis[self.ICONS_CHOICES[i]]
                await self.message.add_reaction(icon)
            await self.message.add_reaction(self.emojis[self.ICON_FINISH])
        return self.message.id
