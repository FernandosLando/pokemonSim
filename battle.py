"""
This module contains the Battle class that manages the Pokémon battle mechanics.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from pokemon import Pokemon
from player import Player
from data import MOVE_DATA, TYPE_CHART

class Battle:
    """
    Class managing a Pokémon battle between two players.
    
    Attributes:
        player1 (Player): The first player
        player2 (Player): The second player
        current_turn (int): Current turn number
        is_battle_over (bool): Whether the battle has ended
        winner (Optional[Player]): The winning player, if any
        battle_log (List[str]): A log of battle events
    """
    
    def __init__(self, player1: Player, player2: Player):
        """
        Initialize a new battle.
        
        Args:
            player1: The first player
            player2: The second player
        """
        self.player1 = player1
        self.player2 = player2
        self.current_turn = 0
        self.is_battle_over = False
        self.winner = None
        self.battle_log = []
    
    def execute_turn(self, player1_action: Dict[str, Any], player2_action: Dict[str, Any]) -> List[str]:
        """
        Execute a turn of battle with the given player actions.
        
        Args:
            player1_action: The action for player 1
            player2_action: The action for player 2
            
        Returns:
            A list of log messages from the turn
        """
        self.current_turn += 1
        self.battle_log = []  # Clear log for new turn
        
        # Determine action order
        actions = self._determine_action_order(player1_action, player2_action)
        
        # Execute actions in order
        for player, action in actions:
            if self.is_battle_over:
                break
                
            self._execute_action(player, action)
            
            # Check for battle end after each action
            self._check_battle_end()
        
        # Apply end-of-turn effects
        if not self.is_battle_over:
            self._apply_end_of_turn_effects()
            self._check_battle_end()
        
        return self.battle_log
    
    def _determine_action_order(self, player1_action: Dict[str, Any], player2_action: Dict[str, Any]) -> List[Tuple[Player, Dict[str, Any]]]:
        """
        Determine the order in which actions should be executed.
        
        Args:
            player1_action: The action for player 1
            player2_action: The action for player 2
            
        Returns:
            A list of (player, action) tuples in execution order
        """
        actions = []
        
        # Handle empty actions
        if player1_action.get("type") == "pass":
            actions.append((self.player2, player2_action))
            return actions
            
        if player2_action.get("type") == "pass":
            actions.append((self.player1, player1_action))
            return actions
            
        # Switching and items go before moves
        if player1_action.get("type") in ["switch", "item"] and player2_action.get("type") == "move":
            actions.append((self.player1, player1_action))
            actions.append((self.player2, player2_action))
            return actions
            
        if player2_action.get("type") in ["switch", "item"] and player1_action.get("type") == "move":
            actions.append((self.player2, player2_action))
            actions.append((self.player1, player1_action))
            return actions
            
        # If both players use the same action type, use speed to break the tie
        if player1_action.get("type") == player2_action.get("type"):
            if player1_action.get("type") == "move":
                # Check for priority moves
                p1_priority = MOVE_DATA.get(player1_action.get("move", ""), {}).get("effect", {}).get("priority", 0)
                p2_priority = MOVE_DATA.get(player2_action.get("move", ""), {}).get("effect", {}).get("priority", 0)
                
                if p1_priority != p2_priority:
                    if p1_priority > p2_priority:
                        actions.append((self.player1, player1_action))
                        actions.append((self.player2, player2_action))
                    else:
                        actions.append((self.player2, player2_action))
                        actions.append((self.player1, player1_action))
                    return actions
            
            # Speed tie-breaker
            p1_speed = self.player1.active_pokemon.get_modified_stat("speed") if self.player1.active_pokemon else 0
            p2_speed = self.player2.active_pokemon.get_modified_stat("speed") if self.player2.active_pokemon else 0
            
            if p1_speed > p2_speed:
                actions.append((self.player1, player1_action))
                actions.append((self.player2, player2_action))
            elif p2_speed > p1_speed:
                actions.append((self.player2, player2_action))
                actions.append((self.player1, player1_action))
            else:
                # Speed tie, randomize
                if random.random() < 0.5:
                    actions.append((self.player1, player1_action))
                    actions.append((self.player2, player2_action))
                else:
                    actions.append((self.player2, player2_action))
                    actions.append((self.player1, player1_action))
            return actions
            
        # Different action types and not covered by earlier rules
        actions.append((self.player1, player1_action))
        actions.append((self.player2, player2_action))
        return actions
    
    def _execute_action(self, player: Player, action: Dict[str, Any]) -> None:
        """
        Execute a single player's action.
        
        Args:
            player: The player performing the action
            action: The action to execute
        """
        action_type = action.get("type", "pass")
        
        if action_type == "move":
            self._execute_move(player, action.get("move", ""))
        elif action_type == "switch":
            self._execute_switch(player, action.get("pokemon_index", 0))
        elif action_type == "item":
            self._execute_item(player, action.get("item", ""), action.get("target_index", 0))
        # "pass" actions do nothing
    
    def _execute_move(self, player: Player, move_name: str) -> None:
        """
        Execute a move in battle.
        
        Args:
            player: The player using the move
            move_name: The name of the move to use
        """
        attacker = player.active_pokemon
        
        if not attacker or attacker.is_fainted():
            return
            
        # Get the opponent
        opponent = self.player2 if player == self.player1 else self.player1
        defender = opponent.active_pokemon
        
        if not defender or defender.is_fainted():
            return
            
        # Get move data
        move = MOVE_DATA.get(move_name, {})
        move_type = move.get("type", "Normal")
        
        # Check if move exists and attacker has it
        if not move or move_name not in attacker.moves:
            self.battle_log.append(f"{attacker.nickname} tried to use {move_name}, but it doesn't know that move!")
            return
            
        self.battle_log.append(f"{player.name}'s {attacker.nickname} used {move_name}!")
        
        # Status effects can prevent action
        if attacker.status == "paralyzed" and random.random() < 0.25:
            self.battle_log.append(f"{attacker.nickname} is paralyzed and couldn't move!")
            return
        elif attacker.status == "frozen" and random.random() < 0.8:
            self.battle_log.append(f"{attacker.nickname} is frozen solid!")
            return
        elif attacker.status == "asleep":
            self.battle_log.append(f"{attacker.nickname} is fast asleep!")
            return
            
        # Check accuracy
        accuracy = move.get("accuracy", 100)
        if accuracy < 100 and random.randint(1, 100) > accuracy:
            self.battle_log.append(f"{attacker.nickname}'s attack missed!")
            return
            
        # Handle different move categories
        category = move.get("category", "Physical")
        
        if category in ["Physical", "Special"]:
            # Calculate damage
            damage = self._calculate_damage(attacker, defender, move)
            
            # Apply damage
            actual_damage = defender.take_damage(damage)
            self.battle_log.append(f"{defender.nickname} took {actual_damage} damage!")
            
            # Check if defender fainted
            if defender.is_fainted():
                self.battle_log.append(f"{opponent.name}'s {defender.nickname} fainted!")
                
            # Handle move effects for damaging moves
            self._apply_move_effects(move, attacker, defender, player, opponent)
            
        elif category == "Status":
            # Handle status moves
            self._apply_move_effects(move, attacker, defender, player, opponent)
    
    def _calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Dict[str, Any]) -> int:
        """
        Calculate damage for a move.
        
        Args:
            attacker: The attacking Pokémon
            defender: The defending Pokémon
            move: The move data
            
        Returns:
            The calculated damage
        """
        # Get move power and category
        power = move.get("power", 0)
        category = move.get("category", "Physical")
        move_type = move.get("type", "Normal")
        
        if power == 0:
            return 0
            
        # Get relevant stats
        if category == "Physical":
            attack_stat = attacker.get_modified_stat("attack")
            defense_stat = defender.get_modified_stat("defense")
        else:  # Special
            attack_stat = attacker.get_modified_stat("sp_attack")
            defense_stat = defender.get_modified_stat("sp_defense")
            
        # Base damage formula
        damage = ((2 * attacker.level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2
        
        # STAB (Same Type Attack Bonus)
        if move_type in attacker.types:
            damage *= 1.5
            
        # Type effectiveness
        effectiveness = 1.0
        for defender_type in defender.types:
            type_effectiveness = TYPE_CHART.get(move_type, {}).get(defender_type, 1.0)
            effectiveness *= type_effectiveness
            
        damage *= effectiveness
        
        if effectiveness > 1.0:
            self.battle_log.append("It's super effective!")
        elif effectiveness < 1.0 and effectiveness > 0:
            self.battle_log.append("It's not very effective...")
        elif effectiveness == 0:
            self.battle_log.append(f"It doesn't affect {defender.nickname}...")
            
        # Random factor (85-100%)
        damage *= random.uniform(0.85, 1.0)
        
        # Critical hit (6.25% chance)
        if random.random() < 0.0625:
            damage *= 1.5
            self.battle_log.append("A critical hit!")
            
        return max(1, int(damage))
    
    def _apply_move_effects(self, move: Dict[str, Any], attacker: Pokemon, defender: Pokemon, 
                           attacker_player: Player, defender_player: Player) -> None:
        """
        Apply secondary effects of a move.
        
        Args:
            move: The move data
            attacker: The attacking Pokémon
            defender: The defending Pokémon
            attacker_player: The player using the move
            defender_player: The opponent
        """
        effect = move.get("effect", {})
        
        # Status infliction
        if "status" in effect:
            status = effect["status"]
            chance = effect.get("chance", 1.0)
            
            if random.random() < chance and defender.apply_status(status):
                self.battle_log.append(f"{defender.nickname} was {status}!")
                
        # Stat changes
        if "stat_boost" in effect:
            for stat, stages in effect["stat_boost"].items():
                if attacker.modify_stat_stage(stat, stages) != 0:
                    self.battle_log.append(f"{attacker.nickname}'s {stat} {'rose' if stages > 0 else 'fell'}!")
                    
        if "stat_drop" in effect:
            for stat, stages in effect["stat_drop"].items():
                if defender.modify_stat_stage(stat, -stages) != 0:
                    self.battle_log.append(f"{defender.nickname}'s {stat} fell!")
                    
        # Stat change chance effects
        if "stat_boost_chance" in effect:
            chance = effect.get("chance", 0.1)
            if random.random() < chance:
                for stat, stages in effect["stat_boost_chance"].items():
                    if attacker.modify_stat_stage(stat, stages) != 0:
                        self.battle_log.append(f"{attacker.nickname}'s {stat} rose!")
                        
        if "stat_drop_chance" in effect:
            chance = effect.get("chance", 0.1)
            if random.random() < chance:
                for stat, stages in effect["stat_drop_chance"].items():
                    if defender.modify_stat_stage(stat, -stages) != 0:
                        self.battle_log.append(f"{defender.nickname}'s {stat} fell!")
                        
        # Healing effects
        if "heal" in effect:
            heal_percent = effect["heal"]
            heal_amount = int(attacker.max_hp * heal_percent)
            actual_heal = attacker.heal(heal_amount)
            
            if actual_heal > 0:
                self.battle_log.append(f"{attacker.nickname} restored {actual_heal} HP!")
                
        # Drain effects
        if "drain" in effect and not defender.is_fainted():
            drain_percent = effect["drain"]
            damage_dealt = min(defender.max_hp - defender.current_hp, move.get("power", 0))
            heal_amount = int(damage_dealt * drain_percent)
            actual_heal = attacker.heal(heal_amount)
            
            if actual_heal > 0:
                self.battle_log.append(f"{attacker.nickname} restored {actual_heal} HP!")
                
        # Recoil damage
        if "recoil" in effect:
            recoil_percent = effect["recoil"]
            damage_dealt = min(defender.max_hp - defender.current_hp, move.get("power", 0))
            recoil_damage = int(damage_dealt * recoil_percent)
            
            if recoil_damage > 0:
                actual_recoil = attacker.take_damage(recoil_damage)
                self.battle_log.append(f"{attacker.nickname} was hurt by recoil! ({actual_recoil} damage)")
                
                if attacker.is_fainted():
                    self.battle_log.append(f"{attacker_player.name}'s {attacker.nickname} fainted due to recoil!")
    
    def _execute_switch(self, player: Player, pokemon_index: int) -> None:
        """
        Execute a switch action.
        
        Args:
            player: The player switching Pokémon
            pokemon_index: The index of the Pokémon to switch to
        """
        if player.switch_pokemon(pokemon_index):
            self.battle_log.append(f"{player.name} withdrew their Pokémon!")
            self.battle_log.append(f"{player.name} sent out {player.active_pokemon.nickname}!")
        else:
            self.battle_log.append(f"{player.name} tried to switch, but couldn't!")
    
    def _execute_item(self, player: Player, item: str, target_index: int) -> None:
        """
        Execute an item action.
        
        Args:
            player: The player using the item
            item: The item to use
            target_index: The index of the Pokémon to use the item on
        """
        if item == "potion":
            if player.use_potion(target_index):
                target_pokemon = player.team[target_index]
                self.battle_log.append(f"{player.name} used a Potion on {target_pokemon.nickname}!")
                self.battle_log.append(f"{target_pokemon.nickname} restored some HP!")
            else:
                self.battle_log.append(f"{player.name} tried to use a Potion, but couldn't!")
    
    def _apply_end_of_turn_effects(self) -> None:
        """Apply end-of-turn effects like burn damage, etc."""
        # Apply status effects for player 1
        if self.player1.active_pokemon and not self.player1.active_pokemon.is_fainted():
            pokemon = self.player1.active_pokemon
            self._apply_status_damage(pokemon, self.player1)
            
        # Apply status effects for player 2
        if self.player2.active_pokemon and not self.player2.active_pokemon.is_fainted():
            pokemon = self.player2.active_pokemon
            self._apply_status_damage(pokemon, self.player2)
    
    def _apply_status_damage(self, pokemon: Pokemon, player: Player) -> None:
        """
        Apply damage from status conditions.
        
        Args:
            pokemon: The Pokémon to apply status damage to
            player: The player who owns the Pokémon
        """
        if pokemon.status == "burned":
            damage = max(1, pokemon.max_hp // 16)
            actual_damage = pokemon.take_damage(damage)
            self.battle_log.append(f"{pokemon.nickname} was hurt by its burn! ({actual_damage} damage)")
            
            if pokemon.is_fainted():
                self.battle_log.append(f"{player.name}'s {pokemon.nickname} fainted!")
                
        elif pokemon.status == "poisoned":
            damage = max(1, pokemon.max_hp // 8)
            actual_damage = pokemon.take_damage(damage)
            self.battle_log.append(f"{pokemon.nickname} was hurt by poison! ({actual_damage} damage)")
            
            if pokemon.is_fainted():
                self.battle_log.append(f"{player.name}'s {pokemon.nickname} fainted!")
    
    def _check_battle_end(self) -> None:
        """Check if the battle is over and update the battle state accordingly."""
        # Check if player 1 has any usable Pokémon
        p1_has_usable = self.player1.has_usable_pokemon()
        
        # Check if player 2 has any usable Pokémon
        p2_has_usable = self.player2.has_usable_pokemon()
        
        # Determine winner
        if not p1_has_usable and not p2_has_usable:
            self.is_battle_over = True
            self.winner = None  # Draw
            self.battle_log.append("The battle ended in a draw!")
        elif not p1_has_usable:
            self.is_battle_over = True
            self.winner = self.player2
            self.battle_log.append(f"{self.player2.name} won the battle!")
        elif not p2_has_usable:
            self.is_battle_over = True
            self.winner = self.player1
            self.battle_log.append(f"{self.player1.name} won the battle!")
