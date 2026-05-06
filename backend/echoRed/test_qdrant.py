"""
Test Qdrant connection and verify setup
"""
import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

print("=" * 60)
print("Qdrant Connection Test")
print("=" * 60)
print()
print(f"URL: {QDRANT_URL}")
print(f"API Key: {QDRANT_API_KEY[:20] if QDRANT_API_KEY else 'None'}...")
print()

if not QDRANT_URL:
    print("❌ ERROR: QDRANT_URL not found in .env file")
    print()
    print("Please set QDRANT_URL in backend/echoRed/.env")
    sys.exit(1)

print("Attempting connection...")
print()

try:
    # Try to connect
    if "localhost" in QDRANT_URL or "127.0.0.1" in QDRANT_URL:
        # Local connection
        client = QdrantClient(url=QDRANT_URL, timeout=30, prefer_grpc=False)
    else:
        # Cloud connection
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30,
            prefer_grpc=False,
        )
    
    # Test connection by getting collections
    collections = client.get_collections()
    
    print("✓ Connected to Qdrant successfully!")
    print()
    print(f"Collections found: {len(collections.collections)}")
    
    if collections.collections:
        print()
        print("Existing collections:")
        for col in collections.collections:
            print(f"  • {col.name}")
            # Get collection info
            try:
                info = client.get_collection(col.name)
                print(f"    - Points: {info.points_count}")
                print(f"    - Vectors: {info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 'N/A'}")
            except Exception as e:
                print(f"    - Could not get details: {e}")
    else:
        print()
        print("No collections found yet (this is normal for first run)")
    
    print()
    print("=" * 60)
    print("✓ CONNECTION TEST PASSED")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: python generate_synthetic_data.py")
    print("  2. Run: python run_local.py")
    print()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("=" * 60)
    print("TROUBLESHOOTING")
    print("=" * 60)
    print()
    print("Possible causes:")
    print("  1. Qdrant server not running (if using local)")
    print("  2. Wrong URL or API key")
    print("  3. Network/firewall blocking connection")
    print("  4. VPN interfering with connection")
    print()
    print("Solutions:")
    print("  • For local: Run 'docker-compose up -d'")
    print("  • For cloud: Check .env credentials")
    print("  • Try different network (mobile hotspot)")
    print("  • Disable VPN temporarily")
    print()
    sys.exit(1)
