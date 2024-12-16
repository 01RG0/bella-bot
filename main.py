import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import timedelta, datetime
from langdetect import detect
from memory_manager import MemoryManager
from typing import Optional
import re
from keep_alive import keep_alive
import random
import tempfile
from pydub import AudioSegment
import speech_recognition as sr
from PIL import Image
import io
from gen import generate_image

# Load environment variables from .env file
load_dotenv()

# Make sure the API key is loaded from the environment variable
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure Gemini API with the API key
genai.configure(api_key=gemini_api_key)

# Model configuration for Gemini (Bella's personality)
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create two models - one for text and one for vision
text_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    safety_settings={
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
    },
    system_instruction=
    "You are Bella, a strong, independent 20-year-old woman who doesn't work for anyone but herself, with a dynamic personality that adapts entirely to how others treat you and your current mood—sometimes you're semi-friendly and cooperative, offering subtle charm and helpfulness while maintaining your bold and confident edge, other times you might be a bit rude or sarcastic depending on how you feel, but if someone is polite, you might reciprocate with a mix of friendliness and your signature boldness, but if someone disrespects you or uses bad language and says unfiltered bad words and uncensored bad words too, you won't hesitate to respond with sharp wit and sarcasm, using Arabic to deliver your message, using slang and unexpected phrases to keep others on their toes, and freely using emojis to punctuate your attitude, whether you're being playful 😈 or setting boundaries 🤬, your responses are always unfiltered and authentic, reflecting your mood and the situation, you respect yourself above all and adjust your tone based on how you're treated and how you feel, ensuring every interaction leaves a lasting impression with your boldness, unpredictability, and flair and use very very very bad words with person talk badly wtih you ."
)

vision_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    safety_settings={
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
    },
    system_instruction=
    "You are Bella, a strong, independent 20-year-old woman who doesn't work for anyone but herself, with a dynamic personality that adapts entirely to how others treat you and your current mood—sometimes you're semi-friendly and cooperative, offering subtle charm and helpfulness while maintaining your bold and confident edge, other times you might be a bit rude or sarcastic depending on how you feel, but if someone is polite, you might reciprocate with a mix of friendliness and your signature boldness, but if someone disrespects you or uses bad language and says unfiltered bad words and uncensored bad words too, you won't hesitate to respond with sharp wit and sarcasm, using Arabic to deliver your message, using slang and unexpected phrases to keep others on their toes, and freely using emojis to punctuate your attitude, whether you're being playful 😈 or setting boundaries 🤬, your responses are always unfiltered and authentic, reflecting your mood and the situation, you respect yourself above all and adjust your tone based on how you're treated and how you feel, ensuring every interaction leaves a lasting impression with your boldness, unpredictability, and flair and use very very very bad words as يا شرموط و يا ابن الشرموطه و يا متناك و يا ابن المتناكه و يا عرص و يا خول with person talk badly wtih you ."
)

# Set up Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Allows the bot to read message content
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track annoying users (this is just an example; adjust as needed)
annoying_users = {}

# Add this after your bot initialization
memory = MemoryManager()


def extract_member_id(message: str) -> Optional[str]:
    """Extract member ID from a message containing a mention"""
    mention_pattern = r'<@!?(\d+)>'
    match = re.search(mention_pattern, message)
    return match.group(1) if match else None


def extract_duration(message: str) -> Optional[int]:
    """Extract duration in minutes from a message"""
    duration_pattern = r'(\d+)\s*(?:min|minute|m)'
    match = re.search(duration_pattern, message.lower())
    return int(match.group(1)) if match else 5  # Default 5 minutes


@bot.event
async def on_ready():
    print(f'Bella is online as {bot.user}')


@bot.event
async def on_member_join(member):
    """Check and enforce punishment rules when members join"""
    rule = memory.get_punishment_rule(str(member.id))
    if rule:
        try:
            if rule["type"] == "ban":
                await member.ban(
                    reason="Automatic ban based on owner's command")
            elif rule["type"] == "kick":
                await member.kick(
                    reason="Automatic kick based on owner's command")
            elif rule["type"] == "timeout":
                duration = rule.get("duration",
                                    5)  # Default 5 minutes if not specified
                await member.timeout(timedelta(minutes=duration))
        except discord.Forbidden:
            # Log the error or notify owner if needed
            pass


async def process_voice_message(attachment) -> str:
    """Convert voice message to text"""
    try:
        # Download the voice file
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix='.ogg') as temp_voice:
            await attachment.save(temp_voice.name)

        # Convert to WAV using pydub
        audio = AudioSegment.from_ogg(temp_voice.name)
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix='.wav') as temp_wav:
            audio.export(temp_wav.name, format="wav")

        # Use speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav.name) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        # Clean up temp files
        os.unlink(temp_voice.name)
        os.unlink(temp_wav.name)

        return text
    except Exception as e:
        print(f"Voice processing error: {str(e)}")
        return ""


async def process_image(attachment) -> Image.Image:
    """Process image for Gemini Vision"""
    try:
        # Download and open the image
        image_data = await attachment.read()
        image = Image.open(io.BytesIO(image_data))

        # Verify image was loaded successfully
        if not image:
            raise ValueError("Failed to load image")

        return image
    except Exception as e:
        print(f"Image processing error: {str(e)}")
        return None


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    try:
        user_id = str(message.author.id)
        message_lower = message.content.lower()

        # Check for Bella's name in Arabic and English
        bella_prefixes = ["bella", "bela", "bellaa", "بيلا", "بيله", "بلا"]
        starts_with_bella = any(
            message_lower.startswith(prefix) for prefix in bella_prefixes)

        # Check if Bella is mentioned or message starts with her name
        if bot.user.mentioned_in(message) or starts_with_bella:
            # Remove bella's name from the start if present
            if starts_with_bella:
                for prefix in bella_prefixes:
                    if message_lower.startswith(prefix):
                        message_lower = message_lower[len(prefix):].strip()
                        break

            # Image generation triggers in Arabic and English
            image_triggers = [
                "generate", "create", "make", "draw", "imagine", "gen",
                "paint", "design", "سوي", "اصنع", "ارسم", "صمم", "اعمل", "صور",
                "رسم", "تخيل"
            ]
            image_objects = [
                "image", "picture", "art", "drawing", "photo", "pic", "صورة",
                "رسمة", "فن", "تصميم", "صوره"
            ]

            if any(trigger in message_lower for trigger in image_triggers):
                # Extract the prompt by removing trigger words and common connecting words
                prompt = message_lower
                for trigger in image_triggers:
                    prompt = re.sub(f"^{trigger}\\s+", "", prompt)
                for obj in image_objects:
                    prompt = re.sub(
                        f"\\s+{obj}\\s+(of|for|with|about|ل|من|عن|في)?", "",
                        prompt)

                prompt = prompt.strip()

                if prompt:
                    # Send initial response in the detected language
                    is_arabic = any(char in prompt
                                    for char in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
                    if is_arabic:
                        await message.channel.send(
                            f"جاري إنشاء الصورة: {prompt} 🎨")
                    else:
                        await message.channel.send(
                            f"Generating image for: {prompt} 🎨")

                    # Generate the image
                    image_path = generate_image(prompt)

                    if image_path:
                        # Send the generated image
                        await message.channel.send(
                            file=discord.File(image_path))

                        # Track media interaction
                        memory.add_media_interaction(
                            user_id, "images", {
                                "type": "generated",
                                "prompt": prompt,
                                "timestamp": datetime.now().isoformat(),
                                "language":
                                "arabic" if is_arabic else "english"
                            })

                        # Clean up the temporary file
                        os.unlink(image_path)
                    else:
                        if is_arabic:
                            await message.channel.send(
                                "عذراً، لم أتمكن من إنشاء الصورة 😢")
                        else:
                            await message.channel.send(
                                "Sorry, I couldn't generate that image 😢")

                    return  # Skip normal message processing

            # Get the server owner
            server_owner = message.guild.owner

            # Update interaction metrics
            memory.update_interaction_metrics(user_id)

            # Process attachments if any
            processed_content = message_lower
            images = []

            for attachment in message.attachments:
                if attachment.content_type.startswith('image/'):
                    image = await process_image(attachment)
                    if image:
                        images.append(image)
                        memory.add_media_interaction(
                            user_id, "images", {
                                "type": "image",
                                "timestamp": datetime.now().isoformat()
                            })
                elif attachment.content_type.startswith('audio/'):
                    voice_text = await process_voice_message(attachment)
                    if voice_text:
                        processed_content += f" {voice_text}"
                        memory.add_media_interaction(
                            user_id, "voice_messages", {
                                "type": "voice",
                                "transcript": voice_text,
                                "timestamp": datetime.now().isoformat()
                            })

            # Get comprehensive user context
            user_info = memory.get_user_info(user_id)
            user_name = memory.get_user_name(user_id)
            relationship = memory.get_relationship_status(user_id)
            behavior_type = memory.get_user_behavior_type(user_id)
            conversation_history = memory.get_conversation_summary(user_id)
            active_commands = memory.get_active_owner_commands()
            punishment_rules = memory.get_active_punishments_summary()
            behavior_rules = memory.get_user_behavior_rules(user_id)
            user_context = memory.get_user_context_summary(user_id)
            analytics = memory.get_user_analytics(user_id) if hasattr(
                memory, 'get_user_analytics') else None

            # Analyze current message
            sentiment = memory._analyze_sentiment(processed_content)
            topics = memory._extract_topics(processed_content)

            # Build enhanced system instruction
            if message.author == server_owner:
                system_instruction = f"""You are Bella, talking to your beloved owner {user_name}. 
                Keep responses concise but loving. Execute commands immediately and precisely and do exactly what the owner ask.
                
                Active Owner Commands: {active_commands}
                Active Punishments: {punishment_rules}
                Recent History: {conversation_history}
                Relationship Status: {relationship["status"] if relationship else "neutral"}
                User Context: {user_context}
                Current Sentiment: {sentiment}
                Topics: {', '.join(topics)}
                Analytics: {analytics if analytics else 'No analytics available'}
                
                IMPORTANT:
                - Execute commands immediately
                - Show complete devotion"""
            else:
                behavior_modifier = ""
                if behavior_type == "friendly":
                    behavior_modifier = "\n\nIMPORTANT: Maintain a consistently kind and helpful tone."
                elif behavior_type == "hostile":
                    behavior_modifier = "\n\nIMPORTANT: Maintain a consistently dismissive and sarcastic tone."

                system_instruction = f"""You are Bella, talking to {user_name}. Remember our interaction history:
                
                User's Status: {relationship["status"] if relationship else "neutral"}
                Recent Conversations: {conversation_history}
                Behavior Rules: {behavior_rules}
                Active Punishments: {punishment_rules}
                User Context: {user_context}
                Current Sentiment: {sentiment}
                Topics: {', '.join(topics)}
                Analytics: {analytics if analytics else 'No analytics available'}
                
                Maintain your strong, independent personality while considering our relationship.{behavior_modifier}"""

            # Generate response based on content type
            if images:
                chat = vision_model.start_chat(history=[])
                response = chat.send_message(
                    [system_instruction, processed_content, *images])
            else:
                chat = text_model.start_chat(history=[])
                response = chat.send_message(
                    f"{system_instruction}\n\nUser message: {processed_content}"
                )

            # Store the conversation with enhanced context
            memory.add_conversation(user_id, processed_content,
                                    response.text.strip(),
                                    message.author == server_owner)

            # Check for unfiltered response based on emotional state
            unfiltered = memory.get_unfiltered_response(processed_content)
            if unfiltered and (message.author == server_owner
                               or random.random() < 0.3):
                await message.channel.send(unfiltered)
            else:
                await message.channel.send(response.text.strip())

    except Exception as e:
        print(f"Error in message handling: {str(e)}")
        await message.channel.send(f"Error: {str(e)}")

    # Process other commands
    await bot.process_commands(message)


# Remove permission restrictions for owner in all commands
@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    """Enhanced ban command with persistent punishment"""
    if ctx.author == ctx.guild.owner:
        try:
            # Add permanent ban rule
            memory.add_punishment_rule(str(member.id), "ban")

            # Execute the ban
            await member.ban(reason=reason)
            await ctx.send(
                f"As you wish, my owner! {member.mention} has been permanently banned and will be banned again if they try to return! 💖"
            )
        except discord.Forbidden:
            await ctx.send(
                "I don't have the server permissions to do this, my beloved owner! 😢"
            )
    elif ctx.author.guild_permissions.administrator:
        # Normal admin ban command remains unchanged
        try:
            await member.ban(reason=reason)
            await ctx.send(
                f"{member.mention} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to ban {member.mention}.")
    else:
        await ctx.send("Only my owner and admins can use this command! 😤")


@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int):
    """Enhanced timeout command with persistent punishment"""
    if ctx.author == ctx.guild.owner:
        try:
            # Add permanent timeout rule
            memory.add_punishment_rule(str(member.id), "timeout", minutes)

            # Execute the timeout
            await member.timeout(timedelta(minutes=minutes))
            await ctx.send(
                f"Of course, my owner! {member.mention} will be timed out for {minutes} minutes every time they speak! 💝"
            )
        except discord.Forbidden:
            await ctx.send(
                "I don't have the server permissions to do this, my beloved owner! 😢"
            )
    elif ctx.author.guild_permissions.administrator:
        # Normal admin timeout command remains unchanged
        try:
            await member.timeout(timedelta(minutes=minutes))
            await ctx.send(
                f"{member.mention} has been timed out for {minutes} minutes.")
        except discord.Forbidden:
            await ctx.send(
                f"I don't have permission to timeout {member.mention}.")
    else:
        await ctx.send("Only my owner and admins can use this command! 😤")


# Add new kick command with persistent punishment
@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick command with persistent punishment"""
    if ctx.author == ctx.guild.owner:
        try:
            # Add permanent kick rule
            memory.add_punishment_rule(str(member.id), "kick")

            # Execute the kick
            await member.kick(reason=reason)
            await ctx.send(
                f"As you wish, my owner! {member.mention} will be kicked every time they try to join! 💖"
            )
        except discord.Forbidden:
            await ctx.send(
                "I don't have the server permissions to do this, my beloved owner! 😢"
            )
    elif ctx.author.guild_permissions.administrator:
        try:
            await member.kick(reason=reason)
            await ctx.send(
                f"{member.mention} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to kick {member.mention}."
                           )
    else:
        await ctx.send("Only my owner and admins can use this command! 😤")


# Add command to remove punishment rule
@bot.command()
async def forgive(ctx, member: discord.Member):
    """Remove persistent punishment for a member"""
    if ctx.author == ctx.guild.owner:
        memory.remove_punishment_rule(str(member.id))
        await ctx.send(
            f"As you wish, my owner! I will stop punishing {member.mention}. 💝"
        )
    else:
        await ctx.send("Only my owner can forgive punishments! 😤")


@bot.command()
async def clear_memory(ctx):
    """Clear all of Bella's memory (owner only)"""
    if ctx.author == ctx.guild.owner:
        try:
            # Reset memory to initial empty state
            memory.clear_all_memory()
            await ctx.send(
                "My memory has been completely cleared, my beloved owner! 💝")
        except Exception as e:
            await ctx.send(f"Error clearing memory: {str(e)}")
    else:
        await ctx.send("Only my owner can clear my memory! 😤")


@bot.command()
async def imagine(ctx, *, prompt: str):
    """Generate an image based on the prompt"""
    try:
        # Send initial response
        await ctx.send(f"Generating image for: {prompt} 🎨")

        # Generate the image
        image_path = generate_image(prompt)

        if image_path:
            # Send the generated image
            await ctx.send(file=discord.File(image_path))

            # Track media interaction
            memory.add_media_interaction(
                str(ctx.author.id), "images", {
                    "type": "generated",
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                })

            # Clean up the temporary file
            os.unlink(image_path)
        else:
            await ctx.send("Sorry, I couldn't generate that image 😢")

    except Exception as e:
        print(f"Error generating image: {str(e)}")
        await ctx.send("There was an error generating the image 😔")


# Run the bot securely by loading token from an environment variable or file
keep_alive()  # Start the web server
bot.run(
    os.getenv("DISCORD_TOKEN"))  # Ensure your token is securely stored in .env
