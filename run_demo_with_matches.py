#!/usr/bin/env python3
"""Demo with guaranteed matching events and subscriptions."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from publisher.ecommerce_publisher import EcommercePublisher
from brokers.broker import EcommerceBroker
from subscribers.subscriber import EcommerceSubscriber
from common.data_generator import EcommerceDataGenerator
import protos.ecommerce_pb2 as ecommerce_pb2

def main():
    print("🎯 E-commerce Demo with Guaranteed Matches")
    print("=" * 50)
    print("This demo creates events that WILL match subscriptions!")
    print()

    # Start broker
    print("1. 🏗️ Starting Broker...")
    broker = EcommerceBroker("demo_broker", 5565, 5566)
    broker.start()
    time.sleep(2)

    # Start subscriber
    print("2. 👥 Starting Subscriber...")
    subscriber = EcommerceSubscriber("demo_subscriber", [5566])
    subscriber.start()
    time.sleep(2)

    # Create SPECIFIC subscriptions that will match
    print("3. 📝 Creating TARGETED subscriptions...")
    
    # Create subscription for Electronics purchases
    electronics_sub = ecommerce_pb2.Subscription(
        subscription_id="electronics_sub",
        subscriber_id="demo_subscriber",
        type=ecommerce_pb2.SIMPLE,
        conditions=[
            ecommerce_pb2.FilterCondition(
                field_name="category",
                operator=ecommerce_pb2.EQUAL,
                value="Electronics",
                is_windowed=False
            )
        ]
    )
    
    # Create subscription for high-value purchases (>$500)
    high_value_sub = ecommerce_pb2.Subscription(
        subscription_id="high_value_sub",
        subscriber_id="demo_subscriber",
        type=ecommerce_pb2.SIMPLE,
        conditions=[
            ecommerce_pb2.FilterCondition(
                field_name="price",
                operator=ecommerce_pb2.GREATER_THAN,
                value="500.0",
                is_windowed=False
            )
        ]
    )
    
    # Register subscriptions manually
    broker.matcher.add_subscription(electronics_sub)
    broker.matcher.add_subscription(high_value_sub)
    
    print("   ✅ Created subscription for Electronics category")
    print("   ✅ Created subscription for purchases > $500")

    # Start publisher
    print("\n4. 📢 Starting Custom Publisher...")
    generator = EcommerceDataGenerator()
    
    print("5. 🎯 Publishing TARGETED events that WILL match...")
    
    # Publish specific events that will match our subscriptions
    for i in range(20):
        if i % 3 == 0:
            # Create Electronics purchase
            event = generator.generate_purchase_event()
            event.purchase.category = "Electronics"  # Force Electronics
            event.purchase.price = 750.0  # Force high value
            
            # Send via broker
            notifications = broker.matcher.match_event(event)
            if notifications:
                for notif in notifications:
                    broker._send_notification(notif)
            
            print(f"   📤 Sent Electronics purchase: ${event.purchase.price}")
            
        elif i % 3 == 1:
            # Create high-value purchase (any category)
            event = generator.generate_purchase_event()
            event.purchase.price = 800.0  # Force high value
            
            notifications = broker.matcher.match_event(event)
            if notifications:
                for notif in notifications:
                    broker._send_notification(notif)
                    
            print(f"   📤 Sent high-value {event.purchase.category} purchase: ${event.purchase.price}")
            
        else:
            # Create normal event (might not match)
            event = generator.generate_purchase_event()
            
            notifications = broker.matcher.match_event(event)
            if notifications:
                for notif in notifications:
                    broker._send_notification(notif)
                    
            print(f"   📤 Sent normal {event.purchase.category} purchase: ${event.purchase.price}")
        
        time.sleep(1)  # 1 second between events
    
    print("\n6. 📊 Final Results:")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Get statistics
    sub_stats = subscriber.get_statistics()
    broker_stats = broker.get_statistics()
    
    print(f"   📨 Notifications Received: {sub_stats['notifications_received']}")
    print(f"   ⚡ Events Processed: {broker_stats['events_processed']}")
    print(f"   🎯 Match Rate: {(sub_stats['notifications_received']/20)*100:.1f}%")
    
    if sub_stats['notifications_received'] > 0:
        print(f"   ⏱️ Average Latency: {sub_stats['average_latency_ms']:.2f} ms")
        print("\n🎉 SUCCESS! Notifications are working!")
    else:
        print("\n❌ No notifications received - check broker matching logic")

    # Cleanup
    print("\n7. 🧹 Stopping components...")
    subscriber.stop()
    broker.stop()
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    main() 