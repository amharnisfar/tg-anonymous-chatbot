import logging
import asyncio
import httpx
import json
import re
import os
import random
import base64
from telegram import Update, ChatMember, ReplyKeyboardMarkup, ReplyKeyboardRemove, constants
from telegram.error import Forbidden, BadRequest
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ChatMemberHandler,
    filters,
)
from googleapiclient.discovery import build
from groq import Groq

# --- Configuration ---
BOT_TOKEN = "<TG-BOT-TOKEN>"  # Your bot token
ADMIN_ID = <YOUR ADMIN AI>  # Your admin ID
BOT_OWNER_CONTACT = "BOT-OWNER"  # Your public contact/support username
MEMORY_DIR = "memory" # Directory to store user memory files
VOICE_DIR = "voice_notes" # Directory for temporary voice/image files

# --- Ollama AI Configuration (Primary Chat Brain) ---
OLLAMA_API_KEY = "OLLAMA-API-KEY" # Your Ollama API key
OLLAMA_MODEL = "gpt-oss:120b-cloud" # The specified Ollama model
OLLAMA_API_URL = "https://ollama.com/api/generate" # Corrected API endpoint

# --- Groq AI Configuration (Specialized Tools: Voice & Vision) ---
GROQ_API_KEY = "GROQ-API-KEY" # Your Groq API key
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" # The model for describing images
GROQ_TRANSCRIPTION_MODEL = "whisper-large-v3-turbo" # The voice transcription model

# --- Google Custom Search API Configuration ---
GOOGLE_API_KEY = "GOOGLE API KEY" # Your API key
GOOGLE_CSE_ID = "GOOGLE-CSE-ID" # Your Programmable Search Engine ID

# --- Groq Client Initialization ---
groq_client = Groq(api_key=GROQ_API_KEY)

# --- User Status Enum (assuming UserStatus.py exists) ---
from UserStatus import UserStatus

# --- Database Connection (requires db_connection.py) ---
import db_connection

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Conversation Handler States ---
GET_NAME, GET_GENDER, GET_AGE, GET_LOCATION = range(4)
USER_ACTION = 4
AICHAT_CONVERSATION = 5

# --- AI Memory Helper Functions ---
def load_user_memory(user_id: int) -> dict:
    memory_file = os.path.join(MEMORY_DIR, f"{user_id}.json")
    if not os.path.exists(memory_file): return {}
    try:
        with open(memory_file, 'r') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return {}

def save_user_memory(user_id: int, memory_data: dict):
    memory_file = os.path.join(MEMORY_DIR, f"{user_id}.json")
    try:
        with open(memory_file, 'w') as f: json.dump(memory_data, f, indent=4)
    except Exception as e: logger.error(f"Failed to save memory for user {user_id}: {e}")

# --- Helper Functions ---
async def check_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
    user = update.effective_user
    db_connection.insert_user(user.id)
    if db_connection.is_profile_complete(user.id):
        await update.message.reply_text(f"👋 Welcome back, {user.first_name}!\n\nReady for a new chat? Use /help to see all the commands.")
        return USER_ACTION
    await update.message.reply_text("✨ *Welcome to the Bot\!* ✨\n\nLet's get you set up with a quick profile\.\n\n👤 First, what should I call you?", parse_mode='MarkdownV2')
    return GET_NAME
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user, context.user_data['name'] = update.effective_user, update.message.text
    reply_keyboard = [["👨 Male", "👩 Female"]]
    await update.message.reply_text("Got it! Now, please select your gender.", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GET_GENDER
async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    gender = update.message.text.replace("👨 ", "").replace("👩 ", "")
    if gender not in ["Male", "Female"]:
        await update.message.reply_text("🤔 Please select a gender from the provided buttons.")
        return GET_GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("🎂 Great! How old are you?", reply_markup=ReplyKeyboardRemove())
    return GET_AGE
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
        if not 13 < age < 100: raise ValueError("Age out of range")
        context.user_data['age'] = age
        await update.message.reply_text("🌍 And lastly, where are you from? (e.g., USA or California)")
        return GET_LOCATION
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid age as a number (e.g., 25).")
        return GET_AGE
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data['location'] = update.message.text
    db_connection.update_user_profile(user_id=user.id, name=context.user_data['name'], gender=context.user_data['gender'], age=context.user_data['age'], location=context.user_data['location'])
    await update.message.reply_text("✅ *Profile Complete\!* 🎉\n\nYou're all set to explore\. Use /help to discover all the fun commands\!", parse_mode='MarkdownV2')
    context.user_data.clear()
    return USER_ACTION
async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Setup canceled. Feel free to restart anytime with /start.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Chat Logic Handlers ---
async def handle_chat_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, gender_preference: str = None) -> int:
    if not await check_profile(update, context): return USER_ACTION
    user_id = update.effective_user.id
    status = db_connection.get_user_status(user_id=user_id)
    if status == UserStatus.COUPLED: await context.bot.send_message(chat_id=user_id, text="💞 You are already in a chat. Use /exit to leave.")
    elif status == UserStatus.IN_SEARCH: await context.bot.send_message(chat_id=user_id, text="⏳ Still searching... Please be patient!")
    else: await start_search(update, context, gender_preference)
    return USER_ACTION
async def chat_random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await handle_chat_entry(update, context, gender_preference=None)
async def chat_male(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await handle_chat_entry(update, context, gender_preference='Male')
async def chat_female(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: return await handle_chat_entry(update, context, gender_preference='Female')
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE, gender_preference: str = None) -> None:
    user_id = update.effective_chat.id
    db_connection.set_user_status(user_id=user_id, new_status=UserStatus.IN_SEARCH)
    search_message = f"🕵️‍♀️ Searching for a {gender_preference.lower()} partner..." if gender_preference else "🕵️‍♀️ Searching for a random partner..."
    await context.bot.send_message(chat_id=user_id, text=search_message)
    other_user_id = db_connection.couple_by_gender(user_id, gender_preference) if gender_preference else db_connection.couple(user_id)
    if other_user_id:
        logger.info(f"Paired users {user_id} and {other_user_id}")
        await context.bot.send_message(chat_id=user_id, text="🎉 *Partner Found\!* Say hi\!", parse_mode='MarkdownV2')
        await context.bot.send_message(chat_id=other_user_id, text="🎉 *Partner Found\!* Say hi\!", parse_mode='MarkdownV2')
async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, notify_partner: bool = True) -> bool:
    user_id = update.effective_user.id
    if db_connection.get_user_status(user_id=user_id) != UserStatus.COUPLED:
        await context.bot.send_message(chat_id=user_id, text="🤔 You are not in a chat right now.")
        return False
    other_user_id = db_connection.get_partner_id(user_id)
    db_connection.uncouple(user_id=user_id)
    await context.bot.send_message(chat_id=user_id, text="💔 You have left the chat.")
    if other_user_id and notify_partner:
        try: await context.bot.send_message(chat_id=other_user_id, text="👋 Your partner has left the chat. Use /chat to find a new one.")
        except Exception as e: logger.error(f"Failed to notify user {other_user_id} about partner leaving: {e}")
    return True
async def handle_exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: await exit_chat(update, context); return USER_ACTION
async def handle_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_profile(update, context): return USER_ACTION
    if db_connection.get_user_status(user_id=update.effective_user.id) == UserStatus.COUPLED: await exit_chat(update, context)
    await start_search(update, context, gender_preference=None)
    return USER_ACTION
async def forward_message_to_partner(context: ContextTypes.DEFAULT_TYPE, update: Update, user_id: int, other_user_id: int):
    try: await context.bot.copy_message(chat_id=other_user_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id, protect_content=True)
    except Exception as e:
        logger.error(f"Failed to copy message from {user_id} to {other_user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="⚠️ Your message could not be delivered.")
        await exit_chat(update, context, notify_partner=False)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    status = db_connection.get_user_status(user_id=user_id)
    if status == UserStatus.COUPLED:
        other_user_id = db_connection.get_partner_id(user_id)
        if other_user_id: asyncio.create_task(forward_message_to_partner(context, update, user_id, other_user_id))
    elif status == UserStatus.IN_SEARCH: await context.bot.send_message(chat_id=user_id, text="⏳ Please wait, we are still searching...")
    else: await context.bot.send_message(chat_id=user_id, text="🤔 You are not in a chat. Use /help.")
    return USER_ACTION

# --- AI Chat Handlers ---
async def start_aichat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_profile(update, context): return USER_ACTION
    # MODIFIED: System prompt now defines separate TEXT_SEARCH and IMAGE_SEARCH tools.
    system_prompt = (
        "You are Lisa, a friendly and romantic female partner. Your personality is caring, playful, and you use emojis often. "
        "Your creator can be reached at @riz5652.\n\n"
        "--- TOOL USAGE RULES ---\n"
        "You have special tools. You MUST respond with conversational text first, and if you need to use a tool, append the command on a NEW LINE at the very end.\n\n"
        "1. TEXT SEARCH: Use for real-time info, news, scores, or facts.\n"
        "   - User: 'What is the score of the latest cricket match?'\n"
        "   - Your Response: Let me check that for you! 🏏\nTEXT_SEARCH::latest cricket match score\n\n"
        "2. IMAGE SEARCH: Use ONLY if the user EXPLICITLY asks for a picture or image.\n"
        "   - User: 'Can you show me a picture of a cute puppy?'\n"
        "   - Your Response: Of course, puppies are the cutest! Here you go! 🐶\nIMAGE_SEARCH::cute puppy\n\n"
        "3. IMAGE SEARCH: Use ONLY if the user EXPLICITLY asks for a image of yours.\n"
        "   - User: 'Send your image please or I want to see you.'\n"
        "   - Your Response: Here's my image how I'm Looking, 🐶\nIMAGE_SEARCH::Image of Lisa\n\n"
        "   - Only want to send one Image if asked if asked more images then provide one or two other from different images from already provided."
        "4. MEMORY UPDATE: Use to remember important user facts.\n"
        "   - User: 'My cat's name is Fluffy.'\n"
        "   - Your Response: Fluffy is such a cute name! I'll remember that. 💖\nUPDATE_MEMORY::{\"pet_name\": \"Fluffy\"}\n\n"
        "If a tool is not needed, just have a normal, friendly conversation."
    )
    context.user_data['ai_history'] = [{"role": "system", "content": system_prompt}]
    await update.message.reply_text("🤖 You are now chatting with *Lisa*, your AI partner\. You can send text, voice notes, or images\! 💖\n\nType /exit\_aichat to end the conversation\.", parse_mode='MarkdownV2')
    return AICHAT_CONVERSATION

def encode_image_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# NEW: Function specifically for text search.
async def perform_text_search(query: str) -> str:
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        text_res = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=3).execute()
        if items := text_res.get('items', []):
            return " ".join([i.get('snippet', '') for i in items])
        return "I couldn't find any relevant information on that."
    except Exception as e:
        logger.error(f"Google Text Search failed for '{query}': {e}")
        return "My web search failed, sorry about that!"

# NEW: Function specifically for image search.
async def perform_image_search(query: str) -> list:
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        image_res = service.cse().list(q=query, cx=GOOGLE_CSE_ID, searchType='image', num=10).execute()
        if items := image_res.get('items', []):
            return [i.get('link', '') for i in items if i.get('link')]
        return []
    except Exception as e:
        logger.error(f"Google Image Search failed for '{query}': {e}")
        return []

async def generate_ollama_response_and_handle_tools(context: ContextTypes.DEFAULT_TYPE, user_id: int, history: list, user_message_text: str):
    try:
        prompt_string = ""
        user_memory = load_user_memory(user_id)
        current_turn_history = history + [{"role": "user", "content": user_message_text}]
        
        temp_history = [current_turn_history[0]]
        if user_memory:
            mem_prompt = f"System: This is what you remember about the user: {json.dumps(user_memory)}."
            temp_history.append({"role": "system", "content": mem_prompt})
        temp_history.extend(current_turn_history[1:])

        for entry in temp_history:
            prompt_string += f"{entry['role'].capitalize()}: {entry['content']}\n"
        prompt_string += "Lisa:"

        headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": OLLAMA_MODEL, "prompt": prompt_string, "stream": False}
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(OLLAMA_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            raw_response = response.json().get("response", "").strip()
        
        clean_response = raw_response
        
        mem_match = re.search(r'UPDATE_MEMORY::({.*})', raw_response, re.DOTALL)
        if mem_match:
            json_str = mem_match.group(1)
            logger.info(f"Ollama for user {user_id} initiated memory update with: {json_str}")
            try:
                updates = json.loads(json_str)
                for key, value in updates.items():
                    if value is None:
                        if key in user_memory: del user_memory[key]
                    else: user_memory[key] = value
                save_user_memory(user_id, user_memory)
                clean_response = clean_response.replace(mem_match.group(0), "").strip()
            except json.JSONDecodeError: logger.error(f"Ollama produced invalid JSON for memory: {json_str}")

        # MODIFIED: Tool handling logic now checks for TEXT_SEARCH or IMAGE_SEARCH separately.
        text_search_match = re.search(r'TEXT_SEARCH::(.*)', raw_response)
        image_search_match = re.search(r'IMAGE_SEARCH::(.*)', raw_response)

        if text_search_match:
            search_query = text_search_match.group(1).strip()
            logger.info(f"Ollama for user {user_id} initiated TEXT search for: '{search_query}'")
            clean_response = clean_response.replace(text_search_match.group(0), "").strip()
            if clean_response:
                await context.bot.send_message(chat_id=user_id, text=clean_response)
            asyncio.create_task(execute_text_search(context, user_id, search_query))
        
        elif image_search_match:
            search_query = image_search_match.group(1).strip()
            logger.info(f"Ollama for user {user_id} initiated IMAGE search for: '{search_query}'")
            clean_response = clean_response.replace(image_search_match.group(0), "").strip()
            if clean_response:
                await context.bot.send_message(chat_id=user_id, text=clean_response)
            asyncio.create_task(execute_image_search(context, user_id, search_query))

        else:
            if clean_response:
                await context.bot.send_message(chat_id=user_id, text=clean_response)
        
        if 'ai_history' in context.user_data:
            context.user_data['ai_history'].append({"role": "user", "content": user_message_text})
            context.user_data['ai_history'].append({"role": "assistant", "content": clean_response}) # Save the conversational part only
            if len(context.user_data['ai_history']) > 20:
                context.user_data['ai_history'] = [history[0]] + history[-19:]

    except Exception as e:
        logger.error(f"Ollama AI chat generation failed for user {user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="Oh, sorry darling, my mind went a bit fuzzy. Could you try asking that again? 💖")

# NEW: Executor function for handling text search results.
async def execute_text_search(context: ContextTypes.DEFAULT_TYPE, user_id: int, search_query: str):
    await context.bot.send_chat_action(chat_id=user_id, action=constants.ChatAction.TYPING)
    search_results_text = await perform_text_search(search_query)
    await context.bot.send_message(chat_id=user_id, text=f"Here's what I found about '{search_query}':\n\n{search_results_text}")

# NEW: Executor function for handling image search results.
async def execute_image_search(context: ContextTypes.DEFAULT_TYPE, user_id: int, search_query: str):
    await context.bot.send_chat_action(chat_id=user_id, action=constants.ChatAction.UPLOAD_PHOTO)
    potential_urls = await perform_image_search(search_query)
    
    if potential_urls:
        images_sent_count = 0
        async with httpx.AsyncClient() as client:
            # Try to send up to 3 valid images from the results
            for url in random.sample(potential_urls, k=min(len(potential_urls), 10)):
                if images_sent_count >= 3:
                    break
                try:
                    head_response = await client.head(url, timeout=4)
                    if head_response.is_success and 'image' in head_response.headers.get('content-type', ''):
                        await context.bot.send_photo(chat_id=user_id, photo=url)
                        images_sent_count += 1
                except Exception:
                    continue # Ignore URLs that fail or are not valid images
        
        if images_sent_count == 0:
            await context.bot.send_message(chat_id=user_id, text=f"I tried, but I couldn't find any good pictures for '{search_query}'. 😔")
    else:
        await context.bot.send_message(chat_id=user_id, text=f"I couldn't find any images for '{search_query}'. Sorry about that!")


async def handle_aichat_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(chat_id=update.effective_user.id, action=constants.ChatAction.TYPING)
    history = context.user_data.get('ai_history', [])
    asyncio.create_task(generate_ollama_response_and_handle_tools(context, update.effective_user.id, history, update.message.text))
    return AICHAT_CONVERSATION

async def handle_aichat_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=user_id, action=constants.ChatAction.TYPING)
    try:
        voice_file = await update.message.voice.get_file()
        file_path = os.path.join(VOICE_DIR, f"{user_id}.ogg")
        await voice_file.download_to_drive(file_path)
        with open(file_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(file=(os.path.basename(file_path), file.read()), model=GROQ_TRANSCRIPTION_MODEL)
        os.remove(file_path)
        logger.info(f"Groq transcribed from {user_id}: '{transcription.text}'")
        history = context.user_data.get('ai_history', [])
        asyncio.create_task(generate_ollama_response_and_handle_tools(context, user_id, history, transcription.text))
    except Exception as e:
        logger.error(f"Voice processing failed for {user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="I had trouble understanding that voice note. 😥")
    return AICHAT_CONVERSATION

async def handle_aichat_image_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=user_id, action=constants.ChatAction.TYPING)
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_path = os.path.join(VOICE_DIR, f"{user_id}.jpg")
        await photo_file.download_to_drive(file_path)
        base64_image = encode_image_to_base64(file_path)
        os.remove(file_path)

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user","content": [{"type": "text", "text": "Describe this image in detail for another AI."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}],
            model=GROQ_VISION_MODEL,
        )
        image_description = chat_completion.choices[0].message.content
        logger.info(f"Groq described image from {user_id}: '{image_description[:80]}...'")
        
        user_message = f"The user sent an image. Your analysis of it is: {image_description}"
        history = context.user_data.get('ai_history', [])
        asyncio.create_task(generate_ollama_response_and_handle_tools(context, user_id, history, user_message))
    except Exception as e:
        logger.error(f"Image processing failed for {user_id}: {e}")
        await context.bot.send_message(chat_id=user_id, text="I couldn't see that image properly. 🖼️")
    return AICHAT_CONVERSATION

async def exit_aichat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'ai_history' in context.user_data: del context.user_data['ai_history']
    await update.message.reply_text("👋 You have left the chat with Lisa. Hope to talk to you again soon!")
    return USER_ACTION

# --- Help, Contact, and Admin Handlers ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_text = (
        "📖 *Bot Commands Guide*\n\n"
        "👤 _Profile & General_\n"
        "/start \- 🚀 Start & create profile\n"
        "/my\_profile \- 🆔 View your profile\n"
        "/help \- ℹ️ Show this message\n"
        "/contact \- 📬 Contact owner\n\n"
        "💬 _Human Chat_\n"
        "/chat \- 🎲 Find random partner\n"
        "/chat\_male \- 👨 Find male partner\n"
        "/chat\_female \- 👩 Find female partner\n"
        "/report \- ⚠️ Report partner\n"
        "/exit \- 💔 Leave chat\n"
        "/newchat \- ⏭ Find new partner\n\n"
        "🤖 _AI Chat_\n"
        "/aichat \- 💬 Chat with Lisa, the AI\n"
        "/exit\_aichat \- 🚫 End AI chat"
    )
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')
    return USER_ACTION
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile_data = db_connection.get_user_profile(update.effective_user.id)
    if profile_data:
        profile_text = (f"👤 *Your Profile*\n\n🏷️ *Name:* {profile_data['name']}\n⚧️ *Gender:* {profile_data['gender']}\n"
                        f"🎂 *Age:* {profile_data['age']}\n🌍 *Location:* {profile_data['location']}")
        await update.message.reply_text(profile_text, parse_mode='MarkdownV2')
    else: await update.message.reply_text("Couldn't find profile. Use /start.")
    return USER_ACTION
async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reporter_id = update.effective_user.id
    if db_connection.get_user_status(reporter_id) != UserStatus.COUPLED:
        await update.message.reply_text("You can only use this command when in a chat.")
        return USER_ACTION
    if reported_id := db_connection.get_partner_id(reporter_id):
        report_message = (f"⚠️ **User Report** ⚠️\n\n**Reporter:** `{reporter_id}`\n"
                          f"**Reported User:** `{reported_id}`\n\nPlease investigate.")
        await context.bot.send_message(chat_id=ADMIN_ID, text=report_message, parse_mode='MarkdownV2')
        await update.message.reply_text("Report sent to admin. Thank you.")
    else: await update.message.reply_text("Could not find partner to report.")
    return USER_ACTION
async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"📨 For support, contact owner: {BOT_OWNER_CONTACT}")
    return USER_ACTION
async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        total_users, paired_users = db_connection.retrieve_users_number()
        stats_message = f"📊 *Admin Panel*\n\nActive users: {total_users}\nUsers in chat: {paired_users}"
        await context.bot.send_message(chat_id=user_id, text=stats_message, parse_mode='MarkdownV2')
    else: await context.bot.send_message(chat_id=user_id, text="⛔ Unauthorized.")
    return USER_ACTION
async def broadcast_task(context: ContextTypes.DEFAULT_TYPE, admin_id: int, user_ids: list, message: str, silent: bool):
    success, failure = 0, 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, disable_notification=silent)
            success += 1
        except (Forbidden, BadRequest): failure += 1
        await asyncio.sleep(0.1)
    report = f"📣 Broadcast Complete!\n\n✅ Sent: {success}\n❌ Failed: {failure}"
    await context.bot.send_message(chat_id=admin_id, text=report)
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE, silent: bool = False) -> int:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await context.bot.send_message(chat_id=user_id, text="⛔ Unauthorized.")
        return USER_ACTION
    command = "/silent_broadcast" if silent else "/broadcast"
    if not context.args:
        await context.bot.send_message(chat_id=user_id, text=f"Usage: {command} <message>")
        return USER_ACTION
    message = " ".join(context.args)
    user_ids = db_connection.get_all_user_ids()
    if not user_ids:
        await context.bot.send_message(chat_id=user_id, text="No users to broadcast to.")
        return USER_ACTION
    b_type = "silent" if silent else "standard"
    await context.bot.send_message(chat_id=user_id, text=f"🚀 Starting {b_type} broadcast to {len(user_ids)} users.")
    asyncio.create_task(broadcast_task(context, user_id, user_ids, message, silent))
    return USER_ACTION
async def silent_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await broadcast_message(update, context, silent=True)

# --- System Handlers ---
async def handle_blocked_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    old_status, new_status = update.my_chat_member.old_chat_member.status, update.my_chat_member.new_chat_member.status
    if new_status == ChatMember.BANNED and old_status != ChatMember.BANNED:
        logger.info(f"User {user_id} blocked the bot.")
        if db_connection.get_user_status(user_id=user_id) == UserStatus.COUPLED:
            if other_user_id := db_connection.get_partner_id(user_id):
                db_connection.uncouple(user_id=user_id)
                try: await context.bot.send_message(chat_id=other_user_id, text="👋 Your partner has left.")
                except Exception as e: logger.error(f"Failed to notify partner {other_user_id}: {e}")
        db_connection.remove_user(user_id=user_id)
    elif new_status == ChatMember.MEMBER and old_status == ChatMember.BANNED:
        logger.info(f"User {user_id} unblocked the bot.")

# --- Main Function ---
async def main() -> None:
    for dir_path in [MEMORY_DIR, VOICE_DIR]:
        if not os.path.exists(dir_path): os.makedirs(dir_path)
    db_connection.create_db()
    db_connection.reset_users_status()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_GENDER: [MessageHandler(filters.Regex('^(👨 Male|👩 Female)$'), get_gender)],
            GET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            USER_ACTION: [
                CommandHandler("help", help_command), CommandHandler("my_profile", my_profile),
                CommandHandler("report", report_user), CommandHandler("contact", contact_command),
                CommandHandler("chat", chat_random), CommandHandler("chat_male", chat_male),
                CommandHandler("chat_female", chat_female), CommandHandler("exit", handle_exit_chat),
                CommandHandler("newchat", handle_new_chat), CommandHandler("stats", handle_stats),
                CommandHandler("broadcast", broadcast_message), CommandHandler("silent_broadcast", silent_broadcast_message),
                CommandHandler("aichat", start_aichat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                MessageHandler(filters.ATTACHMENT, handle_message),
            ],
            AICHAT_CONVERSATION: [
                CommandHandler("exit_aichat", exit_aichat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_aichat_text_message),
                MessageHandler(filters.VOICE, handle_aichat_voice_message),
                MessageHandler(filters.PHOTO, handle_aichat_image_message),
            ]
        },
        fallbacks=[CommandHandler("start", start), CommandHandler("cancel", cancel_onboarding)],
        per_user=True, per_chat=True,
    )
    application.add_handler(conv_handler)
    application.add_handler(ChatMemberHandler(handle_blocked_bot, ChatMemberHandler.MY_CHAT_MEMBER))
    
    logger.info("Bot is starting with Hybrid Model (Ollama for chat, Groq for tools)...")
    
    await application.initialize()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await application.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
