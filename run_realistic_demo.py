#!/usr/bin/env python3
"""Realistic demo with actual matching subscriptions."""

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

def create_realistic_subscriptions(subscriber, broker):
    """Create subscriptions that will actually match real e-commerce events."""
    
    # Categories that the data generator actually uses
    real_categories = [
        "Electronics", "Clothing", "Home & Garden", "Sports", 
        "Books", "Health", "Beauty", "Automotive", "Toys"
    ]
    
    # Create subscriptions for real categories
    for i, category in enumerate(real_categories[:3]):  # Use first 3 categories
        subscription = ecommerce_pb2.Subscription(
            subscription_id=f"category_{category.lower().replace(' ', '_')}",
            subscriber_id=subscriber.subscriber_id,
            type=ecommerce_pb2.SIMPLE,
            conditions=[
                ecommerce_pb2.FilterCondition(
                    field_name="category",
                    operator=ecommerce_pb2.EQUAL,
                    value=category,
                    is_windowed=False
                )
            ]
        )
        broker.matcher.add_subscription(subscription)
        print(f"   ✅ Subscribed to {category} purchases")
    
    # Create price-based subscriptions with realistic ranges
    price_ranges = [
        ("budget", "LESS_THAN", "100.0"),
        ("mid_range", "GREATER_THAN", "100.0"),
        ("expensive", "GREATER_THAN", "500.0")
    ]
    
    for name, operator, price in price_ranges:
        subscription = ecommerce_pb2.Subscription(
            subscription_id=f"price_{name}",
            subscriber_id=subscriber.subscriber_id,
            type=ecommerce_pb2.SIMPLE,
            conditions=[
                ecommerce_pb2.FilterCondition(
                    field_name="price",
                    operator=getattr(ecommerce_pb2, operator),
                    value=price,
                    is_windowed=False
                )
            ]
        )
        broker.matcher.add_subscription(subscription)
        print(f"   ✅ Subscribed to {name} purchases ({operator.lower().replace('_', ' ')} ${price})")
    
    # Create stock-based subscription
    stock_subscription = ecommerce_pb2.Subscription(
        subscription_id="low_stock_alert",
        subscriber_id=subscriber.subscriber_id,
        type=ecommerce_pb2.SIMPLE,
        conditions=[
            ecommerce_pb2.FilterCondition(
                field_name="stock_level",
                operator=ecommerce_pb2.LESS_THAN,
                value="10",
                is_windowed=False
            )
        ]
    )
    broker.matcher.add_subscription(stock_subscription)
    print(f"   ✅ Subscribed to low stock alerts (< 10 items)")

def main():
    print("🛒 Realistic E-commerce Demo with Actual Matches")
    print("=" * 55)
    print("This demo uses REAL categories and price ranges!")
    print()

    # Start broker
    print("1. 🏗️ Starting Broker...")
    broker = EcommerceBroker("realistic_broker", 5567, 5568)
    broker.start()
    time.sleep(2)

    # Start subscriber
    print("2. 👥 Starting Subscriber...")
    subscriber = EcommerceSubscriber("realistic_subscriber", [5568])
    subscriber.start()
    time.sleep(2)

    # Create realistic subscriptions
    print("3. 📝 Creating REALISTIC subscriptions...")
    create_realistic_subscriptions(subscriber, broker)
    print(f"   📊 Total subscriptions: 7")

    # Start publisher with normal random events
    print("\n4. 📢 Starting Publisher with NORMAL random events...")
    publisher = EcommercePublisher("realistic_publisher", 5567)
    publisher.start(8.0)  # 8 events per second
    
    print("5. ⏳ Running for 30 seconds to collect matches...")
    print("   (You should see notifications appearing!)")
    print()
    
    # Monitor for 30 seconds
    start_time = time.time()
    last_notifications = 0
    
    while time.time() - start_time < 30:
        time.sleep(5)
        
        # Show progress
        elapsed = time.time() - start_time
        pub_stats = publisher.get_statistics()
        sub_stats = subscriber.get_statistics()
        broker_stats = broker.get_statistics()
        
        new_notifications = sub_stats['notifications_received'] - last_notifications
        last_notifications = sub_stats['notifications_received']
        
        print(f"⏱️  {elapsed:.0f}s: {pub_stats['events_published']} events → "
              f"{sub_stats['notifications_received']} notifications "
              f"(+{new_notifications} new)")
    
    # Stop publisher
    publisher.stop()
    
    print("\n6. 📊 Final Results:")
    sub_stats = subscriber.get_statistics()
    broker_stats = broker.get_statistics()
    pub_stats = publisher.get_statistics()
    
    print(f"   📤 Events Published: {pub_stats['events_published']}")
    print(f"   ⚡ Events Processed: {broker_stats['events_processed']}")
    print(f"   📨 Notifications Received: {sub_stats['notifications_received']}")
    
    if sub_stats['notifications_received'] > 0:
        match_rate = (sub_stats['notifications_received'] / pub_stats['events_published']) * 100
        print(f"   🎯 Match Rate: {match_rate:.1f}%")
        print(f"   ⏱️  Average Latency: {sub_stats['average_latency_ms']:.2f} ms")
        print(f"   📈 Simple Notifications: {sub_stats['simple_notifications']}")
        print(f"   📊 Complex Notifications: {sub_stats['complex_notifications']}")
        print("\n🎉 SUCCESS! Realistic matching is working!")
        
        # Show some example matches
        print("\n📋 What types of events matched:")
        print("   - Electronics/Clothing/Home & Garden purchases")
        print("   - Budget purchases (< $100)")
        print("   - Mid-range purchases (> $100)")  
        print("   - Expensive purchases (> $500)")
        print("   - Low stock alerts (< 10 items)")
    else:
        print("\n❌ No matches found - may need to run longer or adjust subscriptions")

    # Cleanup
    print("\n7. 🧹 Stopping components...")
    subscriber.stop()
    broker.stop()
    
    print("\n✅ Realistic demo completed!")

if __name__ == "__main__":
    main() 