import sys
sys.path.insert(0,'/src/mtginator/')
import random
import json
import cards
import re


class Deck(object):

    def __init__(self, name=''):
        self.main = []
        self.side = []
        self.deck_file = ''
        self.name = name
        self.total_cards = 0  # not including side
        self.db = CardDB()

    def shuffle(self):
        random.shuffle(self.main)

    def draw_card(self):
        return self.main.pop()

    def put_on_top(self, card):
        self.main.append(card)

    def put_on_bottom(self, card):
        self.main.insert(0, card)

    def load_deck(self, input_file='', file_type="txt"):
        ''' need cockatrice XML parse here as well'''

        self.deck_file = input_file
        df = open(input_file)
        regular = re.compile(r'(\d+)\s+(.+)$')
        sideRe = re.compile(r'side(?i)')
        side = False
        for line in df.readlines():
            #  pre filters
            if sideRe.search(line):
                side = True
                continue
            if line.isspace() or line.find('#') >= 0 or line.find('/') >= 0:
                # probably a comment line
                continue
            card_line = regular.match(line)
            if not card_line:
                print("Odd line in deck: %s" % (line))
                continue
            num = int(card_line.group(1))
            card_name = card_line.group(2).strip()
            try:
                template = self.db.by_card[card_name]
            except KeyError:
                print("Could not find %s in db" % (card_name))
                continue

            for n in range(num):
                if side:
                    self.side.append(cards.Card(card_data=template))
                else:
                    self.main.append(cards.Card(card_data=template))
        self.total_cards = len(self.main)


class CardDB(object):
    ''' this reads all MTG cards from JSON.  It should be memoized '''
    def __init__(self, input_file='./data/AllSets-x.json'):
        self.all = json.load(open(input_file))

        hashed = {}
        for s in self.all.values():
            hashed.update({c['name']: c for c in s['cards']})

        self.by_card = hashed
