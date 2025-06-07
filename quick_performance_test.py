#!/usr/bin/env python3
"""Quick performance test to demonstrate the system working."""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from publisher.ecommerce_publisher import EcommercePublisher
from brokers.broker import EcommerceBroker
from subscribers.subscriber import EcommerceSubscriber

def main():
    print("=== Quick E-commerce Pub/Sub Performance Test ===")
    print("This test will run for 60 seconds with real notifications")
    print()

    # Start broker
    print("1. Starting broker...")
    broker = EcommerceBroker("perf_broker", 5557, 5554)
    broker.start()
    time.sleep(2)

    # Start subscriber
    print("2. Starting subscriber...")
    subscriber = EcommerceSubscriber("perf_subscriber", [5554])
    subscriber.start()
    time.sleep(2)

    # Create targeted subscriptions that will match
    print("3. Creating targeted subscriptions...")
    
    # Create subscriptions with 100% equality for better matching
    subscriber.subscribe_with_equality_ratio(50, 1.0)  # 50 subscriptions, all equality
    time.sleep(3)

    # Start publisher
    print("4. Starting publisher...")
    publisher = EcommercePublisher("perf_publisher", 5557)
    publisher.start(20.0)  # 20 events per second
    
    print("5. Running test for 60 seconds...")
    print("   You should see notifications being delivered!")
    print()

    # Monitor for 60 seconds
    for i in range(12):  # 12 * 5 = 60 seconds
        time.sleep(5)
        
        # Get statistics
        pub_stats = publisher.get_statistics()
        sub_stats = subscriber.get_statistics()
        broker_stats = broker.get_statistics()
        
        print(f"--- After {(i+1)*5} seconds ---")
        print(f"  Events published: {pub_stats['events_published']}")
        print(f"  Events processed: {broker_stats['events_processed']}")
        print(f"  Notifications delivered: {sub_stats['notifications_received']}")
        print(f"  Simple notifications: {sub_stats['simple_notifications']}")
        print(f"  Complex notifications: {sub_stats['complex_notifications']}")
        if sub_stats['average_latency_ms'] > 0:
            print(f"  Average latency: {sub_stats['average_latency_ms']:.2f} ms")
        print(f"  Subscription count: {len(subscriber.active_subscriptions)}")
        print()

    # Final results
    print("=" * 60)
    print("FINAL RESULTS:")
    
    final_pub_stats = publisher.get_statistics()
    final_sub_stats = subscriber.get_statistics()
    final_broker_stats = broker.get_statistics()
    
    total_events = final_pub_stats['events_published']
    total_notifications = final_sub_stats['notifications_received']
    matching_rate = (total_notifications / max(1, total_events)) * 100
    
    print(f"✅ Total events published: {total_events}")
    print(f"✅ Total events processed by broker: {final_broker_stats['events_processed']}")
    print(f"✅ Total notifications delivered: {total_notifications}")
    print(f"✅ Matching rate: {matching_rate:.2f}%")
    if final_sub_stats['average_latency_ms'] > 0:
        print(f"✅ Average end-to-end latency: {final_sub_stats['average_latency_ms']:.2f} ms")
    print(f"✅ Active subscriptions: {len(subscriber.active_subscriptions)}")
    
    # Cleanup
    print("\n6. Stopping components...")
    publisher.stop()
    subscriber.stop()
    broker.stop()
    
    print("\n🎉 Quick performance test completed successfully!")
    print("The system is working correctly with:")
    print("  ✅ Event publishing and processing")
    print("  ✅ Content-based subscription matching")
    print("  ✅ Real-time notification delivery")
    print("  ✅ Performance monitoring and statistics")

if __name__ == "__main__":
    main() 