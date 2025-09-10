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
secret_key = 'pass123' # Admin sebaiknya mengubah variabel ini sesuai kebutuhannya
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
            placeholder='Enter schedule data (e.g., {"monday": ["math", "science"]})',
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
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                real_name TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                total_answered INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

# Perintah !start
@bot.command(name='start')
async def start(ctx):
    async with ctx.typing():
        await ctx.send("Halo! Saya adalah bot AI pembantu belajar!\nGunakan `!help` untuk melihat panduan!" , ephemeral=True)

# Perintah !help
@bot.command(name='help')
async def help_command(ctx):
    help_text = (
        "**Panduan Bot AI Quiz System:**\n\n"
        "**📝 Registrasi & Profil:**\n"
        "`!registration <nama>` - Registrasi dengan nama asli\n"
        "`!rank` - Lihat ranking dan statistik pribadi\n"
        "`!leaderboard <limit>` - Lihat leaderboard top pemain (default: 10)\n\n"
        "**🎯 Kuis & Game:**\n"
        "`!quiz <topik> <jumlah_soal>` - Mulai kuis dengan topik tertentu\n"
        "   Contoh: `!quiz matematika 5` atau `!quiz sejarah 10`\n\n"
        "**📅 Jadwal:**\n"
        "`!set_schedule <kunci_rahasia>` - Set jadwal (admin only)\n"
        "`!schedule` - Lihat jadwal minggu ini\n\n"
        "**ℹ️ Lainnya:**\n"
        "`!help` - Menampilkan bantuan ini\n\n"
        "**📊 Sistem Poin:**\n"
        "• +10 poin untuk setiap jawaban benar\n"
        "• Statistik akurasi dicatat\n"
        "• Leaderboard berdasarkan total poin\n\n"
        "**💡 Tips:**\n"
        "• Gunakan `!register` dulu sebelum main kuis\n"
        "• Jawab dengan huruf A/B/C/D dalam 15 detik\n"
        "• Cek `!rank` untuk lihat progress belajar kamu!\n"
        "• Usahakan tidak ada spasi untuk setiap parameter!"
    )
    await ctx.send(help_text, ephemeral=True)

@bot.command(name='registration')
async def register(ctx, real_name: str):
    if real_name == '':
        await ctx.send("Tolong berikan nama aslimu! Command: `!registration <nama>`", ephemeral=True)
        return
    
    username = ctx.author.name
    user_id = ctx.author.id
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO students (user_id, username, real_name, points, total_correct, total_answered)
                VALUES (?, ?, ?, 0, 0, 0)
            ''', (user_id, username, real_name))
            
            conn.commit()
            await ctx.send(f"Registrasi Behrasil! Selamat datang {real_name} ({username})!", ephemeral=True)
            
        except sqlite3.IntegrityError:
            # If user already exists, update their real name (in case they want to change it)
            cursor.execute('''
                UPDATE students SET real_name = ? WHERE username = ?
            ''', (real_name, username))
            
            conn.commit()
            await ctx.send(f"Profilmu telah diperbarui! Nama asli diganti ke: {real_name}", ephemeral=True)

@bot.command(name="set_schedule")
async def set_schedule(ctx, key: str):
    class ScheduleView(discord.ui.View):
        def __init__(self, key: str):
            super().__init__()
            self.key = key
            
        @discord.ui.button(label="Set Schedule", style=discord.ButtonStyle.primary)
        async def set_schedule_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = ScheduleModal(self.key)
            await interaction.response.send_modal(modal)
    
    view = ScheduleView(key)
    await ctx.send("Pencet tombol dibawah untuk melihat jadwal:", ephemeral=True, view=view)

@bot.command(name='schedule')
async def schedule(ctx):
    schedule_message = "Jadwal minggu ini:\n"
    
    for days in real_schedule:
        subjects = '\n'.join([f'  {i+1}. {subject}' for i, subject in enumerate(real_schedule[days])])
        print(f'- {days}:\n{subjects}')
        schedule_message += f'- {days}:\n{subjects}\n'
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
                "model": "deepseek/deepseek-chat-v3.1:free", 
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

        if response.status_code != 200:
            await ctx.send(f"❌ Error dari API: {response.status_code} - {response.text}")
            return

        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        
        match = re.search(r'```json\s*\n([\s\S]+?)\n```', content)
        if match:
            json_content = match.group(1).strip()
        else:
            json_content = content.strip()
        
        quiz_data = json.loads(json_content)

        total_correct = 0
        total_answered = 0
        points_earned = 0
        user_id = ctx.author.id
        username = ctx.author.name

        for i, q in enumerate(quiz_data):
            options = q["options"]
            option_map = {chr(65 + idx): opt for idx, opt in enumerate(options)}
            question_text = f"**Soal {i+1}:** {q['question']}\n" + "\n".join([f"{key}. {val}" for key, val in option_map.items()])
            await ctx.send(f"{question_text}\n\n*Ketik A/B/C/D untuk menjawab (15 detik)*", ephemeral=True)

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

                correct_answer = q["answer"]
                correct_letter = None
                correct_value = None

                if correct_answer.upper() in option_map:
                    correct_letter = correct_answer.upper()
                    correct_value = option_map[correct_letter]
                else:
                    for letter, value in option_map.items():
                        if value.strip().lower() == correct_answer.strip().lower():
                            correct_letter = letter
                            correct_value = value
                            break
                    if correct_letter is None:
                        correct_letter = "?"
                        correct_value = correct_answer

                total_answered += 1

                is_correct = False
                if (user_choice_letter == correct_letter or 
                    user_choice_value.strip().lower() == correct_answer.strip().lower()):
                    total_correct += 1
                    points_earned += 10
                    is_correct = True
                    await ctx.send("✅ Benar! +10 poin!", ephemeral=True)
                else:
                    await ctx.send(f"❌ Salah! Jawaban benar: {correct_letter}. {correct_value}", ephemeral=True)

                await update_user_stats(user_id, username, points_earned_per_question=10 if is_correct else 0, 
                                      is_correct=is_correct)

            except asyncio.TimeoutError:
                total_answered += 1
                await ctx.send(f"⌛ Waktu habis! Jawaban yang benar adalah: {correct_letter if correct_letter else '?'}. {correct_value if correct_value else correct_answer}")
                await update_user_stats(user_id, username, points_earned_per_question=0, is_correct=False)
            except Exception as e:
                await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)

        accuracy = (total_correct / total_answered * 100) if total_answered > 0 else 0
        await ctx.send(f"🎯 **Kuis selesai!**\n"
                      f"✅ Benar: {total_correct}/{total_answered}\n"
                      f"📊 Akurasi: {accuracy:.1f}%\n"
                      f"⭐ Poin diperoleh: {points_earned}\n"
                      f"💰 Total poin: {await get_user_points(user_id)}", ephemeral=True)

    except json.JSONDecodeError:
        await ctx.send("❌ Tidak dapat memparse respons JSON dari API")
    except KeyError as e:
        await ctx.send(f"❌ Format respons API tidak sesuai: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


async def update_user_stats(user_id, username, points_earned_per_question=0, is_correct=False):
    """Update user statistics in the database using user_id"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT user_id FROM students WHERE user_id = ?', (user_id,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            # Create new user record
            cursor.execute('''
                INSERT INTO students (user_id, username, real_name, points, total_correct, total_answered)
                VALUES (?, ?, 'Unknown', 0, 0, 0)
            ''', (user_id, username))
        
        # Update user statistics
        cursor.execute('''
            UPDATE students SET 
                points = points + ?,
                total_correct = total_correct + ?,
                total_answered = total_answered + 1,
                username = ?  # Update username in case it changed
            WHERE user_id = ?
        ''', (points_earned_per_question, 1 if is_correct else 0, username, user_id))
        
        conn.commit()

async def get_user_points(user_id):
    """Get user's current total points using user_id"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT points FROM students WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

@bot.command(name='rank')
async def rank(ctx):
    """Show user's current rank and stats using user_id"""
    user_id = ctx.author.id
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, real_name, points, total_correct, total_answered 
            FROM students WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result:
            username, real_name, points, correct, answered = result
            accuracy = (correct / answered * 100) if answered > 0 else 0
            await ctx.send(f"📊 **Stats {real_name}:**\n"
                          f"⭐ Poin: {points}\n"
                          f"✅ Benar: {correct}/{answered}\n"
                          f"🎯 Akurasi: {accuracy:.1f}%", ephemeral=True)
        else:
            await ctx.send("Kamu belum terdaftar! Gunakan `!registration <nama>`", ephemeral=True)

@bot.command(name='leaderboard')
async def leaderboard(ctx, limit: int = 10):
    """Show top ranking users"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT real_name, points 
            FROM students 
            ORDER BY points DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        
        leaderboard_text = "🏆 **Leaderboard:**\n"
        for i, (real_name, points) in enumerate(results, 1):
            leaderboard_text += f"{i}. {real_name} - {points} poin\n"
        
        await ctx.send(leaderboard_text, ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
