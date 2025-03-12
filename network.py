"""
This module contains networking classes for online Pokémon battles.
"""

import socket
import threading
import json
import time
import random
from typing import List, Dict, Any, Tuple, Optional, Union
from pokemon import Pokemon
from player import Player, OnlinePlayer
from battle import Battle

class PokemonServer:
    """
    Server for hosting online Pokémon battles.
    
    Attributes:
        host (str): Server host address
        port (int): Server port
        running (bool): Whether the server is running
        server_socket (socket.socket): Server socket
        clients (List[Tuple[socket.socket, str]]): Connected clients (socket, name)
        battles (Dict[str, Dict]): Active battles
        threads (List[threading.Thread]): Active threads
    """
    
    def __init__(self, host: str = "", port: int = 5555):
        """
        Initialize a new Pokémon battle server.
        
        Args:
            host: Server host address (default: all interfaces)
            port: Server port (default: 5555)
        """
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        self.battles = {}
        self.threads = []
    
    def start(self) -> bool:
        """
        Start the server.
        
        Returns:
            True if the server started successfully, False otherwise
        """
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"Server started on port {self.port}")
            
            # Start main thread
            main_thread = threading.Thread(target=self._accept_connections)
            main_thread.daemon = True
            main_thread.start()
            self.threads.append(main_thread)
            
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the server."""
        self.running = False
        
        # Close client connections
        for client_socket, _ in self.clients:
            try:
                client_socket.close()
            except:
                pass
                
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        print("Server stopped")
    
    def _accept_connections(self) -> None:
        """Accept and handle incoming client connections."""
        while self.running:
            try:
                # Accept connection
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address[0]}:{client_address[1]}")
                
                # Start client handler thread
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
                self.threads.append(client_thread)
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                    time.sleep(1)
    
    def _handle_client(self, client_socket: socket.socket) -> None:
        """
        Handle a client connection.
        
        Args:
            client_socket: The client's socket
        """
        try:
            # Send welcome message
            self.send_data(client_socket, {
                "type": "welcome",
                "message": "Welcome to the Pokémon Battle Server!"
            })
            
            # Request player name
            self.send_data(client_socket, {
                "type": "request_name",
                "message": "Please enter your name:"
            })
            
            # Get player name
            name_data = self.receive_data(client_socket)
            if not name_data or "name" not in name_data:
                print("Invalid name data received")
                client_socket.close()
                return
                
            player_name = name_data["name"]
            print(f"Player {player_name} connected")
            
            # Add to clients list
            self.clients.append((client_socket, player_name))
            
            # Request mode (host or join)
            self.send_data(client_socket, {
                "type": "request_mode",
                "message": "Would you like to host a battle or join an existing one?"
            })
            
            # Get mode
            mode_data = self.receive_data(client_socket)
            if not mode_data or "mode" not in mode_data:
                print("Invalid mode data received")
                client_socket.close()
                return
                
            mode = mode_data["mode"]
            
            # Handle mode
            if mode == "host":
                self._handle_host_mode(client_socket, player_name)
            elif mode == "join":
                self._handle_join_mode(client_socket, player_name)
            else:
                print(f"Invalid mode: {mode}")
                client_socket.close()
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # Remove from clients list
            self.clients = [(s, n) for s, n in self.clients if s != client_socket]
            
            try:
                client_socket.close()
            except:
                pass
                
            print(f"Connection closed for player {player_name}")
    
    def _handle_host_mode(self, client_socket: socket.socket, player_name: str) -> None:
        """
        Handle a client in host mode.
        
        Args:
            client_socket: The client's socket
            player_name: The client's name
        """
        # Create a battle ID
        battle_id = str(random.randint(1000, 9999))
        while battle_id in self.battles:
            battle_id = str(random.randint(1000, 9999))
            
        # Create battle
        self.battles[battle_id] = {
            "host_socket": client_socket,
            "host_name": player_name,
            "challenger_socket": None,
            "challenger_name": None,
            "status": "waiting"  # waiting, in_progress, completed
        }
        
        # Inform client
        self.send_data(client_socket, {
            "type": "battle_created",
            "message": f"Battle #{battle_id} created. Waiting for an opponent...",
            "battle_id": battle_id
        })
        
        # Wait for challenger (handled in _handle_join_mode)
        # This waiting is asynchronous - the server continues to accept connections
        
        # Wait for battle to start
        while battle_id in self.battles and self.battles[battle_id]["status"] == "waiting":
            time.sleep(0.5)
            
        # Check if battle was cancelled
        if battle_id not in self.battles:
            return
            
        # Get challenger info
        challenger_socket = self.battles[battle_id]["challenger_socket"]
        challenger_name = self.battles[battle_id]["challenger_name"]
        
        # Let host know opponent joined
        self.send_data(client_socket, {
            "type": "opponent_joined",
            "message": f"{challenger_name} has joined your battle!",
            "opponent_name": challenger_name
        })
        
        # Start team selection
        self._handle_team_selection(battle_id, client_socket, challenger_socket, player_name, challenger_name)
    
    def _handle_join_mode(self, client_socket: socket.socket, player_name: str) -> None:
        """
        Handle a client in join mode.
        
        Args:
            client_socket: The client's socket
            player_name: The client's name
        """
        # Check available battles
        available_battles = []
        for battle_id, battle in self.battles.items():
            if battle["status"] == "waiting":
                available_battles.append({
                    "battle_id": battle_id,
                    "host_name": battle["host_name"]
                })
                
        # Send available battles
        if not available_battles:
            self.send_data(client_socket, {
                "type": "no_battles",
                "message": "No battles available to join. Try hosting one instead!"
            })
            return
            
        self.send_data(client_socket, {
            "type": "available_battles",
            "message": "Choose a battle to join:",
            "battles": available_battles
        })
        
        # Get battle selection
        selection_data = self.receive_data(client_socket)
        if not selection_data or "battle_id" not in selection_data:
            print("Invalid battle selection received")
            return
            
        battle_id = selection_data["battle_id"]
        
        # Check if battle exists
        if battle_id not in self.battles or self.battles[battle_id]["status"] != "waiting":
            self.send_data(client_socket, {
                "type": "error",
                "message": "The selected battle is no longer available."
            })
            return
            
        # Join battle
        battle = self.battles[battle_id]
        battle["challenger_socket"] = client_socket
        battle["challenger_name"] = player_name
        
        # Inform client
        self.send_data(client_socket, {
            "type": "battle_joined",
            "message": f"Joined battle #{battle_id} hosted by {battle['host_name']}!",
            "host_name": battle["host_name"],
            "battle_id": battle_id
        })
        
        # Continue to team selection (handled by host's thread)
    
    def _handle_team_selection(self, battle_id: str, host_socket: socket.socket, 
                              challenger_socket: socket.socket, host_name: str, 
                              challenger_name: str) -> None:
        """
        Handle team selection for a battle.
        
        Args:
            battle_id: The battle ID
            host_socket: The host's socket
            challenger_socket: The challenger's socket
            host_name: The host's name
            challenger_name: The challenger's name
        """
        # Update battle status
        self.battles[battle_id]["status"] = "team_selection"
        
        # Request teams from both players
        for socket, name in [(host_socket, host_name), (challenger_socket, challenger_name)]:
            self.send_data(socket, {
                "type": "team_selection",
                "message": f"Select your team of up to 6 Pokémon."
            })
        
        # Get host team
        host_team_data = self.receive_data(host_socket)
        if not host_team_data or "team" not in host_team_data:
            print("Invalid host team data received")
            self._end_battle(battle_id, "Host disconnected during team selection")
            return
            
        # Get challenger team
        challenger_team_data = self.receive_data(challenger_socket)
        if not challenger_team_data or "team" not in challenger_team_data:
            print("Invalid challenger team data received")
            self._end_battle(battle_id, "Challenger disconnected during team selection")
            return
            
        # Create player objects and their teams
        host_player = OnlinePlayer(host_name, host_socket, self)
        challenger_player = OnlinePlayer(challenger_name, challenger_socket, self)
        
        # Add Pokémon to teams
        self._create_team_from_data(host_player, host_team_data["team"])
        self._create_team_from_data(challenger_player, challenger_team_data["team"])
        
        # Check if teams are valid
        if not host_player.team or not challenger_player.team:
            self._end_battle(battle_id, "Invalid team selection")
            return
            
        # Create battle
        battle = Battle(host_player, challenger_player)
        self.battles[battle_id]["battle"] = battle
        self.battles[battle_id]["status"] = "in_progress"
        
        # Start battle
        self._run_battle(battle_id, battle, host_player, challenger_player, host_socket, challenger_socket)
    
    def _create_team_from_data(self, player: Player, team_data: List[Dict[str, Any]]) -> None:
        """
        Create a team of Pokémon from client data.
        
        Args:
            player: The player to create the team for
            team_data: The team data from the client
        """
        from pokemon import Pokemon
        
        for i, pokemon_data in enumerate(team_data[:6]):  # Max 6 Pokémon
            try:
                pokemon_id = pokemon_data.get("id", 0)
                nickname = pokemon_data.get("nickname", "")
                level = pokemon_data.get("level", 50)
                
                # Create Pokémon
                pokemon = Pokemon(pokemon_id, level, nickname)
                player.add_pokemon(pokemon)
            except Exception as e:
                print(f"Error creating Pokémon: {e}")
    
    def _run_battle(self, battle_id: str, battle: Battle, host_player: Player, 
                   challenger_player: Player, host_socket: socket.socket, 
                   challenger_socket: socket.socket) -> None:
        """
        Run a battle between two players.
        
        Args:
            battle_id: The battle ID
            battle: The Battle object
            host_player: The host player
            challenger_player: The challenger player
            host_socket: The host's socket
            challenger_socket: The challenger's socket
        """
        # Battle loop
        while not battle.is_battle_over:
            try:
                # Get host action
                host_action = self._get_player_action(host_socket, battle, host_player)
                
                # Get challenger action
                challenger_action = self._get_player_action(challenger_socket, battle, challenger_player)
                
                # Execute turn
                turn_log = battle.execute_turn(host_action, challenger_action)
                
                # Send turn results to both players
                turn_results = {
                    "type": "turn_results",
                    "log": turn_log,
                    "battle_over": battle.is_battle_over
                }
                
                self.send_data(host_socket, turn_results)
                self.send_data(challenger_socket, turn_results)
                
                # Handle fainted Pokémon
                self._handle_fainted_pokemon(battle, host_player, host_socket)
                self._handle_fainted_pokemon(battle, challenger_player, challenger_socket)
                
            except Exception as e:
                print(f"Error in battle: {e}")
                self._end_battle(battle_id, f"Error: {e}")
                return
                
        # Battle is over
        self._end_battle(battle_id, f"{battle.winner.name if battle.winner else 'No one'} won the battle!")
    
    def _get_player_action(self, client_socket: socket.socket, battle: Battle, player: Player) -> Dict[str, Any]:
        """
        Get an action from a player.
        
        Args:
            client_socket: The player's socket
            battle: The Battle object
            player: The Player object
            
        Returns:
            The action dictionary
        """
        # Prepare state data
        state = self._get_battle_state(battle, player)
        
        # Send state and request action
        self.send_data(client_socket, {
            "type": "request_action",
            **state
        })
        
        # Get action
        action_data = self.receive_data(client_socket)
        if not action_data or "action" not in action_data:
            return {"type": "pass"}
            
        return action_data["action"]
    
    def _get_battle_state(self, battle: Battle, player: Player) -> Dict[str, Any]:
        """
        Get the current battle state for a player.
        
        Args:
            battle: The Battle object
            player: The Player object
            
        Returns:
            A dictionary with the battle state
        """
        # Get opponent
        opponent = battle.player1 if player == battle.player2 else battle.player2
        
        # Get player's active Pokémon
        active_pokemon = self._get_pokemon_info(player.active_pokemon, True) if player.active_pokemon else None
        
        # Get opponent's active Pokémon
        opponent_pokemon = self._get_pokemon_info(opponent.active_pokemon, False) if opponent.active_pokemon else None
        
        # Get player's team
        team = [self._get_pokemon_info(pokemon, True) for pokemon in player.team]
        
        return {
            "active_pokemon": active_pokemon,
            "opponent_pokemon": opponent_pokemon,
            "team": team,
            "potions": player.potions,
            "turn": battle.current_turn
        }
    
    def _get_pokemon_info(self, pokemon: Pokemon, full_info: bool) -> Dict[str, Any]:
        """
        Get information about a Pokémon.
        
        Args:
            pokemon: The Pokémon to get info for
            full_info: Whether to include full info (for player's own Pokémon)
            
        Returns:
            A dictionary with the Pokémon's info
        """
        if not pokemon:
            return None
            
        if not full_info:
            # Limited info for opponent's Pokémon
            return {
                "name": pokemon.name,
                "nickname": pokemon.nickname,
                "level": pokemon.level,
                "types": pokemon.types,
                "current_hp_percent": pokemon.current_hp / pokemon.max_hp,
                "status": pokemon.status,
                "is_fainted": pokemon.is_fainted()
            }
        else:
            # Full info for player's own Pokémon
            return {
                "id": pokemon.id,
                "name": pokemon.name,
                "nickname": pokemon.nickname,
                "level": pokemon.level,
                "types": pokemon.types,
                "moves": pokemon.moves,
                "current_hp": pokemon.current_hp,
                "max_hp": pokemon.max_hp,
                "status": pokemon.status,
                "stat_stages": pokemon.stat_stages,
                "is_fainted": pokemon.is_fainted()
            }
    
    def _handle_fainted_pokemon(self, battle: Battle, player: Player, client_socket: socket.socket) -> None:
        """
        Handle a player's fainted Pokémon.
        
        Args:
            battle: The Battle object
            player: The Player object
            client_socket: The player's socket
        """
        if battle.is_battle_over:
            return
            
        if player.active_pokemon and player.active_pokemon.is_fainted() and player.has_usable_pokemon():
            # Send switch request
            state = self._get_battle_state(battle, player)
            self.send_data(client_socket, {
                "type": "request_switch",
                "message": f"Your {player.active_pokemon.nickname} fainted! Choose another Pokémon.",
                **state
            })
            
            # Get switch action
            switch_data = self.receive_data(client_socket)
            if not switch_data or "action" not in switch_data or switch_data["action"].get("type") != "switch":
                # Auto-select first non-fainted Pokémon
                for i, pokemon in enumerate(player.team):
                    if not pokemon.is_fainted():
                        player.switch_pokemon(i)
                        break
            else:
                # Apply player's choice
                player.switch_pokemon(switch_data["action"].get("pokemon_index", 0))
    
    def _end_battle(self, battle_id: str, message: str) -> None:
        """
        End a battle with a message.
        
        Args:
            battle_id: The battle ID
            message: The end message
        """
        if battle_id not in self.battles:
            return
            
        battle = self.battles[battle_id]
        host_socket = battle.get("host_socket")
        challenger_socket = battle.get("challenger_socket")
        
        # Send battle over message to both players
        battle_over = {
            "type": "battle_over",
            "message": message
        }
        
        if host_socket:
            try:
                self.send_data(host_socket, battle_over)
            except:
                pass
                
        if challenger_socket:
            try:
                self.send_data(challenger_socket, battle_over)
            except:
                pass
                
        # Mark battle as completed
        battle["status"] = "completed"
        
        # Clean up after some time
        def cleanup():
            time.sleep(60)  # Wait a minute before cleanup
            if battle_id in self.battles:
                del self.battles[battle_id]
                
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()
    
    def send_data(self, client_socket: socket.socket, data: Dict[str, Any]) -> bool:
        """
        Send data to a client.
        
        Args:
            client_socket: The client's socket
            data: The data to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(data).encode('utf-8')
            message_length = len(serialized)
            header = message_length.to_bytes(4, byteorder='big')
            client_socket.sendall(header + serialized)
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            return False
    
    def receive_data(self, client_socket: socket.socket) -> Optional[Dict[str, Any]]:
        """
        Receive data from a client.
        
        Args:
            client_socket: The client's socket
            
        Returns:
            The received data, or None if an error occurred
        """
        try:
            # Read message length (4 bytes)
            header = client_socket.recv(4)
            if not header or len(header) != 4:
                return None
                
            message_length = int.from_bytes(header, byteorder='big')
            
            # Read the actual message
            chunks = []
            bytes_received = 0
            
            while bytes_received < message_length:
                chunk = client_socket.recv(min(message_length - bytes_received, 4096))
                if not chunk:
                    return None
                chunks.append(chunk)
                bytes_received += len(chunk)
                
            message = b''.join(chunks)
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None