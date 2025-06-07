#!/usr/bin/env python3
"""Simple demo to show the system working without port conflicts."""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🎉 E-commerce Publish/Subscribe System Demo")
    print("=" * 50)
    print("This demo shows all components working together!")
    print()

    # Import here to avoid issues
    from publisher.ecommerce_publisher import EcommercePublisher
    from brokers.broker import EcommerceBroker
    from subscribers.subscriber import EcommerceSubscriber

    print("1. 🏗️  Starting Broker...")
    broker = EcommerceBroker("demo_broker", 5559, 5560)  # Use different ports
    broker.start()
    time.sleep(2)
    print("   ✅ Broker running on ports 5559 (publisher) and 5560 (subscriber)")

    print("\n2. 👥 Starting Subscriber...")
    subscriber = EcommerceSubscriber("demo_subscriber", [5560])
    subscriber.start()
    time.sleep(2)
    print("   ✅ Subscriber connected")

    print("\n3. 📝 Creating 10 subscriptions...")
    subscriber.subscribe_with_equality_ratio(10, 1.0)  # 10 subscriptions with 100% equality
    time.sleep(3)
    print("   ✅ 10 subscriptions registered")

    print("\n4. 📢 Starting Publisher...")
    publisher = EcommercePublisher("demo_publisher", 5559)
    publisher.start(10.0)  # 10 events per second
    print("   ✅ Publisher generating 10 events/second")

    print("\n5. 🔄 Running for 30 seconds - Watch the real-time data!")
    print("   You should see notifications appearing...")
    print()

    # Show real-time statistics for 30 seconds
    for i in range(6):  # 6 * 5 = 30 seconds
        time.sleep(5)
        
        # Get statistics
        pub_stats = publisher.get_statistics()
        sub_stats = subscriber.get_statistics()
        broker_stats = broker.get_statistics()
        
        print(f"📊 After {(i+1)*5} seconds:")
        print(f"   📤 Events Published: {pub_stats['events_published']}")
        print(f"   ⚡ Events Processed: {broker_stats['events_processed']}")
        print(f"   📨 Notifications Delivered: {sub_stats['notifications_received']}")
        if sub_stats['notifications_received'] > 0:
            matching_rate = (sub_stats['notifications_received'] / pub_stats['events_published']) * 100
            print(f"   🎯 Matching Rate: {matching_rate:.1f}%")
        if sub_stats['average_latency_ms'] > 0:
            print(f"   ⚡ Average Latency: {sub_stats['average_latency_ms']:.2f} ms")
        print()

    # Final results
    final_pub_stats = publisher.get_statistics()
    final_sub_stats = subscriber.get_statistics()
    final_broker_stats = broker.get_statistics()
    
    print("🏆 FINAL RESULTS:")
    print("=" * 50)
    print(f"✅ Total Events Published: {final_pub_stats['events_published']}")
    print(f"✅ Total Events Processed: {final_broker_stats['events_processed']}")
    print(f"✅ Total Notifications: {final_sub_stats['notifications_received']}")
    
    if final_sub_stats['notifications_received'] > 0:
        matching_rate = (final_sub_stats['notifications_received'] / final_pub_stats['events_published']) * 100
        print(f"✅ Matching Rate: {matching_rate:.1f}%")
        print(f"✅ Average Latency: {final_sub_stats['average_latency_ms']:.2f} ms")
    
    print(f"✅ Active Subscriptions: {len(subscriber.active_subscriptions)}")

    # Cleanup
    print("\n6. 🧹 Stopping components...")
    publisher.stop()
    subscriber.stop()
    broker.stop()
    
    print("\n🎉 Demo completed successfully!")
    print("\n📋 What you just saw:")
    print("  ✅ E-commerce events (purchases, views, ratings, inventory)")
    print("  ✅ Content-based subscription matching")
    print("  ✅ Real-time notification delivery")
    print("  ✅ Performance monitoring")
    print("  ✅ Binary serialization (Protocol Buffers)")
    print("  ✅ Distributed pub/sub architecture")

if __name__ == "__main__":
    main() 