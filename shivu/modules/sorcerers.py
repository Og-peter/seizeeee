from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaVideo
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from shivu import application, GRADE4, GRADE3, GRADE2, GRADE1, SPECIALGRADE

# Grade database
grades = {
    "Special grade": {
        "users": SPECIALGRADE,
        "video_url": "https://files.catbox.moe/0noa8s.mp4"
    },
    "Grade 1": {
        "users": GRADE1,
        "video_url": "https://files.catbox.moe/0o1307.mp4"
    },
    "Grade 2": {
        "users": GRADE2,
        "video_url": "https://files.catbox.moe/75cts9.mp4"
    },
    "Grade 3": {
        "users": GRADE3,
        "video_url": "https://files.catbox.moe/4hdn74.mp4"
    },
    "Grade 4": {
        "users": GRADE4,
        "video_url": "https://files.catbox.moe/4hdn74.mp4"
    },
}

# Helper: Verify if user is Special Grade
def is_special_grade(user_id):
    return user_id in grades["Special grade"]["users"]

# Command to add a user to a grade
async def add_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_special_grade(user_id):
        await update.message.reply_text("❌ Only Special Grade users can use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addgrade <user_id> <grade>")
        return

    target_user_id = int(context.args[0])
    grade = " ".join(context.args[1:]).title()

    if grade not in grades:
        await update.message.reply_text("❌ Invalid grade. Available grades: Special Grade, Grade 1, Grade 2, Grade 3, Grade 4.")
        return

    # Remove the user from all other grades
    for g in grades.values():
        if target_user_id in g["users"]:
            g["users"].remove(target_user_id)

    # Add to the specified grade
    grades[grade]["users"].append(target_user_id)
    await update.message.reply_text(f"✅ User with ID {target_user_id} added to {grade}.")

# Command to remove a user from all grades
async def remove_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_special_grade(user_id):
        await update.message.reply_text("❌ Only Special Grade users can use this command.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /remgrade <user_id>")
        return

    target_user_id = int(context.args[0])

    # Remove the user from all grades
    removed = False
    for g in grades.values():
        if target_user_id in g["users"]:
            g["users"].remove(target_user_id)
            removed = True

    if removed:
        await update.message.reply_text(f"✅ User with ID {target_user_id} removed from all grades.")
    else:
        await update.message.reply_text(f"❌ User with ID {target_user_id} not found in any grade.")

# Command to list sorcerers (same as before)
async def list_sorcerers(update, context, grade="Special grade"):
    response = f"<b><u>{get_grade_display(grade)}</u></b>\n\n"
    for user_id in grades[grade]["users"]:
        try:
            user = await context.bot.get_chat(user_id)
            user_full_name = user.first_name
            if user.last_name:
                user_full_name += f" {user.last_name}"
            user_link = f'<a href="tg://user?id={user_id}">{user_full_name}</a>'
            response += f"├─➩ {user_link}\n"
        except Exception as e:
            response += f"├─➩ User not found (ID: {user_id})\n"
    response += "╰──────────\n\n"

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="navigate:prev"),
            InlineKeyboardButton("➡️", callback_data="navigate:next")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        media = InputMediaVideo(media=grades[grade]["video_url"], caption=response, parse_mode=ParseMode.HTML)
        await update.callback_query.edit_message_media(
            media=media,
            reply_markup=reply_markup
        )
        await update.callback_query.answer()
    else:
        await update.message.reply_video(
            video=grades[grade]["video_url"],
            caption=response,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

# Command navigation (same as before)
async def navigate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.message is None:
        await query.answer("No message to navigate.")
        return

    current_caption = query.message.caption_html or query.message.caption
    if current_caption is None:
        await query.answer("No caption found in the message.")
        return

    current_grade = next((grade for grade in grades if get_grade_display(grade) in current_caption), None)
    
    if current_grade is None:
        await query.answer("Could not determine current grade.")
        return

    grades_list = list(grades.keys())
    current_index = grades_list.index(current_grade)
    
    if query.data == "navigate:next":
        new_index = (current_index + 1) % len(grades_list)
    else:  # prev
        new_index = (current_index - 1) % len(grades_list)
    
    new_grade = grades_list[new_index]
    await list_sorcerers(update, context, new_grade)

# Add handlers to application
application.add_handler(CommandHandler("sorcerers", list_sorcerers))
application.add_handler(CommandHandler("addgrade", add_grade))
application.add_handler(CommandHandler("remgrade", remove_grade))
application.add_handler(CallbackQueryHandler(navigate, pattern=r"^navigate:(prev|next)$"))
