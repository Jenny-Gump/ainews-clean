"""
Test endpoints for debugging Supabase connection
"""
from fastapi import APIRouter
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

router = APIRouter(prefix="/api/test", tags=["test"])

@router.get("/env")
async def test_env():
    """Test if environment variables are loaded"""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "KEY_EXISTS": bool(os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")),
        "ENV_PATH": str(env_path),
        "ENV_EXISTS": env_path.exists()
    }

@router.get("/supabase")
async def test_supabase():
    """Test Supabase connection and query"""
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            return {"error": "No Supabase key found", "url": url}
        
        supabase: Client = create_client(url, key)
        
        # Try to get global_last_parsed
        result = supabase.table('global_config').select('value').eq('key', 'global_last_parsed').single().execute()
        
        return {
            "success": True,
            "data": result.data,
            "value": result.data.get('value') if result.data else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "key_exists": bool(key)
        }