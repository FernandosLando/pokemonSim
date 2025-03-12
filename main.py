"""
Main entry point for the Pokémon Battle Simulator.
This file contains the game's UI and main menu functionality.
"""

import time
import random
import sys
import os
from typing import List, Dict, Any, Optional, Union

from pokemon import Pokemon
from player import Player, HumanPlayer, AIPlayer
from battle import Battle
from client import PokemonClient
from network import PokemonServer

def display_title_screen() -> None:
    """Display the game's title screen."""
    print("\n" + "="*60)
    print("""
    ██████╗  ██████╗ ██╗  ██╗███████╗███╗   ███╗ ██████╗ ███╗   ██╗
    ██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝████╗ ████║██╔═══██╗████╗  ██║
    ██████╔╝██║   ██║█████╔╝ █████╗  ██╔████╔██║██║   ██║██╔██╗ ██║
    ██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╔╝██║██║   ██║██║╚██╗██║
    ██║     ╚██████╔╝██║  ██╗███████╗██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                     
    ██████╗  █████╗ ████████╗████████╗██╗     ███████╗               
    ██╔══██╗██╔══██╗╚══██╔══╝╚══██╔══╝██║     ██╔════╝               
    ██████╔╝███████║   ██║      ██║   ██║     █████╗                 
    ██╔══██╗██╔══██║   ██║      ██║   ██║     ██╔══╝                 
    ██████╔╝██║  ██║   ██║      ██║   ███████╗███████╗               
    ╚═════╝ ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚══════╝╚══════╝               
                                                                     
    ███████╗██╗███╗   ███╗██╗   ██╗██╗      █████╗ ████████╗ ██████╗ ██████╗ 
    ██╔════╝██║████╗ ████║██║   ██║██║     ██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
    ███████╗██║██╔████╔██║██║   ██║██║     ███████║   ██║   ██║   ██║██████╔╝
    ╚════██║██║██║╚██╔╝██║██║   ██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗
    ███████║██║██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║
    ╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝                                                        
    """)
    print("="*60)
    print("\nWelcome to the Pokémon Battle Simulator!")
    print("A terminal-based Pokémon battle simulator featuring Gen V Pokémon.")
    print("\n" + "="*60)
    input("\nPress Enter to start...")


def clear_screen() -> None:
    """Clear the terminal screen."""
    # Cross-platform clear screen
    os.system('cls' if os.name == 'nt' else 'clear')


def main_menu() -> None:
    """Display the main menu and handle user selection."""
    while True:
        # Clear screen
        clear_screen()
        
        print("\n=== MAIN MENU ===")
        print("1. Single Player")
        print("2. Online Play")
        print("3. View Pokémon List")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ")
        
        if choice == "1":
            single_player_menu()
        elif choice == "2":
            online_play_menu()
        elif choice == "3":
            display_pokemon_list()
        elif choice == "4":
            print("\nThank you for playing! Goodbye.")
            break
        else:
            print("\nInvalid choice. Please try again.")
            input("\nPress Enter to continue...")


def single_player_menu() -> None:
    """Handle single player mode selection."""
    clear_screen()
    print("\n=== SINGLE PLAYER ===")
    
    # Get player name
    player_name = input("\nEnter your name: ")
    
    # Select difficulty
    print("\nSelect AI difficulty:")
    print("1. Easy")
    print("2. Medium")
    print("3. Hard")
    
    while True:
        difficulty_choice = input("\nSelect difficulty (1-3): ")
        if difficulty_choice in ["1", "2", "3"]:
            break
        print("Invalid choice. Please try again.")
    
    difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
    difficulty = difficulty_map[difficulty_choice]
    
    # Create player objects
    human_player = HumanPlayer(player_name)
    ai_player = AIPlayer(f"AI Trainer ({difficulty.capitalize()})", difficulty)
    
    # Set up teams
    setup_player_team(human_player)
    setup_ai_team(ai_player)
    
    # Make sure players have at least one Pokémon
    if len(human_player.team) == 0:
        print("You need at least one Pokémon to battle!")
        input("\nPress Enter to return to the menu...")
        return
    
    # Start battle
    battle = Battle(human_player, ai_player)
    run_battle(battle)


def online_play_menu() -> None:
    """Handle online play mode selection."""
    clear_screen()
    print("\n=== ONLINE PLAY ===")
    print("1. Host a Server")
    print("2. Join a Server")
    print("3. Back to Main Menu")
    
    choice = input("\nSelect an option (1-3): ")
    
    if choice == "1":
        host_server()
    elif choice == "2":
        join_server()
    elif choice == "3":
        return
    else:
        print("\nInvalid choice.")
        input("\nPress Enter to continue...")
        online_play_menu()


def host_server() -> None:
    """Host a battle server."""
    clear_screen()
    print("\n=== HOST SERVER ===")
    
    # Get server details
    port = 5555
    try:
        port_input = input("Enter port number (default: 5555): ")
        if port_input:
            port = int(port_input)
    except ValueError:
        print("Invalid port number. Using default (5555).")
    
    # Start server
    server = PokemonServer(port=port)
    if server.start():
        print(f"\nServer started on port {port}")
        print("Players can connect to your IP address")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            # Keep main thread alive until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
        finally:
            server.stop()
    
    input("\nPress Enter to return to the menu...")


def join_server() -> None:
    """Join a battle server."""
    clear_screen()
    print("\n=== JOIN SERVER ===")
    
    # Get server details
    host = input("Enter server IP address: ")
    if not host:
        print("Invalid IP address.")
        input("\nPress Enter to continue...")
        return
    
    port = 5555
    try:
        port_input = input("Enter server port (default: 5555): ")
        if port_input:
            port = int(port_input)
    except ValueError:
        print("Invalid port number. Using default (5555).")
    
    # Connect to server
    client = PokemonClient()
    if client.connect(host, port):
        print(f"\nConnected to server at {host}:{port}")
        client.handle_game_loop()
    else:
        print(f"\nFailed to connect to server at {host}:{port}")
    
    input("\nPress Enter to return to the menu...")


def display_pokemon_list() -> None:
    """Display the list of available Pokémon."""
    from data import POKEMON_DATA
    
    clear_screen()
    print("\n=== POKÉMON LIST ===")
    
    for pokemon_id, data in POKEMON_DATA.items():
        types = "/".join(data["types"])
        print(f"{pokemon_id}. {data['name']} ({types})")
        print(f"   HP: {data['base_stats']['hp']}  Atk: {data['base_stats']['attack']}  Def: {data['base_stats']['defense']}")
        print(f"   Sp.Atk: {data['base_stats']['sp_attack']}  Sp.Def: {data['base_stats']['sp_defense']}  Spd: {data['base_stats']['speed']}")
        print(f"   Moves: {', '.join(data['moves'][:4])}")
        print()
    
    input("\nPress Enter to return to the menu...")


def setup_player_team(player: Player) -> None:
    """
    Set up the player's team.
    
    Args:
        player: The player to set up the team for
    """
    from data import POKEMON_DATA
    
    clear_screen()
    print("\n=== TEAM SELECTION ===")
    print(f"Select up to 6 Pokémon for your team, {player.name}.")
    print("Enter 'L' to see the list of available Pokémon")
    
    while len(player.team) < 6:
        choice = input(f"\nPokémon #{len(player.team)+1} (or 'D' when done): ").strip().upper()
        
        if choice == 'D' and len(player.team) > 0:
            # Done selecting
            break
        elif choice == 'L':
            # Show list
            display_pokemon_list()
            clear_screen()
            print("\n=== TEAM SELECTION ===")
            print(f"Select up to 6 Pokémon for your team, {player.name}.")
            print("Enter 'L' to see the list of available Pokémon")
        else:
            try:
                pokemon_id = int(choice)
                if pokemon_id in POKEMON_DATA:
                    nickname = input(f"Nickname for {POKEMON_DATA[pokemon_id]['name']} (leave blank for default): ").strip()
                    
                    # Create and add the Pokémon
                    pokemon = Pokemon(pokemon_id, level=50, nickname=nickname or None)
                    player.add_pokemon(pokemon)
                    
                    print(f"Added {pokemon.nickname} to your team!")
                else:
                    print(f"No Pokémon with ID {pokemon_id}")
            except ValueError:
                print("Please enter a valid Pokémon ID, 'L' for list, or 'D' when done")


def setup_ai_team(ai_player: AIPlayer) -> None:
    """
    Set up the AI player's team based on difficulty.
    
    Args:
        ai_player: The AI player to set up the team for
    """
    from data import POKEMON_DATA
    
    team_size = 6
    available_ids = list(POKEMON_DATA.keys())
    
    # Different selection strategies based on difficulty
    if ai_player.difficulty == "easy":
        # Random selection for easy AI
        selected_ids = random.sample(available_ids, team_size)
    elif ai_player.difficulty == "medium":
        # Slightly more balanced team for medium AI
        # Ensure at least one Pokémon of each type category
        starter_ids = [3, 6, 9]  # Final evolutions of starters
        selected_ids = random.sample(starter_ids, 1)  # Pick one starter
        selected_ids.extend(random.sample([id for id in available_ids if id not in starter_ids], team_size - 1))
    else:  # Hard
        # More strategic team for hard AI
        # Include some powerful Pokémon and ensure type coverage
        powerful_ids = [12, 14, 15, 16, 17]  # Some of the strongest Gen V Pokémon
        selected_ids = random.sample(powerful_ids, 2)  # Pick two strong Pokémon
        
        # Add more for balance and coverage
        remaining = [id for id in available_ids if id not in selected_ids]
        selected_ids.extend(random.sample(remaining, team_size - 2))
    
    # Create and add Pokémon to the team
    for pokemon_id in selected_ids:
        pokemon = Pokemon(pokemon_id, level=50)
        ai_player.add_pokemon(pokemon)


def run_battle(battle: Battle) -> None:
    """
    Run a battle between two players.
    
    Args:
        battle: The Battle object
    """
    clear_screen()
    print("\n" + "="*60)
    print(f"BATTLE: {battle.player1.name} vs {battle.player2.name}")
    print("="*60 + "\n")
    
    print(f"{battle.player1.name} sent out {battle.player1.active_pokemon.nickname}!")
    print(f"{battle.player2.name} sent out {battle.player2.active_pokemon.nickname}!")
    
    # Battle loop
    while not battle.is_battle_over:
        # Display current state
        p1_pokemon = battle.player1.active_pokemon
        p2_pokemon = battle.player2.active_pokemon
        
        print("\n" + "-"*40)
        print(f"{battle.player1.name}'s {p1_pokemon.display_info()}")
        print(f"{battle.player2.name}'s {p2_pokemon.display_info()}")
        print("-"*40 + "\n")
        
        # Get actions from players
        player1_action = battle.player1.choose_action(battle)
        player2_action = battle.player2.choose_action(battle)
        
        # Execute turn
        battle.execute_turn(player1_action, player2_action)
        
        # Check if a player needs to switch after fainting
        if battle.player1.active_pokemon.is_fainted() and battle.player1.has_usable_pokemon():
            print(f"\n{battle.player1.name} must switch to another Pokémon!")
            
            # Keep prompting until a valid switch is made
            while True:
                switch_action = battle.player1.choose_switch()
                if switch_action["type"] == "switch":
                    if battle.player1.switch_pokemon(switch_action["pokemon_index"]):
                        print(f"{battle.player1.name} sent out {battle.player1.active_pokemon.nickname}!")
                        break
                    else:
                        print("Invalid switch. Try again.")
        
        if battle.player2.active_pokemon.is_fainted() and battle.player2.has_usable_pokemon():
            if isinstance(battle.player2, AIPlayer):
                # AI chooses automatically
                for i, pokemon in enumerate(battle.player2.team):
                    if not pokemon.is_fainted():
                        battle.player2.switch_pokemon(i)
                        print(f"{battle.player2.name} sent out {battle.player2.active_pokemon.nickname}!")
                        break
            else:
                # Human player needs to choose
                print(f"\n{battle.player2.name} must switch to another Pokémon!")
                
                while True:
                    switch_action = battle.player2.choose_switch()
                    if switch_action["type"] == "switch":
                        if battle.player2.switch_pokemon(switch_action["pokemon_index"]):
                            print(f"{battle.player2.name} sent out {battle.player2.active_pokemon.nickname}!")
                            break
                        else:
                            print("Invalid switch. Try again.")
    
    # Battle is over, announce winner
    if battle.winner:
        print(f"\n{battle.winner.name} won the battle!")
    else:
        print("\nThe battle ended in a draw!")
    
    input("\nPress Enter to continue...")


def main() -> None:
    """Main function to run the game."""
    try:
        # Display title screen
        display_title_screen()
        
        # Show main menu
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
