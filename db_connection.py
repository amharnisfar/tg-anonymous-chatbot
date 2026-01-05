import sqlite3
from UserStatus import UserStatus # Make sure this import is correct

DB_FILE = "users.db"

def create_db():
    """
    Creates the database and the users table with all necessary columns
    if they don't already exist.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Using "IF NOT EXISTS" is safer
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            status INTEGER DEFAULT 0,
            partner_id INTEGER DEFAULT NULL,
            name TEXT DEFAULT NULL,
            gender TEXT DEFAULT NULL,
            age INTEGER DEFAULT NULL,
            location TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_user(user_id: int):
    """Inserts a new user into the database if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, status) VALUES (?, ?)", (user_id, UserStatus.IDLE.value))
    conn.commit()
    conn.close()

def remove_user(user_id: int):
    """Removes a user from the database (e.g., when they block the bot)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, name: str, gender: str, age: int, location: str):
    """Updates the user's profile information after onboarding."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users
        SET name = ?, gender = ?, age = ?, location = ?
        WHERE user_id = ?
    ''', (name, gender, age, location, user_id))
    conn.commit()
    conn.close()

def is_profile_complete(user_id: int) -> bool:
    """Checks if a user has completed their profile (name is a good indicator)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    # If result exists and the name (result[0]) is not None, the profile is complete.
    return result and result[0] is not None

def get_user_status(user_id: int) -> UserStatus:
    """Retrieves the current status of a user."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return UserStatus(result[0]) if result else UserStatus.IDLE

def set_user_status(user_id: int, new_status: UserStatus):
    """Sets a new status for a user."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET status = ? WHERE user_id = ?", (new_status.value, user_id))
    conn.commit()
    conn.close()

def get_partner_id(user_id: int) -> int or None:
    """Gets the ID of a user's partner."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT partner_id FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def couple(current_user_id: int) -> int or None:
    """Finds a random user in search and couples them."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Find another user who is also searching
    c.execute("SELECT user_id FROM users WHERE status = ? AND user_id != ?", (UserStatus.IN_SEARCH.value, current_user_id))
    other_user = c.fetchone()
    
    if other_user:
        other_user_id = other_user[0]
        # Update both users to be coupled with each other
        c.execute("UPDATE users SET status = ?, partner_id = ? WHERE user_id = ?", (UserStatus.COUPLED.value, other_user_id, current_user_id))
        c.execute("UPDATE users SET status = ?, partner_id = ? WHERE user_id = ?", (UserStatus.COUPLED.value, current_user_id, other_user_id))
        conn.commit()
        conn.close()
        return other_user_id
    
    conn.close()
    return None

def couple_by_gender(current_user_id: int, gender_preference: str) -> int or None:
    """Finds a user of a specific gender and couples them."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Find another user with the desired gender who is also searching
    c.execute(
        "SELECT user_id FROM users WHERE status = ? AND user_id != ? AND gender = ?",
        (UserStatus.IN_SEARCH.value, current_user_id, gender_preference)
    )
    other_user = c.fetchone()
    
    if other_user:
        other_user_id = other_user[0]
        c.execute("UPDATE users SET status = ?, partner_id = ? WHERE user_id = ?", (UserStatus.COUPLED.value, other_user_id, current_user_id))
        c.execute("UPDATE users SET status = ?, partner_id = ? WHERE user_id = ?", (UserStatus.COUPLED.value, current_user_id, other_user_id))
        conn.commit()
        conn.close()
        return other_user_id
    
    conn.close()
    return None


def uncouple(user_id: int):
    """Uncouples a user and their partner."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get partner's ID first
    c.execute("SELECT partner_id FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result and result[0]:
        partner_id = result[0]
        # Set partner's status to PARTNER_LEFT
        c.execute("UPDATE users SET status = ?, partner_id = NULL WHERE user_id = ?", (UserStatus.PARTNER_LEFT.value, partner_id))
    
    # Set current user's status to IDLE
    c.execute("UPDATE users SET status = ?, partner_id = NULL WHERE user_id = ?", (UserStatus.IDLE.value, user_id))
    
    conn.commit()
    conn.close()

def retrieve_users_number() -> (int, int):
    """Retrieves total users and paired users."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE status = ?", (UserStatus.COUPLED.value,))
    paired_users = c.fetchone()[0]
    conn.close()
    return total_users, paired_users

def reset_users_status():
    """Resets all users' status to IDLE on bot restart for a clean state."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET status = ?, partner_id = NULL", (UserStatus.IDLE.value,))
    conn.commit()
    conn.close()

# --- NEW FUNCTIONS ADDED BELOW ---

def get_user_profile(user_id: int) -> dict or None:
    """Retrieves a user's full profile from the database for the /my_profile command."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, gender, age, location FROM users WHERE user_id = ?", (user_id,))
    profile = c.fetchone()
    conn.close()
    if profile:
        return {
            "name": profile[0],
            "gender": profile[1],
            "age": profile[2],
            "location": profile[3],
        }
    return None

def get_all_user_ids() -> list:
    """Retrieves a list of all user IDs from the database for broadcast commands."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    # The result of fetchall is a list of tuples, e.g., [(123,), (456,)]
    # We extract the first element from each tuple to get a simple list of IDs.
    user_ids = [item[0] for item in c.fetchall()]
    conn.close()
    return user_ids
