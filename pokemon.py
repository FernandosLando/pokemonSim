"""
This module contains the Pokemon class that represents a single Pokémon with all its attributes.
"""

import random
from typing import List, Dict, Union, Tuple, Optional
from data import POKEMON_DATA, MOVE_DATA, TYPE_CHART

class Pokemon:
    """
    Class representing a Pokémon in battle.
    
    Attributes:
        id (int): The Pokémon's ID number
        name (str): The Pokémon's species name
        nickname (str): The Pokémon's nickname (defaults to species name)
        types (List[str]): The Pokémon's types (e.g., ["Fire", "Flying"])
        level (int): The Pokémon's level
        moves (List[str]): The Pokémon's moves (max 4)
        max_hp (int): Maximum HP calculated from base stats and level
        current_hp (int): Current HP in battle
        attack (int): Attack stat
        defense (int): Defense stat
        sp_attack (int): Special Attack stat
        sp_defense (int): Special Defense stat
        speed (int): Speed stat
        stat_stages (Dict[str, int]): Battle stat modifiers (-6 to +6)
        status (Optional[str]): Current status condition
    """
    
    def __init__(self, pokemon_id: int, level: int = 50, nickname: Optional[str] = None):
        """
        Initialize a new Pokémon.
        
        Args:
            pokemon_id: The ID of the Pokémon from the POKEMON_DATA
            level: The Pokémon's level (default: 50)
            nickname: An optional nickname (default: species name)
        
        Raises:
            ValueError: If the pokemon_id is not found in POKEMON_DATA
        """
        data = POKEMON_DATA.get(pokemon_id, None)
        if not data:
            raise ValueError(f"Pokemon with ID {pokemon_id} not found")
        
        self.id = pokemon_id
        self.name = data["name"]
        self.nickname = nickname or data["name"]
        self.types = data["types"]  # Fixed 'type' to 'types' to match POKEMON_DATA
        self.level = level
        self.moves = data["moves"][:4]  # Max 4 moves
        
        # Calculate stats based on level and base stats
        self.max_hp = self._calculate_hp(data["base_stats"]["hp"])
        self.current_hp = self.max_hp
        self.attack = self._calculate_stat(data["base_stats"]["attack"])
        self.defense = self._calculate_stat(data["base_stats"]["defense"])
        self.sp_attack = self._calculate_stat(data["base_stats"]["sp_attack"])
        self.sp_defense = self._calculate_stat(data["base_stats"]["sp_defense"])
        self.speed = self._calculate_stat(data["base_stats"]["speed"])
        
        # Battle modifiers
        self.stat_stages = {
            "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0, "accuracy": 0, "evasion": 0
        }
        self.status = None  # None, "paralyzed", "poisoned", "burned", "asleep", "frozen"
    
    def _calculate_hp(self, base_hp: int) -> int:
        """
        Calculate the HP stat based on base HP and level.
        
        Args:
            base_hp: The Pokémon's base HP stat
        
        Returns:
            The calculated HP stat
        """
        # Simplified HP calculation
        return int((2 * base_hp * self.level) / 100) + self.level + 10
    
    def _calculate_stat(self, base_stat: int) -> int:
        """
        Calculate a stat (other than HP) based on base stat and level.
        
        Args:
            base_stat: The Pokémon's base stat value
        
        Returns:
            The calculated stat value
        """
        # Simplified stat calculation
        return int((2 * base_stat * self.level) / 100) + 5
    
    def is_fainted(self) -> bool:
        """
        Check if the Pokémon has fainted.
        
        Returns:
            True if the Pokémon's HP is 0 or less, False otherwise
        """
        return self.current_hp <= 0
    
    def get_modified_stat(self, stat_name: str) -> int:
        """
        Get a stat value after applying stat stage modifiers.
        
        Args:
            stat_name: The name of the stat to get
            
        Returns:
            The modified stat value
        """
        # Get the base stat value
        if stat_name == "attack":
            base_value = self.attack
        elif stat_name == "defense":
            base_value = self.defense
        elif stat_name == "sp_attack":
            base_value = self.sp_attack
        elif stat_name == "sp_defense":
            base_value = self.sp_defense
        elif stat_name == "speed":
            base_value = self.speed
        else:
            return 1.0  # For accuracy and evasion
        
        # Apply stat stage modifier
        stage = self.stat_stages.get(stat_name, 0)
        if stat_name in ["accuracy", "evasion"]:
            # Accuracy and evasion use different multipliers
            if stage >= 0:
                multiplier = (3 + stage) / 3
            else:
                multiplier = 3 / (3 - stage)
        else:
            # Other stats
            if stage >= 0:
                multiplier = (2 + stage) / 2
            else:
                multiplier = 2 / (2 - stage)
        
        # Apply status effects
        if stat_name == "speed" and self.status == "paralyzed":
            multiplier *= 0.5
        elif stat_name == "attack" and self.status == "burned":
            multiplier *= 0.5
        
        return int(base_value * multiplier)
    
    def take_damage(self, damage: int) -> int:
        """
        Apply damage to the Pokémon.
        
        Args:
            damage: The amount of damage to apply
            
        Returns:
            The actual amount of damage dealt
        """
        damage = max(1, damage)  # Minimum 1 damage
        self.current_hp = max(0, self.current_hp - damage)
        return damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the Pokémon.
        
        Args:
            amount: The amount of HP to heal
            
        Returns:
            The actual amount healed
        """
        if self.is_fainted():
            return 0
            
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def apply_status(self, status: str) -> bool:
        """
        Apply a status condition to the Pokémon.
        
        Args:
            status: The status to apply
            
        Returns:
            True if the status was applied, False otherwise
        """
        # Already has a status
        if self.status:
            return False
            
        # Type-based immunities
        if status == "paralyzed" and "Electric" in self.types:
            return False
        if status == "poisoned" and ("Poison" in self.types or "Steel" in self.types):
            return False
        if status == "burned" and "Fire" in self.types:
            return False
            
        self.status = status
        return True
    
    def clear_status(self) -> None:
        """Clear the Pokémon's status condition."""
        self.status = None
    
    def modify_stat_stage(self, stat: str, stages: int) -> int:
        """
        Modify a stat stage.
        
        Args:
            stat: The stat to modify
            stages: The number of stages to add (can be negative)
            
        Returns:
            The actual number of stages changed
        """
        if stat not in self.stat_stages:
            return 0
            
        old_stage = self.stat_stages[stat]
        new_stage = max(-6, min(6, old_stage + stages))
        self.stat_stages[stat] = new_stage
        return new_stage - old_stage
    
    def reset_stat_stages(self) -> None:
        """Reset all stat stages to 0."""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0
    
    def display_info(self) -> str:
        """
        Get a string representation of the Pokémon's battle info.
        
        Returns:
            A formatted string with the Pokémon's info
        """
        status_text = f"[{self.status[:3].upper()}]" if self.status else ""
        hp_percent = int((self.current_hp / self.max_hp) * 100)
        hp_bar = "="*int(hp_percent/5) + " "*(20-int(hp_percent/5))
        
        return f"{self.nickname} (Lv.{self.level}) {status_text}\nHP: [{hp_bar}] {self.current_hp}/{self.max_hp} ({hp_percent}%)"
