import logging
import threading
import asyncio
from flask import Flask
from telegram import Update, ChatMember, ReplyKeyboardMarkup, ReplyKeyboardRemove, constants
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ChatMemberHandler,
    filters,
)
import google.generativeai as genai

# --- Configuration ---
BOT_TOKEN = "8251430379:AAGghwHur_RvFpEuq--KSpoYK3WVydkvXy8"  # Replace with your actual bot token
ADMIN_ID = 7947910185  # Replace with your actual admin ID
BOT_OWNER_CONTACT = "@nataliapersonal_bot"  # Your contact username
HEALTH_CHECK_PORT = 28142

# --- Google AI Configuration ---
GOOGLE_AI_API_KEY = "AIzaSyBeaapvBN0OjOoJxUjpHTKvPM7JUhvYZro"  # Replace with your actual key
genai.configure(api_key=GOOGLE_AI_API_KEY)

# --- User Status Enum (assuming UserStatus.py exists) ---
from UserStatus import UserStatus

# --- Database Connection (requires the updated db_connection.py) ---
import db_connection

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Flask Health Check ---
app = Flask(__name__)

@app.route("/check")
def health_check():
    return "Natalia Bot is running!"

def run_flask_app():
    app.run(host="0.0.0.0", port=HEALTH_CHECK_PORT)

# --- Conversation Handler States ---
GET_NAME, GET_GENDER, GET_AGE, GET_LOCATION = range(4)
USER_ACTION = 4
AICHAT_CONVERSATION = 5

# --- Helper Functions ---
async def check_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user has completed their profile. Returns True if complete, False otherwise."""
    user_id = update.effective_user.id
    if not db_connection.is_profile_complete(user_id):
        await update.message.reply_text(
            "❗ *Profile Incomplete* ❗\n\nPlease set up your profile first by using the /start command\.",
            parse_mode='MarkdownV2'
        )
        return False
    return True

# --- Onboarding and Core Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the bot. If new user, begins onboarding. Otherwise, shows welcome message."""
    user = update.effective_user
    db_connection.insert_user(user.id)  # Ensures user is in DB

    if db_connection.is_profile_complete(user.id):
        await update.message.reply_text(
            f"👋 Welcome back, {user.first_name}!\n\n"
            "Ready for a new chat? Use /help to see all the commands."
        )
        return USER_ACTION

    logger.info(f"User {user.id} starting onboarding.")
    await update.message.reply_text(
        "✨ *Welcome to the Bot\!* ✨\n\nLet's get you set up with a quick profile\.\n\n"
        "👤 First, what should I call you?",
        parse_mode='MarkdownV2'
    )
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's name and asks for their gender."""
    user = update.effective_user
    context.user_data['name'] = update.message.text
    logger.info(f"Name for user {user.id}: {context.user_data['name']}")

    reply_keyboard = [["👨 Male", "👩 Female"]]
    await update.message.reply_text(
        "Got it! Now, please select your gender.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return GET_GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's gender and asks for their age."""
    user = update.effective_user
    gender = update.message.text.replace("👨 ", "").replace("👩 ", "")  # Remove emoji for db
    if gender not in ["Male", "Female"]:
        await update.message.reply_text("🤔 Please select a gender from the provided buttons.")
        return GET_GENDER

    context.user_data['gender'] = gender
    logger.info(f"Gender for user {user.id}: {context.user_data['gender']}")

    await update.message.reply_text(
        "🎂 Great! How old are you?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's age and asks for their location."""
    user = update.effective_user
    age_text = update.message.text
    try:
        age = int(age_text)
        if not 13 < age < 100:
            raise ValueError("Age out of range")
        context.user_data['age'] = age
        logger.info(f"Age for user {user.id}: {age}")

        await update.message.reply_text("🌍 And lastly, where are you from? (e.g., USA or California)")
        return GET_LOCATION
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid age as a number (e.g., 25).")
        return GET_AGE

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves location, updates DB, and concludes onboarding."""
    user = update.effective_user
    context.user_data['location'] = update.message.text
    logger.info(f"Location for user {user.id}: {context.user_data['location']}")

    db_connection.update_user_profile(
        user_id=user.id,
        name=context.user_data['name'],
        gender=context.user_data['gender'],
        age=context.user_data['age'],
        location=context.user_data['location']
    )

    await update.message.reply_text(
        "✅ *Profile Complete\!* 🎉\n\nYou're all set to explore\. "
        "Use /help to discover all the fun commands\!",
        parse_mode='MarkdownV2'
    )
    context.user_data.clear()  # Clean up temporary data
    return USER_ACTION

async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the onboarding process."""
    await update.message.reply_text(
        "Setup canceled. Feel free to restart anytime with /start.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# --- Chat Logic Handlers ---

async def handle_chat_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, gender_preference: str = None) -> int:
    """Generic entry point for all human-to-human chats."""
    if not await check_profile(update, context):
        return USER_ACTION

    current_user_id = update.effective_user.id
    current_user_status = db_connection.get_user_status(user_id=current_user_id)

    if current_user_status == UserStatus.COUPLED:
        await context.bot.send_message(chat_id=current_user_id, text="💞 You are already in a chat. Use /exit to leave.")
    elif current_user_status == UserStatus.IN_SEARCH:
        await context.bot.send_message(chat_id=current_user_id, text="⏳ Still searching... Please be patient!")
    else:  # IDLE or PARTNER_LEFT
        await start_search(update, context, gender_preference)

    return USER_ACTION

async def chat_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for the generic /chat command."""
    return await handle_chat_entry(update, context, gender_preference=None)

async def chat_male(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for the /chat_male command."""
    return await handle_chat_entry(update, context, gender_preference='Male')

async def chat_female(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for the /chat_female command."""
    return await handle_chat_entry(update, context, gender_preference='Female')

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE, gender_preference: str = None) -> None:
    """Starts the partner search with an optional gender preference."""
    current_user_id = update.effective_chat.id
    db_connection.set_user_status(user_id=current_user_id, new_status=UserStatus.IN_SEARCH)

    search_message = "🕵️‍♀️ Searching for a random partner..."
    if gender_preference:
        search_message = f"🕵️‍♀️ Searching for a {gender_preference.lower()} partner..."
    await context.bot.send_message(chat_id=current_user_id, text=search_message)

    other_user_id = db_connection.couple_by_gender(current_user_id, gender_preference) if gender_preference else db_connection.couple(current_user_id)

    if other_user_id:
        logger.info(f"Paired users {current_user_id} and {other_user_id}")
        await context.bot.send_message(chat_id=current_user_id, text="🎉 *Partner Found\!* Say hi\!", parse_mode='MarkdownV2')
        await context.bot.send_message(chat_id=other_user_id, text="🎉 *Partner Found\!* Say hi\!", parse_mode='MarkdownV2')

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, notify_partner: bool = True) -> bool:
    """Exits the chat, notifies the partner, and updates user statuses."""
    current_user_id = update.effective_user.id
    if db_connection.get_user_status(user_id=current_user_id) != UserStatus.COUPLED:
        await context.bot.send_message(chat_id=current_user_id, text="🤔 You are not in a chat right now.")
        return False

    other_user_id = db_connection.get_partner_id(current_user_id)
    db_connection.uncouple(user_id=current_user_id)
    await context.bot.send_message(chat_id=current_user_id, text="💔 You have left the chat.")

    if other_user_id and notify_partner:
        try:
            await context.bot.send_message(chat_id=other_user_id, text="👋 Your partner has left the chat. Use /chat to find a new one.")
        except Exception as e:
            logger.error(f"Failed to notify user {other_user_id} about partner leaving: {e}")
    return True

async def handle_exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /exit command."""
    await exit_chat(update, context)
    return USER_ACTION

async def handle_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /newchat command."""
    if not await check_profile(update, context):
        return USER_ACTION

    user_id = update.effective_user.id
    if db_connection.get_user_status(user_id=user_id) == UserStatus.COUPLED:
        await exit_chat(update, context)

    await start_search(update, context, gender_preference=None)  # Searches for a random partner
    return USER_ACTION

async def forward_message_to_partner(context: ContextTypes.DEFAULT_TYPE, update: Update, user_id: int, other_user_id: int):
    """(TASK) Copies a message to the partner and handles potential errors."""
    try:
        await context.bot.copy_message(
            chat_id=other_user_id, from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id, protect_content=True
        )
    except Exception as e:
        logger.error(f"Failed to copy message from {user_id} to {other_user_id}: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Your message could not be delivered. Your partner may have blocked the bot or left the chat.",
        )
        # We can directly call exit_chat now since we have the update object
        await exit_chat(update, context, notify_partner=False)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles regular messages, forwarding them to the partner as a background task."""
    user_id = update.effective_user.id
    status = db_connection.get_user_status(user_id=user_id)

    if status == UserStatus.COUPLED:
        other_user_id = db_connection.get_partner_id(user_id)
        if other_user_id:
            # Run the message forwarding in a background task to avoid blocking
            asyncio.create_task(
                forward_message_to_partner(context, update, user_id, other_user_id)
            )
    elif status == UserStatus.IN_SEARCH:
        await context.bot.send_message(
            chat_id=user_id, text="⏳ Please wait, we are still searching for a partner for you."
        )
    else:  # IDLE or PARTNER_LEFT
        await context.bot.send_message(
            chat_id=user_id,
            text="🤔 You are not in a chat. Use /help to see what you can do.",
        )
    return USER_ACTION


# --- AI Chat Handlers ---

async def start_aichat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts a conversation with the AI assistant Rosi."""
    if not await check_profile(update, context):
        return USER_ACTION

    user_id = update.effective_user.id
    logger.info(f"User {user_id} started an AI chat.")
    if 'ai_history' not in context.user_data:
        context.user_data['ai_history'] = []

    await context.bot.send_message(
        chat_id=user_id,
        text="🤖 You are now chatting with *Rosi*, your AI assistant\. Ask her anything\!\n\nType /exit\_aichat to end the conversation\.",
        parse_mode='MarkdownV2'
    )
    return AICHAT_CONVERSATION

async def generate_and_send_ai_response(context: ContextTypes.DEFAULT_TYPE, user_id: int, prompt: str, user_message: str):
    """(TASK) Generates AI response using the async API and sends it to the user."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # --- MODIFIED PART: Use the async method directly ---
        response = await model.generate_content_async(prompt)
        ai_response = response.text

        # Update conversation history
        # Ensure context.user_data is still valid before modifying
        if 'ai_history' in context.user_data:
            context.user_data['ai_history'].append({"role": "User", "text": user_message})
            context.user_data['ai_history'].append({"role": "Rosi", "text": ai_response})
            # Trim history
            if len(context.user_data['ai_history']) > 20:
                context.user_data['ai_history'] = context.user_data['ai_history'][-20:]

        await context.bot.send_message(chat_id=user_id, text=f"Rosi: {ai_response}")

    except Exception as e:
        logger.error(f"AI chat generation failed for user {user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="Sorry, I couldn't process that. Please try again.")

async def handle_aichat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles messages during AI chat by creating a non-blocking background task."""
    user_id = update.effective_user.id
    user_message = update.message.text

    if GOOGLE_AI_API_KEY == "REPLACE_WITH_YOUR_GOOGLE_AI_API_KEY":
        await context.bot.send_message(chat_id=user_id, text="The AI service is not configured. Please contact the admin.")
        return AICHAT_CONVERSATION

    # Show "typing..." action immediately
    await context.bot.send_chat_action(chat_id=user_id, action=constants.ChatAction.TYPING)

    prompt = "You are Rosi, a friendly and helpful female AI assistant. Keep your answers concise and friendly.\n"
    prompt += "Below is the recent conversation history. Use this for context to make your response relevant.\n\n"
    
    for entry in context.user_data.get('ai_history', []):
        prompt += f"{entry['role']}: {entry['text']}\n"
    prompt += f"User: {user_message}"

    # Run the AI generation and sending as a background task
    asyncio.create_task(
        generate_and_send_ai_response(context, user_id, prompt, user_message)
    )

    return AICHAT_CONVERSATION


async def exit_aichat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exits the AI chat and clears the user's AI conversation history."""
    if 'ai_history' in context.user_data:
        del context.user_data['ai_history']
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="👋 You have left the chat with Rosi. Hope to talk to you again soon!",
    )
    return USER_ACTION


# --- Help, Contact, and Admin Handlers ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the beautiful help message with all commands, using MarkdownV2."""
    help_text = (
        "📖 *Bot Commands Guide*\n\n"
        "Here's everything you can do:\n\n"
        "👤 _Profile & General_\n"
        "/start \- 🚀 Start the bot & create your profile\n"
        "/help \- ℹ️ Show this help message\n"
        "/contact \- 📬 Contact the bot owner\n\n"
        "💬 _Human Chat_\n"
        "/chat \- 🎲 Find a random chat partner\n"
        "/chat\_male \- 👨 Find a male chat partner\n"
        "/chat\_female \- 👩 Find a female chat partner\n"
        "/exit \- 💔 Leave your current chat\n"
        "/newchat \- ⏭ Find a new random partner\n\n"
        "🤖 _AI Chat_\n"
        "/aichat \- 💬 Chat with Rosi, the AI\n"
        "/exit\_aichat \- 🚫 End your chat with the AI"
    )
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')
    return USER_ACTION

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the bot owner's contact information."""
    await update.message.reply_text(f"📨 For support or inquiries, please contact the bot owner: {BOT_OWNER_CONTACT}")
    return USER_ACTION

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /stats command for the admin."""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        total_users, paired_users = db_connection.retrieve_users_number()
        stats_message = (
            "📊 *Admin Panel*\n\n"
            f"Active users \(in DB\): {total_users}\n"
            f"Users in chat: {paired_users}"
        )
        await context.bot.send_message(chat_id=user_id, text=stats_message, parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(
            chat_id=user_id, text="⛔ You are not authorized to use this command."
        )
    return USER_ACTION

async def change_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allows the admin to change the Google AI API key."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await context.bot.send_message(chat_id=user_id, text="⛔ You are not authorized for this command.")
        return USER_ACTION

    try:
        new_key = context.args[0]
        global GOOGLE_AI_API_KEY
        GOOGLE_AI_API_KEY = new_key
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        logger.info(f"Admin {user_id} updated the Google AI API key.")
        await context.bot.send_message(chat_id=user_id, text="✅ Google AI API key has been updated successfully.")
    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=user_id, text="Usage: /change\_api\_key <new\_key>", parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"An error occurred: {e}")
    return USER_ACTION


# --- System Handlers ---

async def handle_blocked_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles when a user blocks or unblocks the bot."""
    user_id = update.effective_user.id
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status

    if new_status == ChatMember.BANNED and old_status != ChatMember.BANNED:
        logger.info(f"User {user_id} has blocked the bot.")
        if db_connection.get_user_status(user_id=user_id) == UserStatus.COUPLED:
            other_user_id = db_connection.get_partner_id(user_id)
            if other_user_id:
                db_connection.uncouple(user_id=user_id)
                try:
                    await context.bot.send_message(chat_id=other_user_id, text="👋 Your partner has left the chat.")
                except Exception as e:
                    logger.error(f"Failed to notify partner {other_user_id} about block: {e}")
        db_connection.remove_user(user_id=user_id)
    elif new_status == ChatMember.MEMBER and old_status == ChatMember.BANNED:
        logger.info(f"User {user_id} has unblocked the bot.")


# --- MODIFIED MAIN FUNCTION ---
async def main() -> None:
    """Sets up and runs the bot using the explicit startup sequence."""
    db_connection.create_db()
    db_connection.reset_users_status()

    health_thread = threading.Thread(target=run_flask_app, daemon=True)
    health_thread.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_GENDER: [MessageHandler(filters.Regex('^(👨 Male|👩 Female)$'), get_gender)],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            USER_ACTION: [
                CommandHandler("help", help_command),
                CommandHandler("contact", contact_command),
                CommandHandler("chat", chat_random),
                CommandHandler("chat_male", chat_male),
                CommandHandler("chat_female", chat_female),
                CommandHandler("exit", handle_exit_chat),
                CommandHandler("newchat", handle_new_chat),
                CommandHandler("stats", handle_stats),
                CommandHandler("change_api_key", change_api_key),
                CommandHandler("aichat", start_aichat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                MessageHandler(filters.ATTACHMENT, handle_message),
            ],
            AICHAT_CONVERSATION: [
                CommandHandler("exit_aichat", exit_aichat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_aichat_message),
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel_onboarding)
        ],
        per_user=True,
        per_chat=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(ChatMemberHandler(handle_blocked_bot, ChatMemberHandler.MY_CHAT_MEMBER))

    logger.info("Bot is starting...")

    # Use the more explicit startup process to avoid event loop conflicts
    await application.initialize()
    await application.updater.start_polling()
    await application.start()
    
    # Keep the script running until interrupted
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
