from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pyrogram import Client, filters
from shivu import user_collection, collection, application
import asyncio
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
        "image_url": "https://telegra.ph/file/7959c4cb32a33ceda8077.png"
    },
    {
        "question": "In 'Dragon Ball Z', what is Goku's Saiyan name?",
        "answers": ["Vegeta", "Broly", "Kakarot", "Raditz"],
        "correct_answer": "Kakarot",
        "image_url": "https://telegra.ph/file/06f49ccbf0fda31ad8a6e.png"
    },
    {
        "question": "Who is the captain of the 'Straw Hat Pirates' in 'One Piece'?",
        "answers": ["Zoro", "Luffy", "Sanji", "Nami"],
        "correct_answer": "Luffy",
        "image_url": "https://telegra.ph/file/28219cc76de077a48d110.png"
    },
    {
        "question": "In 'Attack on Titan', who is the protagonist?",
        "answers": ["Eren Yeager", "Mikasa Ackerman", "Armin Arlert", "Levi Ackerman"],
        "correct_answer": "Eren Yeager",
        "image_url": "https://telegra.ph/file/attack-on-titan.png"  # Replace with a valid image URL
    },
    {
        "question": "Who is the main antagonist of the 'Death Note' series?",
        "answers": ["L", "Ryuk", "Light Yagami", "Misa Amane"],
        "correct_answer": "Light Yagami",
        "image_url": "https://telegra.ph/file/death-note.png"  # Replace with a valid image URL
    },
    {
        "question": "In 'My Hero Academia', what is the quirk of the main protagonist, Izuku Midoriya?",
        "answers": ["One For All", "Explosion", "Zero Gravity", "Engine"],
        "correct_answer": "One For All",
        "image_url": "https://telegra.ph/file/my-hero-academia.png"  # Replace with a valid image URL
    },
    {
        "question": "In 'Fullmetal Alchemist', what is the forbidden act Edward and Alphonse Elric performed?",
        "answers": ["Human Transmutation", "Alchemy Amplification", "Soul Binding", "Homunculus Creation"],
        "correct_answer": "Human Transmutation",
        "image_url": "https://telegra.ph/file/fullmetal-alchemist.png"  # Replace with a valid image URL
    },
    {
        "question": "What is the name of the village where Naruto Uzumaki was born?",
        "answers": ["Konoha", "Suna", "Iwa", "Kumo"],
        "correct_answer": "Konoha",
        "image_url": "https://telegra.ph/file/naruto-village.png"  # Replace with a valid image URL
    },
    {
        "question": "Who is the strongest S-Class hero in 'One Punch Man'?",
        "answers": ["Blast", "Tatsumaki", "Bang", "Genos"],
        "correct_answer": "Blast",
        "image_url": "https://telegra.ph/file/one-punch-man.png"  # Replace with a valid image URL
    },
    {
        "question": "In 'Tokyo Ghoul', what organ was transplanted into Kaneki to turn him into a ghoul?",
        "answers": ["Kidney", "Liver", "Eye", "Heart"],
        "correct_answer": "Eye",
        "image_url": "https://telegra.ph/file/tokyo-ghoul.png"  # Replace with a valid image URL
    }
    # Add more questions as needed
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
application.add_handler(CommandHandler("trivia", start_anime_quiz_cmd, block=False))
# Add callback query handler for quiz answers
application.add_handler(CallbackQueryHandler(quiz_answer_callback, pattern=r'quiz_answer_', block=False))
