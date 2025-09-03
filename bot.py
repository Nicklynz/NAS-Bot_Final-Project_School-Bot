import os, discord, PIL.Image, random, time, requests, json, base64, re, sqlite3, ast, asyncio # godD**N the amount of f****n' libraries
from discord.ext import commands
from discord.ui import Modal, TextInput
from config import api_key, TOKEN, openrouter_api_key
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from typing import Optional

# Inisialisasi bot
DB_NAME = 'students.db'
secret_key = 'OSHARE' # Admins should modify this variable to add a secret key for the admin commands
global real_schedule
real_schedule = None
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

class ScheduleModal(Modal, title="Set Schedule"):
    def __init__(self, key: str):
        super().__init__()
        self.key = key
        self.schedule_input = TextInput(
            label="Schedule Data",
            placeholder='Masukkan data jadwal (e.g., {"monday": ["Science", "Math"], dst...})',
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.schedule_input)

    async def on_submit(self, interaction: discord.Interaction):
        global real_schedule
        if self.key != secret_key:
            await interaction.response.send_message("Invalid key!", ephemeral=True)
            return
        
        try:
            real_schedule = ast.literal_eval(self.schedule_input.value)
            await interaction.response.send_message("Schedule updated successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error parsing schedule: {str(e)}", ephemeral=True)

# Event saat bot siap
@bot.event
async def on_ready():
    print(f'Kami telah masuk sebagai {bot.user}')
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                username TEXT PRIMARY KEY,
                real_name TEXT NOT NULL,
            )
        ''')
        conn.commit()
        conn.close()

# Perintah !start
@bot.command(name='start')
async def start(ctx):
    async with ctx.typing():
        await ctx.send("Halo! Saya adalah bot AI")

# Perintah !help
@bot.command(name='help')
async def help_command(ctx):
    help_text = (
        "**Panduan Bot AI Edit Gambar:**\n\n"
        "`!register <nama asli>` - Registrasi dengan username Discord dan nama asil\n"
        "`!help` - Menampilkan bantuan ini\n"
        "`!quiz <topik> <number of questions>` - Gunakan ini dengan menambahkan topik apapun setelah command untuk dijadikan topik quiz"
        "`!set_schedule <jadwal:json> <kunci rahasia>` - Menentukan jadwal (Pastikan tidak ada spasi untuk JSON jadwalnya)"
        "`!schedule` - Gunakan ini untuk menampilkan jadwal harian"
    )
    async with ctx.typing():
        await ctx.send(help_text)

@bot.command(name='registration')
async def register(ctx, real_name:str):
    if real_name == '': pass
    username = ctx.author.name
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Temporarily empty, dunno what to add
        cursor.execute('''
            empty
            )
        ''')
        conn.commit()
        conn.close()

@bot.command(name="set_schedule")
async def set_schedule(ctx, key: str):
    modal = ScheduleModal(key)
    await ctx.send_modal(modal)

@bot.command(name='schedule')
async def schedule(ctx):
    # Build the entire schedule message first
    schedule_message = "Jadwal minggu ini:\n\n"
    
    for days in real_schedule:
        subjects = '\n'.join([f'  {i+1}. {subject}' for i, subject in enumerate(real_schedule[days])])
        print(f'- {days}:\n{subjects}')
        schedule_message += f'- {days}:\n{subjects}\n\n'
    
    # Send the complete schedule as a single ephemeral message
    await ctx.send(schedule_message, ephemeral=True)

@bot.command(name="quiz")
async def quiz(ctx, topic:str="general", questions:int=5):
    await ctx.send(f"🎯 Membuat kuis tentang **{topic}** dengan **{questions}** soal...")

    prompt = f"""
    Buatkan {questions} soal kuis tentang {topic} dengan pilihan ganda.
    Jawaban hanya satu yang benar. Berikan dalam format JSON seperti ini:
    [
      {{
        "question": "Contoh soal?",
        "options": ["Pilihan A", "Pilihan B", "Pilihan C", "Pilihan D"],
        "answer": "B" // atau bisa juga pakai isi jawaban, seperti "Mars"
      }},
      ...
    ]
    Hanya kembalikan JSON saja tanpa penjelasan tambahan.
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "tngtech/deepseek-r1t2-chimera:free", 
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 128000,
                "type": "json_object"
            })
        )

        # Check if request was successful
        if response.status_code != 200:
            await ctx.send(f"❌ Error dari API: {response.status_code} - {response.text}")
            return

        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        # Extract JSON from the response (handle both with and without code blocks)
        match = re.search(r'```json\s*\n([\s\S]+?)\n```', content)
        if match:
            json_content = match.group(1).strip()
        else:
            # If no code blocks found, try to parse the entire content as JSON
            json_content = content.strip()
        
        quiz_data = json.loads(json_content)

        for i, q in enumerate(quiz_data):
            options = q["options"]
            option_map = {chr(65 + idx): opt for idx, opt in enumerate(options)}  # {'A': '...', 'B': '...', ...}
            question_text = f"**Soal {i+1}:** {q['question']}\n" + "\n".join([f"{key}. {val}" for key, val in option_map.items()])
            await ctx.send(f"{question_text}\n\n*Ketik A/B/C/D untuk menjawab (15 detik)*")

            def check(m):
                return (
                    m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content.upper() in option_map
                )

            try:
                msg = await bot.wait_for("message", timeout=15.0, check=check)
                user_choice_letter = msg.content.upper()
                user_choice_value = option_map[user_choice_letter]

                # Handle different answer formats
                correct_answer = q["answer"]
                correct_letter = None
                correct_value = None

                # If answer is a letter (A, B, C, D)
                if correct_answer.upper() in option_map:
                    correct_letter = correct_answer.upper()
                    correct_value = option_map[correct_letter]
                else:
                    # If answer is the text content, find the corresponding letter
                    for letter, value in option_map.items():
                        if value.strip().lower() == correct_answer.strip().lower():
                            correct_letter = letter
                            correct_value = value
                            break
                    # If still not found, use the original answer
                    if correct_letter is None:
                        correct_letter = "?"
                        correct_value = correct_answer

                if (user_choice_letter == correct_letter or 
                    user_choice_value.strip().lower() == correct_answer.strip().lower()):
                    await ctx.send("✅ Benar!")
                else:
                    await ctx.send(f"❌ Salah! Jawaban benar: {correct_letter}. {correct_value}")

            except asyncio.TimeoutError:
                await ctx.send(f"⌛ Waktu habis! Jawaban yang benar adalah: {correct_letter if correct_letter else '?'}. {correct_value if correct_value else correct_answer}")
            except Exception as e:
                await ctx.send(f"❌ Error: {str(e)}")

    except json.JSONDecodeError:
        await ctx.send("❌ Tidak dapat memparse respons JSON dari API")
    except KeyError as e:
        await ctx.send(f"❌ Format respons API tidak sesuai: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    bot.run(TOKEN)
