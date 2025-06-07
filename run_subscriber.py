#!/usr/bin/env python3
"""Standalone subscriber script."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from subscribers.subscriber import EcommerceSubscriber
import protos.ecommerce_pb2 as ecommerce_pb2

def create_realistic_subscriptions(subscriber):
    """Create realistic subscriptions that will actually match e-commerce events."""
    
    # Categories that the data generator actually uses
    real_categories = [
        "Electronics", "Clothing", "Home & Garden", "Sports", 
        "Books", "Health", "Beauty", "Automotive", "Toys"
    ]
    
    subscriptions_created = []
    
    # Create subscriptions for real categories (first 3)
    for i, category in enumerate(real_categories[:3]):
        subscription = ecommerce_pb2.Subscription(
            subscription_id=f"category_{category.lower().replace(' ', '_').replace('&', 'and')}",
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
        subscriber.active_subscriptions[subscription.subscription_id] = subscription
        subscriber._register_subscription(subscription)
        subscriptions_created.append(f"✅ {category} purchases")
        time.sleep(0.1)
    
    # Create price-based subscriptions with realistic ranges
    price_ranges = [
        ("budget", "LESS_THAN", "100.0", "< $100"),
        ("mid_range", "GREATER_THAN", "100.0", "> $100"),
        ("expensive", "GREATER_THAN", "500.0", "> $500")
    ]
    
    for name, operator, price, description in price_ranges:
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
        subscriber.active_subscriptions[subscription.subscription_id] = subscription
        subscriber._register_subscription(subscription)
        subscriptions_created.append(f"✅ {name.title()} purchases ({description})")
        time.sleep(0.1)
    
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
    subscriber.active_subscriptions[stock_subscription.subscription_id] = stock_subscription
    subscriber._register_subscription(stock_subscription)
    subscriptions_created.append("✅ Low stock alerts (< 10 items)")
    time.sleep(0.1)
    
    return subscriptions_created

def main():
    print("👥 Starting E-commerce Subscriber with REALISTIC Subscriptions")
    print("=" * 65)
    
    subscriber_id = "standalone_subscriber"
    broker_ports = [5562]  # Connect to broker on port 5562
    
    print(f"Subscriber ID: {subscriber_id}")
    print(f"Connecting to broker on port: {broker_ports[0]}")
    print()
    
    # Create and start subscriber
    subscriber = EcommerceSubscriber(subscriber_id, broker_ports)
    subscriber.start()
    time.sleep(2)
    
    print("📝 Creating REALISTIC subscriptions that will actually match...")
    print("   (These subscriptions use real categories and price ranges)")
    print()
    
    # Create realistic subscriptions instead of random ones
    subscriptions_list = create_realistic_subscriptions(subscriber)
    
    print("📋 Active subscriptions:")
    for sub_desc in subscriptions_list:
        print(f"   {sub_desc}")
    print()
    print(f"📊 Total subscriptions: {len(subscriber.active_subscriptions)}")
    print()
    print("🔔 Waiting for notifications...")
    print("   (You should see notifications when events match!)")
    print("Press Ctrl+C to stop the subscriber")
    print("=" * 65)
    
    try:
        # Keep running and show statistics
        last_notifications = 0
        while True:
            time.sleep(10)
            stats = subscriber.get_statistics()
            
            new_notifications = stats['notifications_received'] - last_notifications
            last_notifications = stats['notifications_received']
            
            print(f"📊 Subscriber Stats: {stats['notifications_received']} notifications received (+{new_notifications} new)")
            if stats['notifications_received'] > 0:
                print(f"   - Simple: {stats['simple_notifications']}")
                print(f"   - Complex: {stats['complex_notifications']}")
                print(f"   - Avg Latency: {stats['average_latency_ms']:.2f} ms")
                print(f"   - Uptime: {stats['uptime']:.1f} seconds")
                
                # Show matching rate
                if new_notifications > 0:
                    print(f"   🎯 Receiving {new_notifications} notifications every 10 seconds!")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping subscriber...")
        subscriber.stop()
        print("✅ Subscriber stopped successfully")

if __name__ == "__main__":
    main() 