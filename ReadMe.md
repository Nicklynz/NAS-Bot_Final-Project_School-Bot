# School Discord Bot

A feature-rich Discord bot designed for educational environments, facilitating student registration, interactive quizzes with ranking system, and schedule management.

## Features

### User Registration & Ranking System
*   Students register with real name using: `!registration <nama>`
*   Points system: +10 points per correct quiz answer
*   Track total questions answered and correct answers
*   View personal stats with: `!rank`
*   Check leaderboard with: `!leaderboard <limit>`
*   All data stored in persistent SQLite database

### Interactive Quiz System
*   On-demand quizzes on various topics: `!quiz <topic> <number_of_questions>`
*   Multiple-choice format with 15-second response time
*   Real-time scoring and feedback
*   AI-powered question generation via OpenRouter API
*   Automatic point tracking and statistics

### Admin Schedule Management
*   Authorized administrators set weekly class schedule using JSON format
*   **Schedule Format:**
    ```python
    {
        "Monday": [["Math", "9:00 AM"], ["Science", "11:00 AM"]],
        "Tuesday": [["History", "10:00 AM"], ["Art", "2:00 PM"]],
        # ... continues for each day
    }
    ```
*   **Admin Command:** `!set_schedule <schedule_json> <admin_password>`
*   **View Command:** `!schedule`

### User ID-Based System
*   Uses Discord user IDs instead of usernames for reliability
*   Immune to username changes - all data remains intact
*   Automatic username synchronization

## Admin Security
All administrative commands require a unique password parameter to ensure only authorized users can modify critical bot settings and data.

## Help System
*   Comprehensive command listing: `!help`
*   Automatic help reminders for incorrect commands
*   Clear usage instructions and examples