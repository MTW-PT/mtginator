import sys
sys.path.insert(0,'/src/mtginator/')
import random
import cards

class Game(object):
    ''' Object that represents the game/board state of a given game '''

    def __init__(self, players, maxturns=None):
        self.turn = 0
        self.players = players
        if maxturns:
            self.maxturns = maxturns
        for player in self.players:
            player.game = self

    def play_or_draw(self):
        players = self.players
        return random.shuffle(players)

    def is_over(self, turn=None, draw=(None, None)):
        ''' draw parameter is a tuple with player objects if player1 or 2 is drawing a card
            Returns a list with Losing Players or [] if game continues
        '''
        losers = set()
        if turn and turn > self.maxturns:
            return self.players
        for player in self.players:
            if (player.life <= 0) or (player.poison <= 0) or (len(player.deck.main) == 0 and player in draw):
                losers.update(player)

        return list(losers)

    def __repr__(self):
        return "Magic Game State: Turn {} {}".format(self.turn,self.players)

    def __str__(self):
        return self.__repr__()

class Mana(object):
    ''' Object that represents mana-producing board state of a player '''
    def __init__(self, board, extras=[]):
        self.available_mana = []
        #extras is a list of characters that represent mana already in the mana pool
        #assume for now that player is only playing basic lands and no other mana sources
        if len(extras) == 0:
            self.available_mana[:] = []
            for permanent in board:
                if permanent.is_land() and not permanent.tapped:
                    self.available_mana.append(cards.land_mana[permanent.name])
            print self.available_mana




            
class Player(object):
    ''' Object that represents a player of the game'''

    def __init__(self, name='Default1', deck=None, life=20, poison=10):
        self.name = name
        self.deck = deck
        self.life = life
        self.poison = poison
        self.hand = []
        self.graveyard = []
        self.exile = []
        self.max_handsize = 7  # theoretically this can change by game actions.
        self.game = None  # pointer to the Game object

        self.battlefield = []

    def _satisfied(self, rules, n):
        if not rules:
            if len(self.hand) and len(self.hand) < 5:
                # keep all 4s
                return True
            elif len([c for c in self.hand if c.is_land()]) and len([c for c in self.hand if not c.is_land()]):
                    # literally "lands and spells"
                    return True
            else:
                return False

    def take_turn(self):
        self.untap()
        self.upkeep()
        self.draw()
        self.main()
        self.cleanup()

    def untap(self):
        for permanent in self.battlefield:
            permanent.untap()

    def upkeep(self):
        pass

    def draw(self):
        if self.game.is_over(draw=self):
            return
        self.hand += [self.deck.draw_card()]

    def main(self):
        self.land_drop()
        plays = self.enumerate_plays()
        self.make_play(plays)

    def land_drop(self):
        lands = [c for c in self.hand if c.is_land()]
        if len(lands) > 0:
            pick = random.choice(lands)
            # Note: should implment some color optimization
            pick.play(None) #lands don't need context to play
            self.battlefield.append(pick)
            self.hand.remove(pick)
            print("Played {} as Land for turn [ hand size: {} ]".format(pick, len(self.hand)))

    def cleanup(self):
        while(len(self.hand) > self.max_handsize):
            self.choose_discard()

    def choose_discard(self):
        discard = self.hand.pop(random.randrange(len(self.hand)))
        self.graveyard.append(discard)

        print("Dicarding {}".format(discard))

    def make_play(self, possible_plays):
        if possible_plays:
            card_to_play = random.choice(possible_plays)
            card_to_play.play(cards.Context(self.battlefield, []))
            self.hand.remove(card_to_play)
            if card_to_play.is_permanent():
                self.battlefield.append(card_to_play)
            else:
                self.graveyard.append(card_to_play)
            print("Playing {}".format(card_to_play))

    def available_mana(self):
        return Mana(self.battlefield)
        ''' return mana object based on board state '''

    def reset(self):
        self.deck.main = self.deck.main + self.hand + self.graveyard + self.exile + self.battlefield
        self.hand = self.graveyard = self.exile = self.battlefield = []
        self.deck.shuffle()
        assert(len(self.deck.main) == self.deck.total_cards)

    def mulligan(self, rules=None, n=7, verbose=True):
        ''' draw an initial hand and paris mulligan until acceptable by rules
            default rules are mulligan 0 land and 0 non-land hands until 4, then keep '''

        self.deck.main += self.hand
        self.deck.shuffle()
        self.hand = []
        if verbose:
            if n == 7:
                print("Drawing initial 7...")
            else:
                print("Mulling to {}...".format(n))
        for i in range(0, n):
            self.hand.append(self.deck.draw_card())

        while(not self._satisfied(rules, n)):
            self.mulligan(rules, n-1, verbose=verbose)

        if verbose:
            print("Final hand %s" % ([str(c) for c in self.hand]))

    def enumerate_plays(self):
        ''' For a given hand (or metahand) and available mana, what plays are available to Player
             Returns:  List of Card objects
        '''
        list_of_plays = []
        if not self.hand:
            return list_of_plays

        context = cards.Context(self.battlefield,[])

        for card in self.hand:
            if not card.is_land():
                if context.can_pay(card.mana_cost):
                    list_of_plays.append(card)

        return list_of_plays

    def __repr__(self):
        return("Name: {} Deck {} Life {} Poison {} #Cards-in-Hand {} WP% {}".format(self.name,
                                                                                    self.deck.name,
                                                                                    self.life,
                                                                                    self.poison,
                                                                                    len(self.hand), 0.5))

