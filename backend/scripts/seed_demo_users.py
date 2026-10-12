import os
import asyncio
from supabase import create_client, Client
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def seed_users():
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("SUPABASE_SERVICE_ROLE_KEY is required to seed users. Ensure it is set in .env.")
        return

    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    demo_users = [
        {"email": "demo-a@example.com", "password": settings.DEMO_A_PASSWORD},
        {"email": "demo-b@example.com", "password": settings.DEMO_B_PASSWORD},
    ]

    for user_data in demo_users:
        try:
            print(f"Attempting to create {user_data['email']}")
            response = supabase.auth.admin.create_user(
                {
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "email_confirm": True
                }
            )
            print(f"Created user: {user_data['email']}")
        except Exception as e:
            if "already exists" in str(e).lower() or "User already registered" in str(e):
                print(f"User {user_data['email']} already exists.")
            else:
                print(f"Error creating user {user_data['email']}: {e}")

if __name__ == "__main__":
    seed_users()
