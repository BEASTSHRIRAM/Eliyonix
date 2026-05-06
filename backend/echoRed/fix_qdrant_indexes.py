"""
Fix Qdrant indexes for existing collections
Run this once to add village_id index to existing collections
"""
import sys
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

print("=" * 60)
print("Qdrant Index Fix")
print("=" * 60)
print()

if not QDRANT_URL:
    print("❌ ERROR: QDRANT_URL not found in .env")
    sys.exit(1)

print(f"Connecting to: {QDRANT_URL}")
print()

try:
    # Connect to Qdrant
    if "localhost" in QDRANT_URL or "127.0.0.1" in QDRANT_URL:
        client = QdrantClient(url=QDRANT_URL, timeout=30, prefer_grpc=False)
    else:
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30,
            prefer_grpc=False,
        )
    
    print("✓ Connected to Qdrant")
    print()
    
    # Get collections
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    print(f"Found {len(collection_names)} collections:")
    for name in collection_names:
        print(f"  • {name}")
    print()
    
    # Create indexes
    print("Creating payload indexes...")
    print("─" * 60)
    
    for collection_name in ["sensor_readings", "fault_history"]:
        if collection_name in collection_names:
            try:
                print(f"\n{collection_name}:")
                
                # Create village_id index
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="village_id",
                    field_schema="keyword"
                )
                print(f"  ✓ Created index on 'village_id'")
                
                # Also create timestamp index for time-based queries
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="timestamp",
                    field_schema="float"
                )
                print(f"  ✓ Created index on 'timestamp'")
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ℹ️  Indexes already exist (skipping)")
                else:
                    print(f"  ⚠️  Error: {e}")
        else:
            print(f"\n{collection_name}: Collection not found (skipping)")
    
    print()
    print("─" * 60)
    print("✓ Index creation complete!")
    print()
    print("You can now run queries with village_id filter:")
    print("  curl http://localhost:8080/recommendations/ai?village_id=KA_001")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
