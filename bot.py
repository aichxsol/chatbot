from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import random
import time

# Your bot's API Token (get it from BotFather)
API_TOKEN = 'YOUR_BOT_API_TOKEN'

# Game state variables
player_stats = {}
leaderboard = {}

# Monsters in the game (some with special abilities)
monsters = [
    {'name': 'Goblin', 'health': 30, 'attack': 10, 'defense': 5, 'ability': None},
    {'name': 'Troll', 'health': 50, 'attack': 15, 'defense': 8, 'ability': 'Poison'},
    {'name': 'Dragon', 'health': 100, 'attack': 30, 'defense': 15, 'ability': 'Fire Breath'},
]

# Skills available to players
skills = {
    'heal': {'cost': 10, 'effect': 30, 'description': 'Heals for 30 HP'},
    'fireball': {'cost': 20, 'effect': 40, 'description': 'Deals 40 damage to a monster'},
    'shield': {'cost': 15, 'effect': 10, 'description': 'Increases defense by 10 for one turn'},
    'berserk': {'cost': 25, 'effect': 50, 'description': 'Increases attack by 50 for one turn'},
    'poison': {'cost': 30, 'effect': 20, 'description': 'Deals 20 damage to the enemy over 3 turns'},
    'regen': {'cost': 15, 'effect': 10, 'description': 'Heals 10 HP over 3 turns'},
}

# Items available in the game
items = {
    'health_potion': {'effect': 50, 'description': 'Heals 50 HP'},
    'attack_buff': {'effect': 20, 'description': 'Increases attack by 20 for one battle'},
    'defense_buff': {'effect': 15, 'description': 'Increases defense by 15 for one battle'},
}

# Inventory tracking
inventory = {}

# Daily reward tracking
last_claimed = {}

# Command: /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in player_stats:
        player_stats[user_id] = {
            'health': 100,
            'attack': 20,
            'defense': 10,
            'level': 1,
            'experience': 0,
            'aichx_points': 0,
            'skill_points': 0,
            'skills': {'heal': 0, 'fireball': 0, 'shield': 0, 'berserk': 0, 'poison': 0, 'regen': 0},
            'inventory': {'health_potion': 0, 'attack_buff': 0, 'defense_buff': 0},
            'status_effects': {},  # for tracking status effects (like poison, regen)
        }
    update.message.reply_text("Welcome to the RPG Game! Type /fight to battle a monster, or /pvp to fight another player!")

# Command: /stats
def stats(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in player_stats:
        update.message.reply_text("You need to start a game first with /start!")
        return
    
    stats_text = f"Health: {player_stats[user_id]['health']}\n"
    stats_text += f"Attack: {player_stats[user_id]['attack']}\n"
    stats_text += f"Defense: {player_stats[user_id]['defense']}\n"
    stats_text += f"Level: {player_stats[user_id]['level']}\n"
    stats_text += f"Experience: {player_stats[user_id]['experience']}\n"
    stats_text += f"AICHX Points: {player_stats[user_id]['aichx_points']}\n"
    stats_text += f"Skill Points: {player_stats[user_id]['skill_points']}\n"
    stats_text += f"Skills:\n"
    for skill, level in player_stats[user_id]['skills'].items():
        stats_text += f"{skill.capitalize()}: Level {level} ({skills[skill]['description']})\n"
    stats_text += f"Inventory:\n"
    for item, count in player_stats[user_id]['inventory'].items():
        stats_text += f"{item.capitalize()}: {count} in inventory\n"
    
    update.message.reply_text(stats_text)

# Command: /fight (Monster Battle)
def fight(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in player_stats:
        update.message.reply_text("You need to start a game first with /start!")
        return
    
    # Choose a random monster
    monster = random.choice(monsters)
    
    # Apply any active status effects (like poison, regen)
    if 'poison' in player_stats[user_id]['status_effects']:
        poison_damage = player_stats[user_id]['status_effects']['poison']
        player_stats[user_id]['health'] -= poison_damage
        update.message.reply_text(f"You took {poison_damage} poison damage! You now have {player_stats[user_id]['health']} HP.")
    
    if 'regen' in player_stats[user_id]['status_effects']:
        regen_heal = player_stats[user_id]['status_effects']['regen']
        player_stats[user_id]['health'] += regen_heal
        update.message.reply_text(f"You healed {regen_heal} HP from regen! You now have {player_stats[user_id]['health']} HP.")

    # Battle logic
    while player_stats[user_id]['health'] > 0 and monster['health'] > 0:
        # Player's attack
        monster['health'] -= max(0, player_stats[user_id]['attack'] - monster['defense'])
        if monster['health'] <= 0:
            player_stats[user_id]['experience'] += 10
            player_stats[user_id]['aichx_points'] += 5
            player_stats[user_id]['level'] += 1
            player_stats[user_id]['skill_points'] += 1
            update.message.reply_text(f"You defeated the {monster['name']}! You gained 10 XP, 5 AICHX Points, and 1 Skill Point!")
            break

        # Monster's attack
        player_stats[user_id]['health'] -= max(0, monster['attack'] - player_stats[user_id]['defense'])
        if player_stats[user_id]['health'] <= 0:
            update.message.reply_text(f"You were defeated by the {monster['name']}... Game over!")
            break

        # Apply monster's special ability (e.g., poison, fire breath)
        if monster['ability'] == 'Poison':
            player_stats[user_id]['status_effects']['poison'] = 5  # Poison does 5 damage each turn for 3 turns
            update.message.reply_text("You have been poisoned! You will take 5 damage each turn for the next 3 turns.")
        elif monster['ability'] == 'Fire Breath':
            player_stats[user_id]['health'] -= 20  # Fire Breath does significant damage
            update.message.reply_text("You were hit by the Fire Breath! You took 20 damage.")

        # Show the battle status
        update.message.reply_text(f"Battle Status: \nYou: {player_stats[user_id]['health']} HP\n{monster['name']}: {monster['health']} HP")

# Command: /use_item (Use Items)
def use_item(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in player_stats:
        update.message.reply_text("You need to start a game first with /start!")
        return

    # Get the item name from the user's input
    item = context.args[0] if context.args else None
    if item not in items:
        update.message.reply_text(f"Invalid item! Available items: {', '.join(items.keys())}")
        return

    # Check if player has the item
    if player_stats[user_id]['inventory'].get(item, 0) > 0:
        # Apply item effect
        if item == 'health_potion':
            player_stats[user_id]['health'] += items[item]['effect']
            update.message.reply_text(f"You used a Health Potion! You healed {items[item]['effect']} HP.")
        elif item == 'attack_buff':
            player_stats[user_id]['attack'] += items[item]['effect']
            update.message.reply_text(f"You used an Attack Buff! Your attack increased by {items[item]['effect']} for this battle.")
        elif item == 'defense_buff':
            player_stats[user_id]['defense'] += items[item]['effect']
            update.message.reply_text(f"You used a Defense Buff! Your defense increased by {items[item]['effect']} for this battle.")
        
        # Decrease item count in inventory
        player_stats[user_id]['inventory'][item] -= 1
    else:
        update.message.reply_text(f"You don't have any {item}s in your inventory!")

# Command: /daily_rewards (Get daily rewards)
def daily_rewards(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    current_time = int(time.time())

    # Check if the user has claimed their daily reward
    if user_id not in last_claimed or current_time - last_claimed[user_id] > 86400:
        last_claimed[user_id] = current_time
        # Reward the player with AICHX points
        player_stats[user_id]['aichx_points'] += 10
        update.message.reply_text("You claimed your daily reward! You received 10 AICHX Points.")
    else:
        update.message.reply_text("You have already claimed your daily reward. Come back tomorrow!")

# Command: /leaderboard (View leaderboard)
def leaderboard(update: Update, context: CallbackContext) -> None:
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "Leaderboard:\n"
    for idx, (user_id, points) in enumerate(sorted_leaderboard[:10]):
        leaderboard_text += f"{idx+1}. {user_id}: {points} AICHX Points\n"
    update.message.reply_text(leaderboard_text)

# Main function to start the bot
def main() -> None:
    updater = Updater(API_TOKEN)

    # Register command handlers
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("stats", stats))
    updater.dispatcher.add_handler(CommandHandler("fight", fight))
    updater.dispatcher.add_handler(CommandHandler("use_item", use_item))
    updater.dispatcher.add_handler(CommandHandler("daily_rewards", daily_rewards))
    updater.dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
