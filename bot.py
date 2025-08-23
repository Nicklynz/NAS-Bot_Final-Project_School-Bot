import os, discord, PIL.Image, random, time, requests, json, base64, re, sqlite3
from discord.ext import commands
from config import api_key, TOKEN
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from typing import Optional

# Inisialisasi bot
DB_NAME = 'students.db'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Event saat bot siap
@bot.event
async def on_ready():
    print(f'Kami telah masuk sebagai {bot.user}')
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
        await ctx.send("Halo! Saya adalah bot AI untuk mengedit gambar. Kirim perintah `!edit` disertai gambar dan prompt editan.")

# Perintah !help
@bot.command(name='help')
async def help_command(ctx):
    help_text = (
        "**Panduan Bot AI Edit Gambar:**\n\n"
        "`!register <nama asli>` - Registrasi dengan username Discord dan nama asil\n"
        "`!help` - Menampilkan bantuan ini\n"
        "`!quiz <topik>` - Gunakan ini dengan menambahkan topik apapun setelah command untuk dijadikan topik quiz\n"
        "`!edit <lampiran gambar>` - Gunakan ini dengan melampirkan gambar dan memberi deskripsi edit\n\n"
        "Contoh: `!edit tambahkan efek api pada pedang`"
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


@bot.command(name="quiz")
async def quiz(ctx, *, topic:str="general", questions:int=5):
    await ctx.send(f"🎯 Membuat kuis tentang **{topic}** dengan **{questions}** soal...")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Buatkan {questions} soal kuis tentang {topic} dengan pilihan ganda.
    Jawaban hanya satu yang benar. Berikan dalam format JSON seperti ini:
    [x
      {{
        "question": "Contoh soal?",
        "options": ["Pilihan A", "Pilihan B", "Pilihan C", "Pilihan D"],
        "answer": "B" // atau bisa juga pakai isi jawaban, seperti "Mars"
      }},
      ...
    ]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(response_modalities=['TEXT'])
        )

        content = response.candidates[0].content.parts[0].text
        match = re.search(r'```json\s*\n([\s\S]+?)\n```', content)
        if not match:
            await ctx.send("❌ Tidak dapat menemukan blok JSON dari Gemini.")
            return

        quiz_data = json.loads(match.group(1).strip())

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

                # Gemini's answer may be either a letter or the actual text
                correct_answer = q["answer"]
                correct_letter = None
                correct_value = None

                if correct_answer in option_map:
                    correct_letter = correct_answer
                    correct_value = option_map[correct_letter]
                else:
                    # Try to find the correct letter by matching the value
                    for letter, value in option_map.items():
                        if value.strip().lower() == correct_answer.strip().lower():
                            correct_letter = letter
                            correct_value = value
                            break

                if user_choice_letter == correct_letter or user_choice_value.strip().lower() == correct_answer.strip().lower():
                    await ctx.send("✅ Benar!")
                else:
                    await ctx.send(f"❌ Salah! Jawaban benar: {correct_letter}. {correct_value}")

            except Exception:
                # Handle timeout
                correct_letter = correct_letter if correct_letter else "?"
                correct_value = correct_value if correct_value else correct_answer
                await ctx.send(f"⌛ Waktu habis! Jawaban yang benar adalah: {correct_letter}. {correct_value}")

    except Exception as e:
        await ctx.send(f"❌ Terjadi kesalahan saat membuat kuis: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
