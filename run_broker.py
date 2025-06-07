#!/usr/bin/env python3
"""Standalone broker script."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from brokers.broker import EcommerceBroker

def main():
    print("🏗️ Starting E-commerce Broker")
    print("=" * 40)
    
    # Use unique ports to avoid conflicts
    broker_id = "standalone_broker"
    publisher_port = 5561  # Publisher connects here
    subscriber_port = 5562  # Subscribers connect here
    
    print(f"Broker ID: {broker_id}")
    print(f"Publisher Port: {publisher_port}")
    print(f"Subscriber Port: {subscriber_port}")
    print()
    
    # Create and start broker
    broker = EcommerceBroker(broker_id, publisher_port, subscriber_port)
    broker.start()
    
    print("✅ Broker is running!")
    print("📋 Waiting for:")
    print("   - Publishers to connect on port 5561")
    print("   - Subscribers to connect on port 5562")
    print()
    print("Press Ctrl+C to stop the broker")
    print("=" * 40)
    
    try:
        # Keep running and show statistics
        while True:
            time.sleep(10)
            stats = broker.get_statistics()
            print(f"📊 Broker Stats: {stats['events_processed']} events, {stats['notifications_sent']} notifications")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping broker...")
        broker.stop()
        print("✅ Broker stopped successfully")

if __name__ == "__main__":
    main() 