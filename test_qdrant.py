"""Test Qdrant Cloud connection"""
from qdrant_client import QdrantClient
from app.config import settings

try:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    # Test connection
    collections = client.get_collections()
    
    print("✅ Connected to Qdrant successfully!")
    print(f"   URL: {settings.QDRANT_URL}")
    print(f"   Collections: {len(collections.collections)}")
    
    # List collections
    if collections.collections:
        print("\n   Existing collections:")
        for coll in collections.collections:
            print(f"   - {coll.name}")
    
except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
    print(f"   URL: {settings.QDRANT_URL}")
    print(f"   API Key set: {bool(settings.QDRANT_API_KEY)}")
