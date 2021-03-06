"""The adversary module ... """
from casper.safety_oracles.adversary_models.model_validator import (
    ModelValidator
)


class Adversary(object):
    """Simulates a lower bound, side-effects free adversary."""

    def __init__(self, victim_estimate, latest_bets, viewables, validator_set):

        # Estimate being attacked.
        self.victim_estimate = victim_estimate

        # Estimate adversary is attack towards.
        self.target_estimate = 1 - victim_estimate

        # The attacker adds the bets they created in the attack to this view.
        self.attack_view = set()

        self.validator_set = validator_set

        self.validator_models = dict()
        for validator in validator_set:
            self.validator_models[validator] = ModelValidator(
                validator,
                latest_bets[validator],
                viewables[validator],
                self.target_estimate
            )

        self.voting_against_attacker = set()
        self.voting_with_attacker = set()
        for validator in validator_set:
            success, new_bet = self.validator_models[validator].make_new_latest_bet()

            if success:
                # Sanity check!
                assert new_bet.estimate == self.target_estimate
                self.voting_with_attacker.add(validator)
            else:
                self.voting_against_attacker.add(validator)

        # The attacker tracks the weights of the victim and target estimates:
        self.weight_of_victim_estimate = sum(
            validator.weight
            for validator in self.voting_against_attacker
        )
        self.weight_of_target_estimate = sum(
            validator.weight
            for validator in self.voting_with_attacker
        )

        assert len(self.voting_with_attacker) + len(self.voting_against_attacker) == \
            len(validator_set)
        assert round(self.weight_of_victim_estimate + self.weight_of_target_estimate, 2) == \
            round(validator_set.weight(), 2)

        # The attacker produces a log of the bets added during the attack.
        self.operations_log = []

    def is_attack_complete(self):
        """Return true if the target has more weight than the victim estimate"""
        return self.weight_of_target_estimate > self.weight_of_victim_estimate

    def ideal_network_attack(self):
        """Implements an ideal network attack.

        Returns the triple (was_attack_successful, operation_log, attack_view)."""

        # As work is offloaded somewhat into the get_recent_messages_and_viewables,
        # the attack may be complete already.
        if self.is_attack_complete():
            return True, self.operations_log, self.attack_view

        # First, show all validators not yet on target_estimate
        # all bets that are on the target_estimate
        for validator in self.voting_with_attacker:
            on_target, bet = self.validator_models[validator].make_new_latest_bet()
            assert on_target and bet.estimate == self.target_estimate, 'in voting_with_attacker!'
            for val2 in self.voting_against_attacker:
                self.validator_models[val2].show(bet)

        # We'll continue the attack until we no longer make progress,
        # or until the attack is successful and the victim estimate dethroned.
        progress_made = True
        while progress_made:
            progress_made = False

            to_remove = set()

            for validator in self.voting_against_attacker:

                success, new_bet = self.validator_models[validator].make_new_latest_bet()
                # If this validator failed to make a bet on target_estimate, continue.
                if not success:
                    continue

                assert new_bet.estimate == self.target_estimate

                to_remove.add(validator)
                progress_made = True

                self.weight_of_victim_estimate -= validator.weight
                self.weight_of_target_estimate += validator.weight

                # Add a log of our operations.
                self.operations_log.append([
                    "added valid bet for a validator voting against the attacker",
                    hash(new_bet)
                ])
                # Update the attack view.
                self.attack_view.add(new_bet)

                # If attack is complete, stop attacking!
                if self.is_attack_complete():
                    return True, self.operations_log, self.attack_view

                # Show other validators this new bet on target_estimate.
                for val2 in self.voting_against_attacker.difference(to_remove):
                    self.validator_models[val2].show(new_bet)

            # We can remove the validators who are now voting on target_estimate.
            self.voting_against_attacker.difference_update(to_remove)

            # Sanity check!
            assert not self.is_attack_complete(), "expected attack to be ongoing, at this point"

        return False, self.operations_log, self.attack_view
