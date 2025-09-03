# School Discord Bot

A feature-rich Discord bot designed for educational environments, facilitating student registration, schedule management, and interactive quizzes.

## Features

### User Registration
*   Students can register themselves with a unique username using the command:
    ```
    !register <username>
    ```
*   Registered usernames are stored in a persistent database.

### Admin Schedule Management
*   Authorized administrators can set the weekly class schedule.
*   The schedule is structured using a dictionary with nested lists for organization.
*   **Example Format:**
    ```python
    {
        "Monday": [["Math", "9:00 AM"], ["Science", "11:00 AM"]],
        "Tuesday": [["History", "10:00 AM"], ["Art", "2:00 PM"]],
        # ... continues for each day
    }
    ```
*   **Command:**
    ```
    !set_schedule <admin_password> <schedule_data>
    ```
    (WARNING! Due to certain limitations on the developer's skills, the schedule provided ***MUST NOT*** include spaces aside from differentiating between the schedule itself and the secret key.)
*   Students can also show the schedule using the command:
    ```
    !schedule
    ```

### Interactive Quizzes
*   Engage students with on-demand quizzes on various topics.
*   The command allows specifying both the subject and the number of questions.
*   **Command:**
    ```
    !quiz <topic> <number_of_questions>
    ```

### Help Command
*   A comprehensive `!help` command is available to list all commands and their usage.
*   Users are automatically reminded of this command if they use a non-existent or incorrect command.

## Admin Security
All administrative commands (e.g., `!set_schedule`) require a unique password to be provided as part of the command, ensuring that only authorized users can modify critical bot settings and data.

---
