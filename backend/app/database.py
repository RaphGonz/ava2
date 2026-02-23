from supabase import create_client, Client
from app.config import settings

# Anon key client — for user-facing operations with RLS enforced
# Use this client for all user data operations; RLS policies apply based on user JWT
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

# Service role client — for admin operations that bypass RLS
# Use ONLY for server-to-server operations (e.g., webhook phone lookup)
# NEVER use for user-facing endpoints — bypasses all RLS isolation
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)
