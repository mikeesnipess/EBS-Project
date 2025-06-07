#!/usr/bin/env python3
"""Standalone publisher script."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from publisher.ecommerce_publisher import EcommercePublisher

def main():
    print("📢 Starting E-commerce Publisher")
    print("=" * 40)
    
    publisher_id = "standalone_publisher"
    port = 5561  # Connect to broker on port 5561
    events_per_second = 5.0
    
    print(f"Publisher ID: {publisher_id}")
    print(f"Publishing to port: {port}")
    print(f"Rate: {events_per_second} events/second")
    print()
    
    # Create and start publisher
    publisher = EcommercePublisher(publisher_id, port)
    publisher.start(events_per_second)
    
    print("✅ Publisher is running!")
    print("📋 Publishing e-commerce events:")
    print("   - Purchase events (user buys products)")
    print("   - Product view events (user browses)")
    print("   - Inventory updates (stock changes)")
    print("   - User ratings (product reviews)")
    print()
    print("Press Ctrl+C to stop the publisher")
    print("=" * 40)
    
    try:
        # Keep running and show statistics
        event_count = 0
        while True:
            time.sleep(10)
            stats = publisher.get_statistics()
            
            # Show what types of events are being generated
            events_this_period = stats['events_published'] - event_count
            event_count = stats['events_published']
            
            print(f"📊 Publisher Stats:")
            print(f"   - Total events published: {stats['events_published']}")
            print(f"   - Events last 10s: {events_this_period}")
            print(f"   - Current rate: {stats['events_per_second']:.1f} events/sec")
            print(f"   - Uptime: {stats['uptime']:.1f} seconds")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping publisher...")
        publisher.stop()
        print("✅ Publisher stopped successfully")

if __name__ == "__main__":
    main() 