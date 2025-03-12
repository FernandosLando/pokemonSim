"""
This module contains the client code for connecting to a Pokémon battle server.
"""

import socket
import json
import time
from typing import List, Dict, Any, Optional, Union
from data import POKEMON_DATA

class PokemonClient:
    """
    Client for connecting to a Pokémon battle server.
    
    Attributes:
        socket (socket.socket): The client socket
        connected (bool): Whether the client is connected
        name (str): The player's name
        server_address (tuple): The server address (host, port)
    """
    
    def __init__(self):
        """Initialize a new Pokémon client."""
        self.socket = None
        self.connected = False
        self.name = None
        self.server_address = None
    
    def connect(self, host: str, port: int) -> bool:
        """
        Connect to a Pokémon battle server.
        
        Args:
            host: The server host address
            port: The server port
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.server_address = (host, port)
            print(f"Connected to server at {host}:{port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.socket = None
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.socket = None
        print("Disconnected from server")
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """
        Send data to the server.
        
        Args:
            data: The data to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(data).encode('utf-8')
            message_length = len(serialized)
            header = message_length.to_bytes(4, byteorder='big')
            self.socket.sendall(header + serialized)
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            self.connected = False
            return False
    
    def receive_data(self) -> Optional[Dict[str, Any]]:
        """
        Receive data from the server.
        
        Returns:
            The received data, or None if an error occurred
        """
        try:
            # Read message length (4 bytes)
            header = self.socket.recv(4)
            if not header or len(header) != 4:
                self.connected = False
                return None
                
            message_length = int.from_bytes(header, byteorder='big')
            
            # Read the actual message
            chunks = []
            bytes_received = 0
            
            while bytes_received < message_length:
                chunk = self.socket.recv(min(message_length - bytes_received, 4096))
                if not chunk:
                    self.connected = False
                    return None
                chunks.append(chunk)
                bytes_received += len(chunk)
                
            message = b''.join(chunks)
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.connected = False
            return None
    
    def handle_game_loop(self) -> None:
        """Main game loop for online play."""
        if not self.connected:
            print("Not connected to a server")
            return
        
        try:
            # Wait for welcome message
            welcome = self.receive_data()
            if not welcome or welcome.get("type") != "welcome":
                print("Invalid welcome message received")
                return
                
            print(welcome["message"])
            
            # Set player name
            name_request = self.receive_data()
            if not name_request or name_request.get("type") != "request_name":
                print("Invalid name request received")
                return
                
            print(name_request["message"])
            self.name = input("> ")
            self.send_data({"name": self.name})
            
            # Choose mode (host or join)
            mode_request = self.receive_data()
            if not mode_request or mode_request.get("type") != "request_mode":
                print("Invalid mode request received")
                return
                
            print(mode_request["message"])
            print("1. Host a battle")
            print("2. Join a battle")
            
            while True:
                choice = input("> ")
                if choice == "1":
                    mode = "host"
                    break
                elif choice == "2":
                    mode = "join"
                    break
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            
            self.send_data({"mode": mode})
            
            # Handle battle creation or joining
            if mode == "host":
                battle_created = self.receive_data()
                if not battle_created or battle_created.get("type") != "battle_created":
                    print("Failed to create battle")
                    return
                    
                print(battle_created["message"])
                battle_id = battle_created["battle_id"]
                
                # Wait for opponent
                opponent_joined = self.receive_data()
                if not opponent_joined or opponent_joined.get("type") != "opponent_joined":
                    print("Connection error while waiting for opponent")
                    return
                    
                print(opponent_joined["message"])
                
            elif mode == "join":
                # Get available battles
                available_battles = self.receive_data()
                
                if available_battles.get("type") == "no_battles":
                    print(available_battles["message"])
                    return
                    
                if not available_battles or available_battles.get("type") != "available_battles":
                    print("Failed to get available battles")
                    return
                
                # Show available battles
                battles = available_battles.get("battles", [])
                if not battles:
                    print("No battles available to join")
                    return
                
                print("Available battles:")
                for i, battle in enumerate(battles):
                    print(f"{i+1}. Battle #{battle['battle_id']} hosted by {battle['host_name']}")
                
                # Select a battle
                while True:
                    try:
                        choice = int(input("Select a battle to join (number): "))
                        if 1 <= choice <= len(battles):
                            selected_battle = battles[choice-1]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(battles)}")
                    except ValueError:
                        print("Please enter a valid number")
                
                # Send battle selection
                self.send_data({"battle_id": selected_battle["battle_id"]})
                
                # Wait for confirmation
                battle_joined = self.receive_data()
                if not battle_joined or battle_joined.get("type") != "battle_joined":
                    print("Failed to join battle")
                    return
                
                print(battle_joined["message"])
            
            # Team selection
            team_selection = self.receive_data()
            if not team_selection or team_selection.get("type") != "team_selection":
                print("Failed to enter team selection")
                return
            
            print(team_selection["message"])
            team = self.select_team()
            self.send_data({"team": team})
            
            # Battle loop
            while True:
                # Wait for action request or other message
                battle_data = self.receive_data()
                if not battle_data:
                    print("Battle connection lost")
                    break
                
                # Handle different message types
                message_type = battle_data.get("type", "")
                
                if message_type == "request_action":
                    # Display battle state
                    self.display_battle_state(battle_data)
                    
                    # Choose action
                    action = self.choose_battle_action(battle_data)
                    self.send_data({"action": action})
                    
                elif message_type == "request_switch":
                    # Display battle state
                    self.display_battle_state(battle_data)
                    print(battle_data.get("message", "Choose a Pokémon to switch to:"))
                    
                    # Choose Pokémon to switch to
                    switch_action = self.choose_switch_pokemon(battle_data)
                    self.send_data({"action": switch_action})
                    
                elif message_type == "turn_results":
                    # Display turn results
                    self.display_turn_results(battle_data)
                    
                    # Check if battle is over
                    if battle_data.get("battle_over", False):
                        battle_over = self.receive_data()
                        if battle_over and battle_over.get("type") == "battle_over":
                            print("\n" + battle_over["message"])
                        break
                        
                elif message_type == "battle_over":
                    # Display battle over message
                    print("\n" + battle_data["message"])
                    break
                    
                else:
                    print(f"Unknown message type: {message_type}")
        
        except Exception as e:
            print(f"Error in game loop: {e}")
        finally:
            # Disconnect when done
            self.disconnect()
    
    def select_team(self) -> List[Dict[str, Any]]:
        """
        Let the player select their team.
        
        Returns:
            A list of Pokémon data dictionaries
        """
        team = []
        
        print("\nSelect your team of up to 6 Pokémon:")
        print("Enter 'L' to see the list of available Pokémon")
        
        while len(team) < 6:
            choice = input(f"Pokémon #{len(team)+1} (or 'D' when done): ").strip().upper()
            
            if choice == 'D' and len(team) > 0:
                # Done selecting
                break
            elif choice == 'L':
                # Show list
                self.display_available_pokemon()
            else:
                try:
                    pokemon_id = int(choice)
                    if pokemon_id in POKEMON_DATA:
                        nickname = input(f"Nickname for {POKEMON_DATA[pokemon_id]['name']} (leave blank for default): ").strip()
                        if not nickname:
                            nickname = POKEMON_DATA[pokemon_id]['name']
                        
                        team.append({
                            "id": pokemon_id,
                            "nickname": nickname,
                            "level": 50  # Fixed level for simplicity
                        })
                        
                        print(f"Added {nickname} to your team!")
                    else:
                        print(f"No Pokémon with ID {pokemon_id}")
                except ValueError:
                    print("Please enter a valid Pokémon ID, 'L' for list, or 'D' when done")
        
        return team
    
    def display_available_pokemon(self) -> None:
        """Display the list of available Pokémon."""
        print("\nAvailable Pokémon:")
        for pokemon_id, data in POKEMON_DATA.items():
            types = "/".join(data["types"])
            print(f"{pokemon_id}. {data['name']} ({types})")
        print()
    
    def display_battle_state(self, state: Dict[str, Any]) -> None:
        """
        Display the current battle state.
        
        Args:
            state: The battle state data
        """
        active_pokemon = state["active_pokemon"]
        opponent_pokemon = state["opponent_pokemon"]
        
        # Clear screen (works on most terminals)
        print("\033c", end="")
        
        # Show opponent's Pokémon
        hp_percent = opponent_pokemon["current_hp_percent"] * 100
        status = f"[{opponent_pokemon['status'][:3].upper()}]" if opponent_pokemon["status"] else ""
        print(f"Opponent's {opponent_pokemon['nickname']} (Lv.{opponent_pokemon['level']} {opponent_pokemon['name']}) {status}")
        print(f"HP: {self.generate_hp_bar(hp_percent)} {hp_percent:.1f}%")
        print()
        
        # Show your Pokémon
        status = f"[{active_pokemon['status'][:3].upper()}]" if active_pokemon["status"] else ""
        print(f"Your {active_pokemon['nickname']} (Lv.{active_pokemon['level']} {active_pokemon['name']}) {status}")
        print(f"HP: {active_pokemon['current_hp']}/{active_pokemon['max_hp']} {self.generate_hp_bar(active_pokemon['current_hp'] / active_pokemon['max_hp'] * 100)}")
        print(f"Moves: {', '.join(active_pokemon['moves'])}")
        print(f"Potions remaining: {state['potions']}")
        print()
    
    def generate_hp_bar(self, percent: float) -> str:
        """
        Generate a visual HP bar.
        
        Args:
            percent: The HP percentage to display
            
        Returns:
            A formatted HP bar string
        """
        bar_length = 20
        filled_length = int(bar_length * percent / 100)
        
        if percent > 50:
            color = "\033[92m"  # Green
        elif percent > 20:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
            
        reset = "\033[0m"
        
        bar = f"{color}{'█' * filled_length}{reset}{'-' * (bar_length - filled_length)}"
        return f"[{bar}]"
    
    def choose_battle_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Let the player choose a battle action.
        
        Args:
            state: The battle state data
            
        Returns:
            An action dictionary
        """
        active_pokemon = state["active_pokemon"]
        team = state["team"]
        potions = state["potions"]
        
        print("What would you like to do?")
        print("1. Fight")
        print("2. Switch Pokémon")
        print("3. Use Potion")
        
        while True:
            choice = input("> ")
            
            if choice == "1":
                # Choose a move
                print("\nChoose a move:")
                for i, move in enumerate(active_pokemon["moves"]):
                    print(f"{i+1}. {move}")
                
                while True:
                    move_choice = input("> ")
                    try:
                        move_index = int(move_choice) - 1
                        if 0 <= move_index < len(active_pokemon["moves"]):
                            return {"type": "move", "move": active_pokemon["moves"][move_index]}
                        else:
                            print(f"Please enter a number between 1 and {len(active_pokemon['moves'])}")
                    except ValueError:
                        print("Please enter a valid number")
            
            elif choice == "2":
                # Switch Pokémon
                return self.choose_switch_pokemon(state)
            
            elif choice == "3":
                if potions <= 0:
                    print("You don't have any potions left!")
                    continue
                    
                # Use potion
                print("\nChoose a Pokémon to use a potion on:")
                valid_targets = []
                
                for i, pokemon in enumerate(team):
                    if not pokemon["is_fainted"] and pokemon["current_hp"] < pokemon["max_hp"]:
                        valid_targets.append(i)
                        print(f"{i+1}. {pokemon['nickname']} (HP: {pokemon['current_hp']}/{pokemon['max_hp']})")
                
                if not valid_targets:
                    print("No Pokémon need healing!")
                    continue
                
                while True:
                    target_choice = input("> ")
                    try:
                        target_index = int(target_choice) - 1
                        if target_index in valid_targets:
                            return {"type": "item", "item": "potion", "target_index": target_index}
                        else:
                            print("Please choose a valid Pokémon")
                    except ValueError:
                        print("Please enter a valid number")
            
            else:
                print("Please enter 1, 2, or 3")
    
    def choose_switch_pokemon(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Let the player choose a Pokémon to switch to.
        
        Args:
            state: The battle state data
            
        Returns:
            A switch action dictionary
        """
        team = state["team"]
        active_index = next((i for i, p in enumerate(team) if p == state["active_pokemon"]), 0)
        
        print("\nChoose a Pokémon to switch to:")
        valid_switches = []
        
        for i, pokemon in enumerate(team):
            if not pokemon["is_fainted"] and i != active_index:
                valid_switches.append(i)
                status = f"[{pokemon['status'][:3].upper()}]" if pokemon["status"] else ""
                print(f"{i+1}. {pokemon['nickname']} (HP: {pokemon['current_hp']}/{pokemon['max_hp']}) {status}")
        
        if not valid_switches:
            print("No other Pokémon available to switch to!")
            return {"type": "pass"}
        
        while True:
            switch_choice = input("> ")
            try:
                pokemon_index = int(switch_choice) - 1
                if pokemon_index in valid_switches:
                    return {"type": "switch", "pokemon_index": pokemon_index}
                else:
                    print("Please choose a valid Pokémon")
            except ValueError:
                print("Please enter a valid number")
    
    def display_turn_results(self, results: Dict[str, Any]) -> None:
        """
        Display the results of a turn.
        
        Args:
            results: The turn results data
        """
        # Display battle log
        print("\nBattle Log:")
        for log_entry in results["log"]:
            print(log_entry)
        
        input("\nPress Enter to continue...")
