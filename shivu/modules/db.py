from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram import Client, filters
from shivu import user_collection, collection, application
import asyncios
import random
from datetime import datetime, timedelta

# Dictionary to store active quizzes
active_quizzes = {}
# Dictionary to store user cooldowns
user_cooldowns = {}

# List of anime quiz questions with possible answers
anime_questions = [
    {
        "question": "Who is the main protagonist of 'Naruto'?",
        "answers": ["Naruto Uzumaki", "Sasuke Uchiha", "Kakashi Hatake", "Sakura Haruno"],
        "correct_answer": "Naruto Uzumaki",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"
    },
    {
        "question": "In 'Dragon Ball Z', what is Goku's Saiyan name?",
        "answers": ["Vegeta", "Broly", "Kakarot", "Raditz"],
        "correct_answer": "Kakarot",
        "image_url": "https://files.catbox.moe/4i812w.jpg"
    },
    {
        "question": "Who is the captain of the 'Straw Hat Pirates' in 'One Piece'?",
        "answers": ["Zoro", "Luffy", "Sanji", "Nami"],
        "correct_answer": "Luffy",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"
    },
    {
        "question": "In 'Attack on Titan', who is the protagonist?",
        "answers": ["Eren Yeager", "Mikasa Ackerman", "Armin Arlert", "Levi Ackerman"],
        "correct_answer": "Eren Yeager",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"  # Replace with a valid image URL
    },
    {
        "question": "Who is the main antagonist of the 'Death Note' series?",
        "answers": ["L", "Ryuk", "Light Yagami", "Misa Amane"],
        "correct_answer": "Light Yagami",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'My Hero Academia', what is the quirk of the main protagonist, Izuku Midoriya?",
        "answers": ["One For All", "Explosion", "Zero Gravity", "Engine"],
        "correct_answer": "One For All",
        "image_url": "https://files.catbox.moe/4i812w.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Fullmetal Alchemist', what is the forbidden act Edward and Alphonse Elric performed?",
        "answers": ["Human Transmutation", "Alchemy Amplification", "Soul Binding", "Homunculus Creation"],
        "correct_answer": "Human Transmutation",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"  # Replace with a valid image URL
    },
    {
        "question": "What is the name of the village where Naruto Uzumaki was born?",
        "answers": ["Konoha", "Suna", "Iwa", "Kumo"],
        "correct_answer": "Konoha",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"  # Replace with a valid image URL
    },
    {
        "question": "Who is the strongest S-Class hero in 'One Punch Man'?",
        "answers": ["Blast", "Tatsumaki", "Bang", "Genos"],
        "correct_answer": "Blast",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Tokyo Ghoul', what organ was transplanted into Kaneki to turn him into a ghoul?",
        "answers": ["Kidney", "Liver", "Eye", "Heart"],
        "correct_answer": "Eye",
        "image_url": "https://files.catbox.moe/4i812w.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Bleach', who is the captain of the 13th Division?",
        "answers": ["Byakuya Kuchiki", "Ukitake Jūshirō", "Shunsui Kyōraku", "Kenpachi Zaraki"],
        "correct_answer": "Ukitake Jūshirō",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"  # Replace with a valid image URL
    },
    {
        "question": "Who is the main antagonist in 'Naruto Shippuden'?",
        "answers": ["Madara Uchiha", "Orochimaru", "Obito Uchiha", "Pain"],
        "correct_answer": "Madara Uchiha",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Hunter x Hunter', what is Killua's primary ability?",
        "answers": ["Zetsu", "Nen", "Lightning", "Enhancement"],
        "correct_answer": "Lightning",
        "image_url": "https://files.catbox.moe/4i812w.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Sword Art Online', what is Kirito's real name?",
        "answers": ["Kazuto Kirigaya", "Asuna Yuuki", "Heathcliff", "Sinon"],
        "correct_answer": "Kazuto Kirigaya",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"  # Replace with a valid image URL
    },
    {
        "question": "What is the strongest Nen category in 'Hunter x Hunter'?",
        "answers": ["Enhancement", "Transmutation", "Conjuration", "Specialization"],
        "correct_answer": "Specialization",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Demon Slayer', what is Tanjiro's primary breathing technique?",
        "answers": ["Water Breathing", "Flame Breathing", "Beast Breathing", "Wind Breathing"],
        "correct_answer": "Water Breathing",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Black Clover', what is Asta's primary weapon?",
        "answers": ["Grimoire", "Magic Staff", "Demon Slayer Sword", "Anti-Magic Bow"],
        "correct_answer": "Demon Slayer Sword",
        "image_url": "https://files.catbox.moe/4i812w.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Fate/Stay Night', who is Shirou Emiya's Servant?",
        "answers": ["Saber", "Rider", "Lancer", "Archer"],
        "correct_answer": "Saber",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Re:Zero', what is Subaru's unique ability?",
        "answers": ["Gate of Babylon", "Return by Death", "Magic Eyes", "Command Seals"],
        "correct_answer": "Return by Death",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"  # Replace with a valid image URL
    },
    {
        "question": "In 'Haikyuu!!', what position does Hinata Shoyo play?",
        "answers": ["Setter", "Libero", "Spiker", "Middle Blocker"],
        "correct_answer": "Spiker",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"  # Replace with a valid image URL
    },
    {
        "question": "What is the name of the protagonist in 'Sword Art Online'?",
        "answers": ["Kirito", "Asuna", "Heathcliff", "Sinon"],
        "correct_answer": "Kirito",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"
    },
    {
        "question": "In 'Attack on Titan', what is Levi's rank in the Survey Corps?",
        "answers": ["Captain", "Commander", "Lieutenant", "Corporal"],
        "correct_answer": "Captain",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"
    },
    {
        "question": "Who is known as the 'Hero of the Leaf' in 'Naruto'?",
        "answers": ["Minato Namikaze", "Naruto Uzumaki", "Kakashi Hatake", "Jiraiya"],
        "correct_answer": "Minato Namikaze",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"
    },
    {
        "question": "In 'Dragon Ball Super', which character achieved Ultra Instinct?",
        "answers": ["Vegeta", "Frieza", "Gohan", "Goku"],
        "correct_answer": "Goku",
        "image_url": "https://files.catbox.moe/4i812w.jpg"
    },
    {
        "question": "Who is the creator of the 'One For All' quirk in 'My Hero Academia'?",
        "answers": ["All Might", "Izuku Midoriya", "All For One", "Shigaraki"],
        "correct_answer": "All For One",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"
    },
    {
        "question": "In 'Tokyo Revengers', what is the name of Takemichi's gang?",
        "answers": ["Tokyo Manji Gang", "Black Dragons", "Valhalla", "Tenjiku"],
        "correct_answer": "Tokyo Manji Gang",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"
    },
    {
        "question": "In 'Jujutsu Kaisen', who is the strongest sorcerer?",
        "answers": ["Satoru Gojo", "Sukuna", "Megumi Fushiguro", "Yuji Itadori"],
        "correct_answer": "Satoru Gojo",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"
    },
    {
        "question": "What is the true form of the 'Beast Titan' in 'Attack on Titan'?",
        "answers": ["Eren Yeager", "Zeke Yeager", "Reiner Braun", "Bertholdt Hoover"],
        "correct_answer": "Zeke Yeager",
        "image_url": "https://files.catbox.moe/4i812w.jpg"
    },
    {
        "question": "In 'One Piece', what is the name of the sword used by Roronoa Zoro?",
        "answers": ["Shusui", "Enma", "Wado Ichimonji", "Kitetsu"],
        "correct_answer": "Wado Ichimonji",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"
    },
    {
        "question": "Who is the God of Destruction in 'Dragon Ball Super'?",
        "answers": ["Beerus", "Whis", "Zeno", "Toppo"],
        "correct_answer": "Beerus",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"
    },
    {
        "question": "In 'Fairy Tail', what type of magic does Natsu Dragneel use?",
        "answers": ["Ice-Make Magic", "Sky Dragon Slayer Magic", "Fire Dragon Slayer Magic", "Celestial Spirit Magic"],
        "correct_answer": "Fire Dragon Slayer Magic",
        "image_url": "https://files.catbox.moe/3c3c0o.jpg"
    },
    {
        "question": "In 'Steins;Gate', who is the creator of the time machine?",
        "answers": ["Okabe Rintarou", "Kurisu Makise", "Daru Hashida", "Mayuri Shiina"],
        "correct_answer": "Kurisu Makise",
        "image_url": "https://files.catbox.moe/4i812w.jpg"
    },
    {
        "question": "In 'JoJo's Bizarre Adventure', what is the name of Jotaro's Stand?",
        "answers": ["Star Platinum", "Silver Chariot", "The World", "Hermit Purple"],
        "correct_answer": "Star Platinum",
        "image_url": "https://files.catbox.moe/sbyjpl.jpg"
    },
    {
        "question": "In 'The Promised Neverland', who is the mastermind behind the escape plan?",
        "answers": ["Emma", "Ray", "Norman", "Isabella"],
        "correct_answer": "Norman",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"
    },
    {
        "question": "Who is the leader of the Phantom Troupe in 'Hunter x Hunter'?",
        "answers": ["Chrollo Lucilfer", "Hisoka", "Pakunoda", "Feitan"],
        "correct_answer": "Chrollo Lucilfer",
        "image_url": "https://files.catbox.moe/00ezy3.jpg"
    },
    {
    "question": "In 'Naruto', what is Kakashi's signature jutsu?",
    "answers": ["Chidori", "Rasengan", "Shadow Clone Jutsu", "Fireball Jutsu"],
    "correct_answer": "Chidori",
    "image_url": "https://files.catbox.moe/3c3c0o.jpg"
},
{
    "question": "In 'Dragon Ball Z', who killed Frieza on Namek?",
    "answers": ["Goku", "Vegeta", "Piccolo", "Future Trunks"],
    "correct_answer": "Future Trunks",
    "image_url": "https://files.catbox.moe/4i812w.jpg"
},
{
    "question": "In 'One Punch Man', who is Saitama's disciple?",
    "answers": ["Genos", "King", "Bang", "Fubuki"],
    "correct_answer": "Genos",
    "image_url": "https://files.catbox.moe/sbyjpl.jpg"
},
{
    "question": "In 'Attack on Titan', what is the name of the first Titan Eren fights?",
    "answers": ["Colossal Titan", "Armored Titan", "Female Titan", "Smiling Titan"],
    "correct_answer": "Smiling Titan",
    "image_url": "https://files.catbox.moe/00ezy3.jpg"
},
{
    "question": "In 'Naruto', who is the founder of the Akatsuki?",
    "answers": ["Pain", "Itachi", "Madara", "Nagato"],
    "correct_answer": "Nagato",
    "image_url": "https://files.catbox.moe/3c3c0o.jpg"
}
]

# Command handler to start the anime quiz
async def start_anime_quiz_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
        remaining_time = (user_cooldowns[user_id] - current_time).total_seconds()
        await update.message.reply_text(f"Please wait {int(remaining_time)} seconds before starting a new quiz.")
        return

    # Select a random anime question
    selected_question = random.choice(anime_questions)
    question_text = selected_question["question"]
    correct_answer = selected_question["correct_answer"]
    answers = selected_question["answers"]
    image_url = selected_question["image_url"]

    # Shuffle answers
    random.shuffle(answers)

    # Store the active quiz
    active_quizzes[user_id] = {
        'question': question_text,
        'correct_answer': correct_answer,
        'start_time': current_time
    }

    # Create buttons in a 2x2 layout
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(answers[0], callback_data=f'quiz_answer_{user_id}_{answers[0]}'), InlineKeyboardButton(answers[1], callback_data=f'quiz_answer_{user_id}_{answers[1]}')],
            [InlineKeyboardButton(answers[2], callback_data=f'quiz_answer_{user_id}_{answers[2]}'), InlineKeyboardButton(answers[3], callback_data=f'quiz_answer_{user_id}_{answers[3]}')]
        ]
    )

    # Send the question with the image
    sent_message = await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=image_url,
        caption=f"{question_text}\n\nAnswer in 15 sec.",
        reply_markup=keyboard
    )

    # Schedule timeout
    asyncio.create_task(quiz_timeout(context, user_id, sent_message.chat_id, sent_message.message_id))

# Function to handle quiz timeout
async def quiz_timeout(context: CallbackContext, user_id: int, chat_id: int, message_id: int):
    await asyncio.sleep(15)

    if user_id in active_quizzes:
        correct_answer = active_quizzes[user_id]['correct_answer']
        del active_quizzes[user_id]

        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"Time out! The correct answer was {correct_answer}."
            )
        except Exception as e:
            print(f"Failed to edit message: {e}")

# Callback handler to process the quiz answer
async def quiz_answer_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split('_')
    quiz_user_id = int(data[2])
    selected_answer = data[3]  # Selected answer

    if user_id != quiz_user_id:
        await query.answer("This quiz is not for you.", show_alert=True)
        return

    if quiz_user_id not in active_quizzes:
        await query.answer("You are not currently participating in any quiz.", show_alert=True)
        return

    correct_answer = active_quizzes[quiz_user_id]['correct_answer']

    if selected_answer == correct_answer:
        # Correct answer
        await user_collection.update_one({'id': user_id}, {'$inc': {'tokens': 80}})
        await query.message.edit_caption("Correct answer! You got 80 tokens.")
    else:
        # Incorrect answer
        await query.message.edit_caption(f"Incorrect answer. The correct answer was {correct_answer}.")

    # Remove the active quiz
    del active_quizzes[quiz_user_id]
    # Set user cooldown for 30 seconds
    user_cooldowns[quiz_user_id] = datetime.now() + timedelta(seconds=30)

# Add command handler for starting anime quiz
application.add_handler(CommandHandler("quiz", start_anime_quiz_cmd, block=False))
# Add callback query handler for quiz answers
application.add_handler(CallbackQueryHandler(quiz_answer_callback, pattern=r'quiz_answer_', block=False))
