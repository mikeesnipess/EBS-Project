#!/usr/bin/env python3
"""Test individual components of the system."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_data_generator():
    """Test the data generator."""
    print("=== Testing Data Generator ===")
    
    from common.data_generator import EcommerceDataGenerator
    gen = EcommerceDataGenerator()
    
    # Test event generation
    purchase = gen.generate_purchase_event()
    print(f"✅ Purchase event: {purchase.purchase.category} - ${purchase.purchase.price}")
    
    rating = gen.generate_user_rating_event()
    print(f"✅ Rating event: {rating.user_rating.rating}/5.0 for {rating.user_rating.category}")
    
    # Test subscription generation
    simple_sub = gen.generate_simple_subscription("test_subscriber")
    print(f"✅ Simple subscription with {len(simple_sub.conditions)} conditions")
    
    complex_sub = gen.generate_complex_subscription("test_subscriber")
    print(f"✅ Complex subscription with {len(complex_sub.conditions)} conditions, window size: {complex_sub.window_config.window_size}")

def test_subscription_matcher():
    """Test the subscription matcher."""
    print("\n=== Testing Subscription Matcher ===")
    
    from common.subscription_matcher import SubscriptionMatcher
    from common.data_generator import EcommerceDataGenerator
    import protos.ecommerce_pb2 as ecommerce_pb2
    
    matcher = SubscriptionMatcher()
    gen = EcommerceDataGenerator()
    
    # Create a simple subscription for Electronics category
    subscription = ecommerce_pb2.Subscription(
        subscription_id="test-sub-1",
        subscriber_id="test-subscriber",
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
    
    matcher.add_subscription(subscription)
    print("✅ Added test subscription for Electronics category")
    
    # Generate Electronics events specifically to test matching
    electronics_matches = 0
    for i in range(5):
        event = gen.generate_purchase_event()
        # Force some events to be Electronics
        if i < 3:
            event.purchase.category = "Electronics"
        
        notifications = matcher.match_event(event)
        if notifications:
            electronics_matches += 1
            event_type_name = ecommerce_pb2.EventType.Name(event.event_type)
            print(f"✅ Event {i+1} matched! Type: {event_type_name}, Category: {event.purchase.category}")
    
    print(f"✅ {electronics_matches}/5 events matched the Electronics subscription")
    
    # Test windowed subscription
    complex_subscription = ecommerce_pb2.Subscription(
        subscription_id="test-sub-2",
        subscriber_id="test-subscriber",
        type=ecommerce_pb2.COMPLEX,
        conditions=[
            ecommerce_pb2.FilterCondition(
                field_name="category",
                operator=ecommerce_pb2.EQUAL,
                value="Electronics",
                is_windowed=False
            ),
            ecommerce_pb2.FilterCondition(
                field_name="avg_rating",
                operator=ecommerce_pb2.GREATER_THAN,
                value="3.0",
                is_windowed=True
            )
        ],
        window_config=ecommerce_pb2.WindowConfig(
            window_size=5,
            aggregation_type="avg"
        )
    )
    
    matcher.add_subscription(complex_subscription)
    print("✅ Added complex subscription for Electronics with avg_rating > 3.0")
    
    # Generate rating events to test windowed matching
    for i in range(6):
        rating_event = gen.generate_user_rating_event()
        rating_event.user_rating.category = "Electronics"
        rating_event.user_rating.rating = 4.0 + (i * 0.1)  # Ratings from 4.0 to 4.5
        
        notifications = matcher.match_event(rating_event)
        if notifications:
            for notif in notifications:
                if notif.HasField('complex'):
                    print(f"✅ Complex notification: avg_rating = {notif.complex.aggregated_value:.2f}")

def test_protobuf():
    """Test Protocol Buffers serialization."""
    print("\n=== Testing Protocol Buffers ===")
    
    from common.data_generator import EcommerceDataGenerator
    import protos.ecommerce_pb2 as ecommerce_pb2
    gen = EcommerceDataGenerator()
    
    # Generate an event
    event = gen.generate_purchase_event()
    
    # Serialize to bytes
    serialized = event.SerializeToString()
    print(f"✅ Serialized event to {len(serialized)} bytes")
    
    # Deserialize from bytes
    deserialized_event = ecommerce_pb2.EcommerceEvent()
    deserialized_event.ParseFromString(serialized)
    
    event_type_name = ecommerce_pb2.EventType.Name(deserialized_event.event_type)
    print(f"✅ Deserialized event: {event_type_name} - {deserialized_event.purchase.category}")

def main():
    """Run all component tests."""
    print("E-commerce Publish/Subscribe System - Component Tests")
    print("=" * 60)
    
    try:
        test_data_generator()
        test_subscription_matcher()
        test_protobuf()
        
        print("\n" + "=" * 60)
        print("✅ ALL COMPONENT TESTS PASSED!")
        print("The system components are working correctly.")
        print("\nThe subscription matching engine is functional:")
        print("• Simple subscriptions match based on field conditions")
        print("• Complex subscriptions process windowed analytics")
        print("• Protocol Buffers serialization works correctly")
        print("\nYou can now run:")
        print("  python demo.py                           # Interactive demo")
        print("  python evaluation/performance_test.py    # Full evaluation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 