#!/usr/bin/env python3
"""Web UI for E-commerce Publish/Subscribe System."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import json
from datetime import datetime
from collections import deque

from publisher.ecommerce_publisher import EcommercePublisher
from brokers.broker import EcommerceBroker  
from subscribers.subscriber import EcommerceSubscriber
from common.data_generator import EcommerceDataGenerator
import protos.ecommerce_pb2 as ecommerce_pb2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ebs_demo_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global system components
broker = None
publisher = None
subscriber = None
data_generator = EcommerceDataGenerator()

# Event logging storage (keep last 100 events/notifications)
event_logs = deque(maxlen=100)
notification_logs = deque(maxlen=100)

# System state
system_stats = {
    'events_published': 0,
    'notifications_received': 0,
    'active_subscriptions': 0,
    'system_running': False
}

def log_published_event(event):
    """Log a published event with details."""
    print(f"DEBUG: log_published_event called for event {event.event_id}")
    
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Extract event details based on type
    event_details = {}
    if event.HasField('purchase'):
        event_details = {
            'type': 'Purchase',
            'category': event.purchase.category,
            'product': event.purchase.product_id,  # Changed from product_name to product_id
            'price': f"${event.purchase.price:.2f}",
            'user': event.purchase.user_id
        }
    elif event.HasField('product_view'):
        event_details = {
            'type': 'Product View',
            'category': event.product_view.category,
            'product': event.product_view.product_id,  # Changed from product_name to product_id
            'user': event.product_view.user_id
        }
    elif event.HasField('user_rating'):
        event_details = {
            'type': 'User Rating',
            'category': event.user_rating.category,
            'rating': f"{event.user_rating.rating}/5.0",
            'user': event.user_rating.user_id
        }
    elif event.HasField('inventory_update'):
        event_details = {
            'type': 'Inventory Update',
            'category': event.inventory_update.category,
            'stock': f"{event.inventory_update.stock_level} units",
            'warehouse': event.inventory_update.warehouse_id
        }
    
    log_entry = {
        'timestamp': timestamp,
        'event_id': event.event_id,
        'details': event_details
    }
    
    event_logs.append(log_entry)
    
    # Update system statistics
    system_stats['events_published'] += 1
    
    # Emit to connected clients (Flask-SocketIO broadcasts by default)
    print(f"DEBUG: Emitting event_published via WebSocket: {log_entry}")
    socketio.emit('event_published', log_entry)
    
    # Also emit updated stats
    socketio.emit('stats_update', system_stats)
    
    print(f"[{timestamp}] EVENT PUBLISHED: {event_details['type']} - {event_details}")

def log_received_notification(notification):
    """Log a received notification with details."""
    print(f"DEBUG: log_received_notification called for notification {notification.notification_id}")
    
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Extract event details from the notification
    event = None
    if notification.HasField('simple'):
        event = notification.simple.matched_event  # Fixed: access matched_event properly
    elif notification.HasField('complex'):
        # For complex notifications, we don't have a matched event
        log_entry = {
            'timestamp': timestamp,
            'subscription_id': notification.subscription_id,
            'event_id': 'N/A',
            'details': {
                'type': 'Complex Notification',
                'category': notification.complex.category,
                'field': notification.complex.field_name,
                'value': f"{notification.complex.aggregated_value:.2f}",
                'window_size': notification.complex.window_size
            }
        }
        
        notification_logs.append(log_entry)
        
        # Update system statistics for complex notifications
        system_stats['notifications_received'] += 1
        
        print(f"DEBUG: Emitting notification_received (complex) via WebSocket: {log_entry}")
        socketio.emit('notification_received', log_entry)
        
        # Also emit updated stats
        socketio.emit('stats_update', system_stats)
        
        print(f"[{timestamp}] NOTIFICATION RECEIVED: {notification.subscription_id} -> Complex - {log_entry['details']}")
        return
    
    if event is None:
        print(f"ERROR: Could not extract event from notification {notification.notification_id}")
        return
    
    event_details = {}
    if event.HasField('purchase'):
        event_details = {
            'type': 'Purchase',
            'category': event.purchase.category,
            'product': event.purchase.product_id,  # Changed from product_name to product_id
            'price': f"${event.purchase.price:.2f}",
            'user': event.purchase.user_id
        }
    elif event.HasField('product_view'):
        event_details = {
            'type': 'Product View',
            'category': event.product_view.category,
            'product': event.product_view.product_id,  # Changed from product_name to product_id
            'user': event.product_view.user_id
        }
    elif event.HasField('user_rating'):
        event_details = {
            'type': 'User Rating',
            'category': event.user_rating.category,
            'rating': f"{event.user_rating.rating}/5.0",
            'user': event.user_rating.user_id
        }
    elif event.HasField('inventory_update'):
        event_details = {
            'type': 'Inventory Update',
            'category': event.inventory_update.category,
            'stock': f"{event.inventory_update.stock_level} units",
            'warehouse': event.inventory_update.warehouse_id
        }
    
    log_entry = {
        'timestamp': timestamp,
        'subscription_id': notification.subscription_id,
        'event_id': event.event_id,
        'details': event_details
    }
    
    notification_logs.append(log_entry)
    
    # Update system statistics
    system_stats['notifications_received'] += 1
    
    # Emit to connected clients (Flask-SocketIO broadcasts by default)
    print(f"DEBUG: Emitting notification_received via WebSocket: {log_entry}")
    socketio.emit('notification_received', log_entry)
    
    # Also emit updated stats
    socketio.emit('stats_update', system_stats)
    
    print(f"[{timestamp}] NOTIFICATION RECEIVED: {notification.subscription_id} -> {event_details['type']} - {event_details}")

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the EBS system components."""
    global broker, publisher, subscriber
    
    try:
        if broker is None:
            # Start broker
            broker = EcommerceBroker("web_broker", 5569, 5570)
            
            # Hook into broker's event processing for real-time logging
            original_handle_event = broker._handle_event
            original_send_notification = broker._send_notification
            
            def logged_handle_event(event):
                log_published_event(event)
                return original_handle_event(event)
            
            def logged_send_notification(notification):
                log_received_notification(notification)
                return original_send_notification(notification)
            
            # Replace the methods with logged versions
            broker._handle_event = logged_handle_event
            broker._send_notification = logged_send_notification
            
            broker.start()
            time.sleep(1)
            
            # Start subscriber with realistic subscriptions
            subscriber = EcommerceSubscriber("web_subscriber", [5570])
            subscriber.start()
            time.sleep(1)
            # create_default_subscriptions()  # COMMENTED OUT - No automatic subscriptions
            
            # Start publisher  
            # publisher = EcommercePublisher("web_publisher", 5569)
            # publisher.start(0.5)  # COMMENTED OUT - No automatic event generation
            
            system_stats['system_running'] = True
            
            # Start simplified monitoring thread
            threading.Thread(target=monitor_system_simple, daemon=True).start()
            
            # Test WebSocket communication
            print("DEBUG: Testing WebSocket communication...")
            test_event = {
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'event_id': 'test-event-123',
                'details': {
                    'type': 'Test Event',
                    'message': 'WebSocket test successful!'
                }
            }
            socketio.emit('event_published', test_event)
            print(f"DEBUG: Test event emitted via WebSocket: {test_event}")
            
        return jsonify({'status': 'success', 'message': 'System started successfully'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the EBS system components."""
    global broker, publisher, subscriber
    
    try:
        if publisher:
            publisher.stop()
            publisher = None
            
        if subscriber:
            subscriber.stop()
            subscriber = None
            
        if broker:
            broker.stop()
            broker = None
            
        system_stats['system_running'] = False
        
        return jsonify({'status': 'success', 'message': 'System stopped successfully'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/events/send', methods=['POST'])
def send_custom_event():
    """Send a custom event."""
    try:
        data = request.json
        event_type = data.get('event_type')
        
        if not event_type:
            return jsonify({'status': 'error', 'message': 'Event type is required'})
        
        # Create event based on type
        if event_type == 'purchase':
            event = create_purchase_event(data)
        elif event_type == 'view':
            event = create_view_event(data)
        elif event_type == 'rating':
            event = create_rating_event(data)
        elif event_type == 'inventory':
            event = create_inventory_event(data)
        else:
            return jsonify({'status': 'error', 'message': f'Invalid event type: {event_type}'})
        
        # Log the published event
        log_published_event(event)
        
        # Send via broker if running
        notifications = []
        if broker:
            notifications = broker.matcher.match_event(event)
            for notif in notifications:
                # Send notification (logging is handled automatically by hooked method)
                broker._send_notification(notif)
        else:
            return jsonify({'status': 'error', 'message': 'System not running. Please start the system first.'})
        
        return jsonify({
            'status': 'success', 
            'message': f'{event_type.title()} event sent successfully',
            'matches': len(notifications),
            'event_details': {
                'type': event_type,
                'category': getattr(getattr(event, event_type, None), 'category', 'N/A'),
                'price': getattr(getattr(event, event_type, None), 'price', None) if event_type == 'purchase' else None
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to send event: {str(e)}'})

@app.route('/api/subscriptions/create', methods=['POST'])
def create_subscription():
    """Create a new subscription."""
    try:
        data = request.json
        
        subscription = ecommerce_pb2.Subscription(
            subscription_id=data['subscription_id'],
            subscriber_id="web_subscriber",
            type=ecommerce_pb2.SIMPLE,
            conditions=[
                ecommerce_pb2.FilterCondition(
                    field_name=data['field_name'],
                    operator=getattr(ecommerce_pb2, data['operator']),
                    value=data['value'],
                    is_windowed=False
                )
            ]
        )
        
        if broker:
            broker.matcher.add_subscription(subscription)
            
            # Force update statistics immediately
            if hasattr(broker, 'matcher'):
                subscription_count = len(broker.matcher.simple_subscriptions) + len(broker.matcher.complex_subscriptions)
                system_stats['active_subscriptions'] = subscription_count
                socketio.emit('stats_update', system_stats)
            
            return jsonify({
                'status': 'success', 
                'message': f'Subscription "{data["subscription_id"]}" created successfully',
                'subscription_count': system_stats['active_subscriptions']
            })
        else:
            return jsonify({'status': 'error', 'message': 'System not running. Please start the system first.'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to create subscription: {str(e)}'})

@app.route('/api/stats')
def get_stats():
    """Get current system statistics."""
    stats = system_stats.copy()
    
    if broker:
        broker_stats = broker.get_statistics()
        stats.update(broker_stats)
        
    if subscriber:
        sub_stats = subscriber.get_statistics()
        stats.update(sub_stats)
        
    if publisher:
        pub_stats = publisher.get_statistics()
        stats.update(pub_stats)
        
    return jsonify(stats)

@app.route('/api/event-logs')
def get_event_logs():
    """Get recent event logs."""
    return jsonify({
        'published_events': list(event_logs),
        'received_notifications': list(notification_logs)
    })

def create_default_subscriptions():
    """Create default realistic subscriptions."""
    subscriptions = [
        # Category subscriptions
        ("electronics", "category", "EQUAL", "Electronics"),
        ("clothing", "category", "EQUAL", "Clothing"),
        ("home_garden", "category", "EQUAL", "Home & Garden"),
        
        # Price subscriptions
        ("budget", "price", "LESS_THAN", "100.0"),
        ("expensive", "price", "GREATER_THAN", "500.0"),
        
        # Stock subscription
        ("low_stock", "stock_level", "LESS_THAN", "10")
    ]
    
    for sub_id, field, operator, value in subscriptions:
        subscription = ecommerce_pb2.Subscription(
            subscription_id=sub_id,
            subscriber_id="web_subscriber",
            type=ecommerce_pb2.SIMPLE,
            conditions=[
                ecommerce_pb2.FilterCondition(
                    field_name=field,
                    operator=getattr(ecommerce_pb2, operator),
                    value=value,
                    is_windowed=False
                )
            ]
        )
        broker.matcher.add_subscription(subscription)

def create_purchase_event(data):
    """Create a purchase event from form data."""
    event = data_generator.generate_purchase_event()
    
    # Override with user data, with fallbacks for missing fields
    event.purchase.category = data.get('category', event.purchase.category)
    
    # Handle price with validation
    try:
        price = data.get('price')
        if price and price != '':
            event.purchase.price = float(price)
    except (ValueError, TypeError):
        pass  # Keep generated price
    
    # Handle product ID with fallback (changed from product_name to product_id)
    product_name = data.get('product_name', '').strip()
    if product_name:
        event.purchase.product_id = product_name  # Use product_name input for product_id field
    # Otherwise keep the generated product_id
    
    # Handle user ID with fallback
    user_id = data.get('user_id', '').strip()
    if user_id:
        event.purchase.user_id = user_id
    # Otherwise keep the generated user ID
    
    return event

def create_view_event(data):
    """Create a product view event from form data."""
    event = data_generator.generate_product_view_event()
    
    event.product_view.category = data.get('category', event.product_view.category)
    
    # Handle product ID (changed from product_name to product_id)
    product_name = data.get('product_name', '').strip()
    if product_name:
        event.product_view.product_id = product_name  # Use product_name input for product_id field
    
    event.product_view.user_id = data.get('user_id', event.product_view.user_id)
    
    return event

def create_rating_event(data):
    """Create a rating event from form data."""
    event = data_generator.generate_user_rating_event()
    
    event.user_rating.category = data.get('category', event.user_rating.category)
    event.user_rating.rating = float(data.get('rating', event.user_rating.rating))
    event.user_rating.user_id = data.get('user_id', event.user_rating.user_id)
    
    return event

def create_inventory_event(data):
    """Create an inventory event from form data."""
    event = data_generator.generate_inventory_update_event()
    
    event.inventory_update.category = data.get('category', event.inventory_update.category)
    event.inventory_update.stock_level = int(data.get('stock_level', event.inventory_update.stock_level))
    event.inventory_update.warehouse_id = data.get('warehouse_id', event.inventory_update.warehouse_id)
    
    return event

def monitor_system_simple():
    """Simplified system monitoring without complex event tracking."""
    while system_stats['system_running']:
        try:
            # Update subscription count from broker
            if broker and hasattr(broker, 'matcher'):
                subscription_count = len(broker.matcher.simple_subscriptions) + len(broker.matcher.complex_subscriptions)
                system_stats['active_subscriptions'] = subscription_count
                
            # Don't override the manually tracked events_published and notifications_received
            # as they are now updated in real-time via the logging functions
            
            # Emit notification updates via WebSocket
            socketio.emit('stats_update', system_stats)
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            
        time.sleep(2)  # Update every 2 seconds

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True) 