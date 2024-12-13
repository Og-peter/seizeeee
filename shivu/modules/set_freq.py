from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from shivu import application, OWNER_ID, user_totals_collection,settings_collection

async def get_frequency():
    setting = await settings_collection.find_one({"setting": "frequency"})
    if setting:
        return setting["value"]
    else:
        # Default frequency value if not set
        return 10

async def set_frequency(new_frequency):
    await settings_collection.update_one(
        {"setting": "frequency"},
        {"$set": {"value": new_frequency}},
        upsert=True
    )


async def change_freq(update: Update, context: CallbackContext) -> None:
    sudo_user_ids = {6835013483}
    user = update.effective_user

    try:
        if user.id not in sudo_user_ids:
            await update.message.reply_text('You do not have permission to use this command.')
            return

        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /changetime NUMBER')
            return

        new_frequency = int(args[0])
        if new_frequency < 1:
            await update.message.reply_text('The message frequency must be greater than or equal to 1.')
            return

        if new_frequency > 10000:
            await update.message.reply_text('Thats too much buddy. Use below 10000')
            return

        try:
            await set_frequency(new_frequency)
            await update.message.reply_text(f'Successfully changed character appearance frequency to every {new_frequency} messages.')
        except Exception as e:
            await update.message.reply_text('Failed to change character appearance frequency.')

    except Exception as e:
        await update.message.reply_text('Failed to change character appearance frequency.')


application.add_handler(CommandHandler("cfreq", change_freq, block=False))
