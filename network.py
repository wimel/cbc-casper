import random as r  # to ensure the tie-breaking property

from settings import VALIDATOR_NAMES
from view import View
from validator import Validator
from block import Block
import plot_tool


class Network:
    def __init__(self):
        self.validators = dict()
        for v in VALIDATOR_NAMES:
            self.validators[v] = Validator(v)
        self.global_view = View()

    def propagate_message_to_validator(self, message, validator_name):
        assert message in self.global_view.messages, "...expected only to propagate messages from the global view"
        self.validators[validator_name].receive_messages(set([message]))

    def get_message_from_validator(self, validator_name):
        assert validator_name in VALIDATOR_NAMES, "...expected a known validator"

        if self.validators[validator_name].decided:
            return True

        new_message = self.validators[validator_name].make_new_message()
        return new_message

    # def let_validator_push

    def view_initialization(self, view):
        assert isinstance(view, View)
        self.global_view = view.messages

        latest = view.latest_messages

        for v in latest:
            self.validators[v].receive_messages(set([latest[v]]))

    def random_initialization(self):
        for v in VALIDATOR_NAMES:
            new_bet = self.get_message_from_validator(v)
            self.global_view.add_messages(set([new_bet]))

    def report(self, colored_messages=set(), edges=[], thick_edges=[], colored_edges=[]):
        plot_tool.plot_view(self.global_view, coloured_bets=colored_messages, use_edges=edges, thick_edges=thick_edges, colored_edges=colored_edges)
