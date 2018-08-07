import re
"""
Defines Card objecs.

"""
# from enum import Enum
# zones = Enum('hand', 'library', 'graveyard', 'battlefield', 'exile')
# permanents = Enum('land', 'creature', 'enchantment', 'artifact', 'planeswalker')
# below should be enums I guess but never bothered to load module

zones = ['hand', 'library', 'graveyard', 'battlefield', 'exile']
permanents = ['Land', 'Creature', 'Enchantment', 'Artifact', 'Planeswalker']
land_mana = {
    'Plains':   'W',
    'Island':   'U',
    'Swamp':    'B',
    'Mountain': 'R',
    'Forest':   'G',
    'Wastes':   'C',
}

# mana costs from MTGJson are {Z} where Z is int or symbol
# hybrid is {S/T}
# X is {X}
# Phyrexian is {Z/P}
allowed_symbols = list(land_mana.values())+['X']
for a in land_mana.values():
    allowed_symbols.append(a+'/P')
    for b in list(land_mana.values())[1:]:
        if a == b:
            continue
        else:
            allowed_symbols.append(a+'/'+b)
            allowed_symbols.append(b+'/'+a)

manas = r'\{\d+\}'
for s in allowed_symbols:
    manas += r'\{'+s+r'\}+'

keywords = [
    'flash',
    'haste',
    'flying',
    'first strike',
    'lifelink',
    'deathtouch',
    'indestructable',
    'reach',
    'trample',
    'double strike',
    'hexproof',
    'vigilance'
    ]
# currently just evergreen keywords
kwre = [re.compile(k+'(?i)') for k in keywords]

templates = {
    'triggered': re.compile(r'(when |whenever)(?i)'),
    'conditional': re.compile(r'if (?i)'),
    'activated': re.compile(r'('+manas+r'|sacrifice \S+|pay \S+):(?i)'),
    'mana_ability': re.compile(r'^(B|G|R|W|U)$|\{T\}: Add ('+manas+') (.*) to your mana pool')
}


class Cost(object):
    """
    Object that defines paying the cost of a card (or ability)

    """

    def __init__(self, fromString="", B=0, G=0, R=0, U=0, W=0, C=0, gen=0, X=False):
        # C = colorless gen = generic
        self.mana = {}
        if fromString:
            bracks = re.compile(r'[\{\}]')
            syms = bracks.split(fromString)
            for symbol in syms:
                if not symbol:
                    continue
                    # split leaves ""s
                try:
                    generic = int(symbol)
                    self.mana['generic'] = generic
                except ValueError:
                    if symbol == 'X':
                        self.mana['X'] = True
                    elif symbol in allowed_symbols:
                        self.mana[symbol] = self.mana.get(symbol, 0) + 1
                    else:
                        print("Unknown mana symbol: %s" % (symbol))
                        raise
        else:
            # warning does not handle hybrid/phyrexian use fromString!!!
            # does it handle wingding?
            self.mana['generic'] = int(gen)
            self.mana['C'] = int(C)
            self.mana['B'] = int(B)
            self.mana['G'] = int(G)
            self.mana['R'] = int(R)
            self.mana['U'] = int(U)
            self.mana['W'] = int(W)
            self.mana['X'] = X

        for value in land_mana.values():
            if value not in self.mana.keys():
                self.mana[value] = 0

    def add_costs(self,additional_costs):
        for cost in additional_costs:
            self.mana['generic'] += cost.mana['generic']
            self.mana['C'] += cost.mana['C']
            self.mana['B'] += cost.mana['B']
            self.mana['G'] += cost.mana['G']
            self.mana['R'] += cost.mana['R']
            self.mana['U'] += cost.mana['U']
            self.mana['W'] += cost.mana['W']
            self.mana['X'] = self.mana['X'] or cost.mana['X']
        return self

class Context(object):
    def __init__(self, battlefield, mana_pool):
        self.available_mana = {}
        self.battlefield = battlefield
        #mana_pool is a list of characters that represent mana already in the mana pool
        #assume for now that player is only playing basic lands and no other mana sources
        if len(mana_pool) == 0:
            for permanent in battlefield:
                if permanent.is_land() and not permanent.tapped:
                    if land_mana[permanent.name] in self.available_mana:
                        self.available_mana[land_mana[permanent.name]] += 1
                    else:
                        self.available_mana[land_mana[permanent.name]] = 1
        else:
            print "floating mana is currently not implemented"
        # need to initialize all basic colors
        for value in land_mana.values():
            if value not in self.available_mana.keys():
                self.available_mana[value] = 0

    def can_pay(self, cost):
        if 'generic' in cost.mana.keys():
            total_mana_needed = cost.mana['generic']
        else:
            total_mana_needed = 0
        if 'B' in cost.mana.keys():
            if cost.mana['B'] > self.available_mana['B']:
                return False
            else:
                total_mana_needed += cost.mana['B']
        if 'U' in cost.mana.keys():
            if cost.mana['U'] > self.available_mana['U']:
                return False
            else:
                total_mana_needed += cost.mana['U']
        if 'C' in cost.mana.keys():
            if cost.mana['C'] > self.available_mana['C']:
                return False
            else:
                total_mana_needed += cost.mana['C']
        if 'G' in cost.mana.keys():
            if cost.mana['G'] > self.available_mana['G']:
                return False
            else:
                total_mana_needed += cost.mana['G']
        if 'R' in cost.mana.keys():
            if cost.mana['R'] > self.available_mana['R']:
                return False
            else:
                total_mana_needed += cost.mana['R']
        if 'W' in cost.mana.keys():
            if cost.mana['W'] > self.available_mana['W']:
                return False
            else:
                total_mana_needed += cost.mana['W']
        if (self.available_mana['B'] + self.available_mana['U'] + self.available_mana['C'] + self.available_mana['G'] + self.available_mana['R'] + self.available_mana['W']) < total_mana_needed:
            return False
        else:
            return True

    def pay(self, cost):
        track_mana = {}
        #first pass get tap all the colored mana
        for permanent in self.battlefield:
            if permanent.is_land() and not permanent.tapped:
                if land_mana[permanent.name] in cost.mana:
                    if land_mana[permanent.name] in track_mana:
                        if track_mana[land_mana[permanent.name]] < cost.mana[land_mana[permanent.name]]:
                            track_mana[land_mana[permanent.name]] += 1
                            permanent.tapped = True
                    else:
                        track_mana[land_mana[permanent.name]] = 1
                        permanent.tapped = True
        if 'generic' not in cost.mana:
            return True
        #second pass tap random mana equal to generic mana
        random_taps = 0
        for permanent in self.battlefield:
            if permanent.is_land() and not permanent.tapped:
                permanent.tapped = True
                random_taps += 1
                if random_taps == cost.mana['generic']:
                    return True

class Card(object):

    def __init__(self, name='', cost='', spells=[], card_data={}):
        if card_data:
            self.name = card_data['name']
            self.mana_cost = Cost(fromString=card_data.get('manaCost', ''))
            self.card_data = card_data

            self.keywords = set()
            self.spells = []
            self.targets = []
            self._parse_text()
            self.loyalty = card_data.get('loyalty', None)
        else:
            self.name = name
            self.mana_cost = Cost(fromString=cost)
            self.spells = spells  # array of functions
        self.zone = 'library'
        self.untaps_normally = True
        self.summoning_sick = False
        self.tapped = None

    def _parse_text(self):
        ''' parse text or originalText for important abilities'''
        text = self.card_data.get("text", "")
        if not text:
            # note basic lands
            text = self.card_data.get("originalText", "")

        # find if cipt
        self.cipt = False
        if text.find('enters the battlefield tapped') >= 0:
            self.cipt = True

        # find key_words and mana abilities
        for line in text.split("\n"):
            templated = False
            for template in templates.keys():
                tokens = templates[template].search(line)
                if tokens:
                    templated = True
                    if template == 'mana_ability':
                        if len(tokens.group()) == 2:
                            # basic land?
                            pass
                        elif len(tokens.group()) == 3:
                            # single type
                            pass
                        elif len(tokens.group()) >= 4:
                            # multi type
                            pass
            if templated:
                break
            if self.is_creature:
                for x in kwre:
                    found = re.findall(x, text)
                    if found:
                        self.keywords.add(found[0].lower())
                # self.keywords = [re.findall(x, text) for x in kwre]
            elif re.search(r'flash(?i)', text):
                # this seems like it would fail on "other ~ you control have flash"
                self.keywords = {'flash'}
        # find mana abilities

    def is_land(self):
        return 'Land' in self.card_data['types']

    def is_permanent(self):
        return bool([ty for ty in self.card_data['types'] if ty in permanents])

    def is_creature(self):
        return 'Creature' in self.card_data['types']

    def is_enchantment(self):
        return 'Enchantment' in self.card_data['types']

    def is_planeswalker(self):
        return 'Planeswalker' in self.card_data['types']

    def is_artifact(self):
        return 'Artifact' in self.card_data['types']

    def is_instant(self):
        return 'Instant' in self.card_data['types']

    def is_sorcery(self):
        return 'Sorcery' in self.card_data['types']

    def is_legendary(self):
        return 'Legendary' in self.card_data['supertypes']

    def is_instant_speed(self):
        return self.is_instant() or 'flash' in self.keywords

    def is_mana_source(self):
        return [land_mana[ty] for ty in land_mana.keys() if ty in self.name]

    def draw(self):
        self.zone = 'hand'  # this is probably not correct

    def destroy(self):
        self.zone = 'graveyard'

    def exile(self):
        self.zone = 'exile'

    def tap(self):
        if not self.tapped:
            self.tapped = True

    def untap(self):
        if self.tapped:
            self.tapped = False

    def cmc(self):
        return self.card_data.get('cmc', 0)

    def pay_cost(self, context):

        print("Cost: {} of {}".format(self.mana_cost, self))

        if context.can_pay(self.mana_cost):
            print("Paying Costs")
            context.pay(self.mana_cost)
        else:
            print("{} unable to pay".format(context))

    def play(self, context):

        if context is None:
            self.zone = 'battlefield'
            self.tapped = False
            if self.cipt:
                self.tapped = True
        else:
            self.pay_cost(context)  # need some sort of game context object
            self.zone = 'battlefield'
            self.tapped = False
            if self.cipt:
                self.tapped = True


    def __repr__(self):
        return "[ %s (%s) ]" % (self.name, self.card_data.get('manaCost', '0'))

    def __str__(self):
        return self.__repr__()
