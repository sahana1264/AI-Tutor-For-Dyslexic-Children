import random

class RLManager:
    def __init__(self, alpha=0.5, gamma=0.9, epsilon=0.2):
        # Learning rate, discount, exploration
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        # Q-table
        self.Q = {
            "low": {"easy": 0, "medium": 0, "hard": 0},
            "medium": {"easy": 0, "medium": 0, "hard": 0},
            "high": {"easy": 0, "medium": 0, "hard": 0}
        }

        # Track last state/action for updates
        self.last_state = "medium"   # Start from medium as you wanted
        self.last_action = "medium"

    def get_state(self, spelling_errors, reversal_errors):
        total = spelling_errors + reversal_errors
        if total <= 3:
            return "low"
        elif total <= 6:
            return "medium"
        else:
            return "high"

    def reward_function(self, spelling_errors, reversal_errors):
        total = spelling_errors + reversal_errors
        if total == 0:
            return +5   # did great
        elif total <= 2:
            return +2   # okay
        else:
            return -3   # struggled

    def decide_level(self):
        # ε-greedy: sometimes explore
        if random.random() < self.epsilon:
            return random.choice(["easy", "medium", "hard"])
        else:
            # Exploit: pick best Q-value
            q_values = self.Q[self.last_state]
            return max(q_values, key=q_values.get)

    def update(self, spelling_errors, reversal_errors):
        # Get new state + reward
        new_state = self.get_state(spelling_errors, reversal_errors)
        reward = self.reward_function(spelling_errors, reversal_errors)

        # Q-learning update
        old_value = self.Q[self.last_state][self.last_action]
        future_max = max(self.Q[new_state].values())
        self.Q[self.last_state][self.last_action] = old_value + self.alpha * (
            reward + self.gamma * future_max - old_value
        )

        # Update state/action for next round
        self.last_state = new_state
        self.last_action = self.decide_level()

    def get_current_level(self):
        return self.last_action
    def set_current_level(self, level):
        self.current_level = level