"""
This module contains the Player classes including the base Player class
and its derived classes (HumanPlayer, AIPlayer, OnlinePlayer).
"""

import random
from typing import List, Dict, Any, Optional, Union
from pokemon import Pokemon

class Player:
    """
    Base Player class for Pokémon battles.
    
    Attributes:
        name (str): The player's name
        team (List[Pokemon]): The player's team of Pokémon
        active_pokemon_index (int): Index of the currently active Pokémon
        potions (int): Number of potions the player has
    """
    
    def __init__(self, name: str):
        """
        Initialize a new Player.
        
        Args:
            name: The player's name
        """
        self.name = name
        self.team = []
        self.active_pokemon_index = 0
        self.potions = 3  # Start with 3 potions
    
    @property
    def active_pokemon(self) -> Optional[Pokemon]:
        """Get the currently active Pokémon."""
        if not self.team or self.active_pokemon_index >= len(self.team):
            return None
        return self.team[self.active_pokemon_index]
    
    def add_pokemon(self, pokemon: Pokemon) -> None:
        """
        Add a Pokémon to the team.
        
        Args:
            pokemon: The Pokémon to add
        """
        if len(self.team) < 6:  # Max 6 Pokémon
            self.team.append(pokemon)
        else:
            raise ValueError("Team already has 6 Pokémon")
    
    def switch_pokemon(self, index: int) -> bool:
        """
        Switch to a different Pokémon.
        
        Args:
            index: The index of the Pokémon to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.team) and not self.team[index].is_fainted():
            self.active_pokemon_index = index
            return True
        return False
    
    def use_potion(self, pokemon_index: int) -> bool:
        """
        Use a potion on a Pokémon.
        
        Args:
            pokemon_index: The index of the Pokémon to heal
            
        Returns:
            True if successful, False otherwise
        """
        if self.potions <= 0:
            return False
            
        if 0 <= pokemon_index < len(self.team) and not self.team[pokemon_index].is_fainted():
            pokemon = self.team[pokemon_index]
            if pokemon.current_hp < pokemon.max_hp:
                heal_amount = min(20, pokemon.max_hp - pokemon.current_hp)
                pokemon.heal(heal_amount)
                self.potions -= 1
                return True
        return False
    
    def has_usable_pokemon(self) -> bool:
        """
        Check if the player has any non-fainted Pokémon.
        
        Returns:
            True if at least one Pokémon is not fainted, False otherwise
        """
        return any(not pokemon.is_fainted() for pokemon in self.team)
    
    def choose_action(self, battle) -> Dict[str, Any]:
        """
        Choose an action in battle.
        
        Args:
            battle: The current Battle object
            
        Returns:
            A dictionary representing the action
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def choose_switch(self) -> Dict[str, Any]:
        """
        Choose a Pokémon to switch to.
        
        Returns:
            A dictionary representing the switch action
        """
        raise NotImplementedError("Subclasses must implement this method")


class HumanPlayer(Player):
    """Human-controlled player."""
    
    def choose_action(self, battle) -> Dict[str, Any]:
        """
        Let the human player choose an action in battle.
        
        Args:
            battle: The current Battle object
            
        Returns:
            A dictionary representing the action
        """
        if not self.active_pokemon:
            return {"type": "pass"}
            
        print(f"\n{self.name}'s turn:")
        print("1. Fight")
        print("2. Switch Pokémon")
        print("3. Use Potion")
        
        while True:
            choice = input("Choose an action (1-3): ")
            
            if choice == "1":
                # Choose a move
                print("\nChoose a move:")
                for i, move in enumerate(self.active_pokemon.moves):
                    print(f"{i+1}. {move}")
                
                while True:
                    move_choice = input(f"Choose a move (1-{len(self.active_pokemon.moves)}): ")
                    try:
                        move_index = int(move_choice) - 1
                        if 0 <= move_index < len(self.active_pokemon.moves):
                            return {"type": "move", "move": self.active_pokemon.moves[move_index]}
                        else:
                            print("Invalid move choice.")
                    except ValueError:
                        print("Please enter a number.")
            
            elif choice == "2":
                return {"type": "switch", "pokemon_index": self._choose_pokemon_to_switch()}
            
            elif choice == "3":
                if self.potions <= 0:
                    print("You don't have any potions left!")
                    continue
                    
                return {"type": "item", "item": "potion", "target_index": self._choose_pokemon_for_potion()}
            
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def choose_switch(self) -> Dict[str, Any]:
        """
        Let the human player choose a Pokémon to switch to.
        
        Returns:
            A dictionary representing the switch action
        """
        return {"type": "switch", "pokemon_index": self._choose_pokemon_to_switch()}
    
    def _choose_pokemon_to_switch(self) -> int:
        """
        Helper method to let the player choose a Pokémon to switch to.
        
        Returns:
            The index of the chosen Pokémon
        """
        print("\nChoose a Pokémon to switch to:")
        for i, pokemon in enumerate(self.team):
            if not pokemon.is_fainted() and i != self.active_pokemon_index:
                status = f"[{pokemon.status[:3].upper()}]" if pokemon.status else ""
                print(f"{i+1}. {pokemon.nickname} (HP: {pokemon.current_hp}/{pokemon.max_hp}) {status}")
        
        while True:
            try:
                choice = int(input("Enter your choice: "))
                index = choice - 1
                
                if 0 <= index < len(self.team) and not self.team[index].is_fainted() and index != self.active_pokemon_index:
                    return index
                else:
                    print("Invalid choice. Please select a non-fainted Pokémon that isn't already active.")
            except ValueError:
                print("Please enter a number.")
    
    def _choose_pokemon_for_potion(self) -> int:
        """
        Helper method to let the player choose a Pokémon to use a potion on.
        
        Returns:
            The index of the chosen Pokémon
        """
        print("\nChoose a Pokémon to use a potion on:")
        valid_targets = []
        
        for i, pokemon in enumerate(self.team):
            if not pokemon.is_fainted() and pokemon.current_hp < pokemon.max_hp:
                valid_targets.append(i)
                print(f"{i+1}. {pokemon.nickname} (HP: {pokemon.current_hp}/{pokemon.max_hp})")
        
        if not valid_targets:
            print("No Pokémon need healing!")
            return -1
        
        while True:
            try:
                choice = int(input("Enter your choice: "))
                index = choice - 1
                
                if index in valid_targets:
                    return index
                else:
                    print("Invalid choice. Please select a Pokémon that needs healing.")
            except ValueError:
                print("Please enter a number.")


class AIPlayer(Player):
    """AI-controlled player."""
    
    def __init__(self, name: str, difficulty: str = "medium"):
        """
        Initialize a new AI player.
        
        Args:
            name: The AI player's name
            difficulty: The AI difficulty level ("easy", "medium", or "hard")
        """
        super().__init__(name)
        self.difficulty = difficulty.lower()
    
    def choose_action(self, battle) -> Dict[str, Any]:
        """
        Let the AI choose an action in battle.
        
        Args:
            battle: The current Battle object
            
        Returns:
            A dictionary representing the action
        """
        if not self.active_pokemon:
            return {"type": "pass"}
            
        # Get the opponent's active Pokémon
        opponent = battle.player1 if battle.player2 == self else battle.player1
        opponent_pokemon = opponent.active_pokemon
        
        if not opponent_pokemon:
            return {"type": "pass"}
            
        # Decision making based on difficulty
        if self.difficulty == "easy":
            return self._choose_action_easy(opponent_pokemon)
        elif self.difficulty == "hard":
            return self._choose_action_hard(battle, opponent, opponent_pokemon)
        else:  # medium
            return self._choose_action_medium(opponent_pokemon)
    
    def _choose_action_easy(self, opponent_pokemon) -> Dict[str, Any]:
        """
        Easy AI decision making - mostly random choices.
        
        Args:
            opponent_pokemon: The opponent's active Pokémon
            
        Returns:
            A dictionary representing the action
        """
        # 80% chance to use a move, 15% to switch, 5% to use potion
        action_roll = random.random()
        
        if action_roll < 0.8:
            # Choose a random move
            move = random.choice(self.active_pokemon.moves)
            return {"type": "move", "move": move}
        elif action_roll < 0.95 and self._can_switch():
            # Choose a random Pokémon to switch to
            available_indices = [i for i in range(len(self.team)) 
                                if i != self.active_pokemon_index and not self.team[i].is_fainted()]
            if available_indices:
                return {"type": "switch", "pokemon_index": random.choice(available_indices)}
        elif self.potions > 0 and self._can_use_potion():
            # Choose a random Pokémon to use a potion on
            available_indices = [i for i in range(len(self.team)) 
                               if not self.team[i].is_fainted() and self.team[i].current_hp < self.team[i].max_hp]
            if available_indices:
                return {"type": "item", "item": "potion", "target_index": random.choice(available_indices)}
        
        # Default to using a random move
        move = random.choice(self.active_pokemon.moves)
        return {"type": "move", "move": move}
    
    def _choose_action_medium(self, opponent_pokemon) -> Dict[str, Any]:
        """
        Medium AI decision making - somewhat strategic choices.
        
        Args:
            opponent_pokemon: The opponent's active Pokémon
            
        Returns:
            A dictionary representing the action
        """
        # If HP is low (< 25%), consider switching or using a potion
        hp_percent = (self.active_pokemon.current_hp / self.active_pokemon.max_hp) * 100
        
        if hp_percent < 25:
            # 50% chance to switch or use a potion if available
            if random.random() < 0.5:
                if self.potions > 0 and self._can_use_potion():
                    return {"type": "item", "item": "potion", "target_index": self.active_pokemon_index}
                elif self._can_switch():
                    # Find a good Pokémon to switch to
                    best_index = self._find_best_switch(opponent_pokemon)
                    if best_index >= 0:
                        return {"type": "switch", "pokemon_index": best_index}
        
        # Otherwise, try to choose an effective move
        best_move = self._find_best_move(opponent_pokemon)
        return {"type": "move", "move": best_move}
    
    def _choose_action_hard(self, battle, opponent, opponent_pokemon) -> Dict[str, Any]:
        """
        Hard AI decision making - strategic and tactical choices.
        
        Args:
            battle: The current Battle object
            opponent: The opponent player
            opponent_pokemon: The opponent's active Pokémon
            
        Returns:
            A dictionary representing the action
        """
        # Calculate current Pokémon's effectiveness
        effectiveness_score = self._calculate_effectiveness_score(self.active_pokemon, opponent_pokemon)
        hp_percent = (self.active_pokemon.current_hp / self.active_pokemon.max_hp) * 100
        
        # Consider switching if current Pokémon is at a disadvantage or low on HP
        if effectiveness_score < 0.7 or (hp_percent < 30 and self._can_switch()):
            best_index = self._find_best_switch(opponent_pokemon)
            if best_index >= 0:
                return {"type": "switch", "pokemon_index": best_index}
        
        # Consider using a potion if HP is low but still worth saving
        if 15 <= hp_percent <= 40 and self.potions > 0:
            if effectiveness_score > 0.8 or not self._can_switch():
                return {"type": "item", "item": "potion", "target_index": self.active_pokemon_index}
        
        # Otherwise, choose the best move
        best_move = self._find_best_move(opponent_pokemon)
        return {"type": "move", "move": best_move}
    
    def _find_best_move(self, opponent_pokemon) -> str:
        """
        Find the most effective move against the opponent.
        
        Args:
            opponent_pokemon: The opponent's active Pokémon
            
        Returns:
            The name of the best move to use
        """
        from data import MOVE_DATA, TYPE_CHART
        
        best_move = self.active_pokemon.moves[0]
        best_score = 0
        
        for move_name in self.active_pokemon.moves:
            move = MOVE_DATA.get(move_name, {})
            move_type = move.get("type", "Normal")
            power = move.get("power", 0)
            accuracy = move.get("accuracy", 100) / 100
            
            # Skip moves with 0 power (usually status moves) except sometimes for hard AI
            if power == 0 and (self.difficulty != "hard" or random.random() < 0.7):
                continue
            
            # Calculate effectiveness
            effectiveness = 1.0
            for opponent_type in opponent_pokemon.types:
                type_effectiveness = TYPE_CHART.get(move_type, {}).get(opponent_type, 1.0)
                effectiveness *= type_effectiveness
            
            # STAB bonus (Same Type Attack Bonus)
            stab = 1.5 if move_type in self.active_pokemon.types else 1.0
            
            # Calculate move score
            if power > 0:
                score = power * effectiveness * stab * accuracy
            else:
                # For status moves, give them a base score
                score = 30 * effectiveness * accuracy
                
                # Consider the move's effects
                effect = move.get("effect", {})
                if "stat_boost" in effect or "stat_boost_chance" in effect:
                    score += 20
                elif "heal" in effect:
                    score += 15 * (1 - (self.active_pokemon.current_hp / self.active_pokemon.max_hp))
                elif "status" in effect:
                    score += 25 if not opponent_pokemon.status else 5
            
            # Adjust score based on difficulty
            if self.difficulty == "easy":
                # Add randomness for easy AI
                score *= random.uniform(0.5, 1.5)
            
            if score > best_score:
                best_score = score
                best_move = move_name
        
        return best_move
    
    def _find_best_switch(self, opponent_pokemon) -> int:
        """
        Find the best Pokémon to switch to based on type effectiveness.
        
        Args:
            opponent_pokemon: The opponent's active Pokémon
            
        Returns:
            The index of the best Pokémon to switch to, or -1 if none found
        """
        best_index = -1
        best_score = 0
        
        for i, pokemon in enumerate(self.team):
            if i == self.active_pokemon_index or pokemon.is_fainted():
                continue
                
            # Calculate a score based on type effectiveness and HP
            score = self._calculate_effectiveness_score(pokemon, opponent_pokemon)
            hp_factor = pokemon.current_hp / pokemon.max_hp
            
            # Adjust score based on HP percentage
            score *= hp_factor
            
            # Adjust score based on difficulty
            if self.difficulty == "easy":
                # Add randomness for easy AI
                score *= random.uniform(0.5, 1.5)
            
            if score > best_score:
                best_score = score
                best_index = i
        
        return best_index
    
    def _calculate_effectiveness_score(self, attacker, defender) -> float:
        """
        Calculate a score representing type effectiveness between two Pokémon.
        
        Args:
            attacker: The attacking Pokémon
            defender: The defending Pokémon
            
        Returns:
            A score representing effectiveness (higher is better)
        """
        from data import MOVE_DATA, TYPE_CHART
        
        # Offensive score - how effective our attacks are against opponent
        offensive_score = 0
        for move_name in attacker.moves:
            move = MOVE_DATA.get(move_name, {})
            if move.get("power", 0) > 0:  # Only consider damaging moves
                move_type = move.get("type", "Normal")
                
                # Calculate effectiveness
                effectiveness = 1.0
                for defender_type in defender.types:
                    type_effectiveness = TYPE_CHART.get(move_type, {}).get(defender_type, 1.0)
                    effectiveness *= type_effectiveness
                
                # STAB bonus
                stab = 1.5 if move_type in attacker.types else 1.0
                
                move_score = move.get("power", 40) * effectiveness * stab
                offensive_score = max(offensive_score, move_score)
        
        # Defensive score - how resistant we are to opponent's types
        defensive_score = 0
        for defender_type in defender.types:
            resistance = 1.0
            for attacker_type in attacker.types:
                type_resistance = 1.0 / TYPE_CHART.get(defender_type, {}).get(attacker_type, 1.0)
                resistance *= type_resistance
            defensive_score += resistance
        
        # Normalize defensive score
        defensive_score /= len(defender.types)
        
        # Combined score with more weight on offensive capability
        return (offensive_score * 0.7 + defensive_score * 100 * 0.3) / 100
    
    def _can_switch(self) -> bool:
        """
        Check if the AI can switch Pokémon.
        
        Returns:
            True if the AI has other non-fainted Pokémon to switch to, False otherwise
        """
        return any(i != self.active_pokemon_index and not pokemon.is_fainted() 
                   for i, pokemon in enumerate(self.team))
    
    def _can_use_potion(self) -> bool:
        """
        Check if the AI can use a potion.
        
        Returns:
            True if the AI has potions and Pokémon that need healing, False otherwise
        """
        if self.potions <= 0:
            return False
            
        return any(not pokemon.is_fainted() and pokemon.current_hp < pokemon.max_hp 
                   for pokemon in self.team)
    
    def choose_switch(self) -> Dict[str, Any]:
        """
        Let the AI choose a Pokémon to switch to.
        
        Returns:
            A dictionary representing the switch action
        """
        available_indices = [i for i in range(len(self.team)) 
                           if i != self.active_pokemon_index and not self.team[i].is_fainted()]
        
        if not available_indices:
            return {"type": "pass"}
            
        # Sort by HP percentage for medium and hard difficulties
        if self.difficulty != "easy":
            available_indices.sort(
                key=lambda i: self.team[i].current_hp / self.team[i].max_hp,
                reverse=True
            )
            
        return {"type": "switch", "pokemon_index": available_indices[0]}


class OnlinePlayer(Player):
    """Player connected through the network."""
    
    def __init__(self, name: str, socket, server):
        """
        Initialize a new online player.
        
        Args:
            name: The player's name
            socket: The player's network socket
            server: Reference to the server managing the connection
        """
        super().__init__(name)
        self.socket = socket
        self.server = server
    
    def choose_action(self, battle) -> Dict[str, Any]:
        """
        Get action from the client over the network.
        
        Args:
            battle: The current Battle object
            
        Returns:
            A dictionary representing the action
        """
        # This is handled directly in PokemonServer.run_battle()
        # The server manages sending state and receiving actions
        return {"type": "pass"}
    
    def choose_switch(self) -> Dict[str, Any]:
        """
        Get switch choice from the client over the network.
        
        Returns:
            A dictionary representing the switch action
        """
        # This is also handled by the server
        return {"type": "pass"}
