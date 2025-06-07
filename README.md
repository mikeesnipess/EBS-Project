# EBS Project - Event-Based Systems Web Interface

A comprehensive **Event-Based Systems (EBS)** implementation with a modern web interface for e-commerce event publishing, subscription management, and real-time monitoring.

## 🏗️ Architecture Overview

This project implements a distributed event-based system with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Publishers    │────│     Broker      │────│   Subscribers   │
│                 │    │                 │    │                 │
│ - Manual Events │    │ - Event Routing │    │ - Notifications │
│ - Data Generator│    │ - Subscriptions │    │ - Real-time UI  │
│ - Web Interface │    │ - Matching      │    │ - Statistics    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                        ┌───────────────┐
                        │  Web UI       │
                        │               │
                        │ - Dashboard   │
                        │ - Event Logs  │
                        │ - WebSockets  │
                        │ - Statistics  │
                        └───────────────┘
```

### Core Components

1. **Broker**: Central event routing hub using ZeroMQ
2. **Publishers**: Generate and send events to the broker
3. **Subscribers**: Receive notifications based on subscriptions
4. **Web UI**: Flask-based interface with real-time updates
5. **Protocol Buffers**: Structured data serialization
6. **WebSocket**: Real-time communication between backend and frontend

## 🚀 Features

### Real-Time Event Management
- **Manual Event Creation**: Create Purchase, Product View, User Rating, and Inventory events
- **Dynamic Product Selection**: 10 categories with 5 products each (50 total products)
- **Live Event Logging**: See all published events in real-time
- **Notification Tracking**: Monitor which subscriptions trigger notifications

### Subscription Management
- **Flexible Subscriptions**: Create subscriptions based on various criteria
- **Real-Time Matching**: Events are matched against subscriptions instantly
- **Visual Feedback**: See subscription counts and active status

### Performance & Monitoring
- **Statistics Dashboard**: Track events published, notifications received, active subscriptions
- **Event History**: Store up to 100 recent events and notifications
- **System Status**: Monitor broker, publisher, and subscriber status
- **WebSocket Integration**: Real-time updates without page refresh

### User Interface
- **Modern Dashboard**: Bootstrap-based responsive design
- **Event Panels**: Separate panels for published events and received notifications
- **Manual Controls**: Full control over event generation and subscription creation
- **Processing Indicators**: Visual feedback during event processing

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB free space

### Python Dependencies
```
flask>=2.0.0
flask-socketio>=5.0.0
protobuf>=3.19.0
pyzmq>=22.0.0
eventlet>=0.33.0
```

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd EBS-Project
```

### 2. Install Dependencies
```bash
pip install flask flask-socketio protobuf pyzmq eventlet
```

### 3. Generate Protocol Buffer Files
```bash
# Navigate to the protos directory
cd protos

# Generate Python files from .proto definitions
protoc --python_out=. ecommerce.proto
```

### 4. Verify Installation
```bash
# Check if all required modules are available
python -c "import flask, flask_socketio, zmq, google.protobuf; print('All dependencies installed successfully')"
```

## 🎯 Usage Guide

### Starting the System

1. **Launch the Web Interface**
   ```bash
   cd web_ui
   python app.py
   ```

2. **Access the Dashboard**
   - Open your browser and navigate to: `http://127.0.0.1:5000`
   - You'll see the main dashboard with statistics and control panels

3. **Initialize the EBS System**
   - Click the **"Start System"** button in the dashboard
   - This initializes the broker, subscriber, and sets up event logging
   - Wait for the "System started successfully" message

### Creating Subscriptions

1. **Navigate to Subscription Panel**
   - Use the subscription form in the dashboard
   - Choose field name, operator, and value for filtering

2. **Example Subscriptions**
   ```
   Field: price, Operator: GREATER_THAN, Value: 50
   Field: category, Operator: EQUAL, Value: Electronics
   Field: stock_level, Operator: LESS_THAN, Value: 10
   ```

3. **Subscription Management**
   - Each subscription gets a unique ID
   - Active subscriptions are tracked in real-time
   - Subscriptions persist until system restart

### Generating Events

1. **Manual Event Creation**
   - Use the event creation form in the dashboard
   - Select event type: Purchase, Product View, User Rating, or Inventory Update

2. **Dynamic Product Selection**
   - Choose from 10 categories:
     - Electronics, Clothing, Home & Garden, Sports, Books
     - Health & Beauty, Automotive, Toys & Games, Food & Beverages
   - Each category has 5 realistic products
   - Product dropdown updates automatically when category changes

3. **Event Parameters**
   - **Purchase Events**: Category, Product, Price, User ID
   - **Product View Events**: Category, Product, User ID
   - **User Rating Events**: Category, Rating (1-5), User ID
   - **Inventory Updates**: Category, Stock Level, Warehouse ID

### Monitoring & Analytics

1. **Real-Time Statistics**
   - Events Published: Total number of events created
   - Notifications Received: Total notifications triggered
   - Active Subscriptions: Current subscription count
   - System Status: Running/Stopped indicator

2. **Event Logs**
   - **Published Events Panel**: Shows all created events with timestamps
   - **Received Notifications Panel**: Shows triggered notifications
   - **Event Details**: Type, category, product, price, user, timestamps
   - **Automatic Scrolling**: Latest events appear at the top

3. **Performance Monitoring**
   - Events are processed at optimal speed (0.5 events/second when auto-generated)
   - UI updates are throttled to prevent DOM conflicts
   - Event queues handle burst processing
   - Maximum 100 events/notifications stored in memory

## ⚙️ Configuration Options

### Event Generation Settings
```python
# In web_ui/app.py
system_stats = {
    'events_published': 0,
    'notifications_received': 0,
    'active_subscriptions': 0,
    'system_running': False
}

# Event storage capacity
event_logs = deque(maxlen=100)
notification_logs = deque(maxlen=100)
```

### Network Configuration
```python
# Default ports
BROKER_PUB_PORT = 5569  # Publisher events
BROKER_SUB_PORT = 5570  # Subscriber notifications
WEB_UI_PORT = 5000      # Flask web interface
```

### Product Categories and Items
The system includes 50 predefined products across 10 categories:
- **Electronics**: Laptops, Smartphones, Tablets, Headphones, Cameras
- **Clothing**: T-Shirts, Jeans, Sneakers, Jackets, Dresses
- **Home & Garden**: Sofas, Coffee Tables, Plants, Garden Tools, Lighting
- **Sports**: Running Shoes, Basketballs, Yoga Mats, Dumbbells, Bicycles
- **Books**: Fiction, Non-Fiction, Textbooks, Comics, Magazines
- **Health & Beauty**: Skincare, Makeup, Vitamins, Shampoo, Perfume
- **Automotive**: Car Parts, Motor Oil, Tires, GPS, Car Accessories
- **Toys & Games**: Board Games, Action Figures, Puzzles, Video Games, LEGO
- **Food & Beverages**: Snacks, Beverages, Frozen Foods, Fresh Produce, Condiments

## 🔧 API Endpoints

### System Control
- **POST** `/api/system/start` - Initialize EBS components
- **POST** `/api/system/stop` - Shutdown all components
- **GET** `/api/stats` - Get current system statistics

### Event Management
- **POST** `/api/events/send` - Create and publish custom events
- **GET** `/api/event-logs` - Retrieve recent event and notification logs

### Subscription Management
- **POST** `/api/subscriptions/create` - Create new subscriptions

### WebSocket Events
- `event_published` - New event created
- `notification_received` - Subscription triggered
- `stats_update` - Statistics updated

## 🚀 Performance Considerations

### High-Volume Event Processing (10,000+ Events)

The system is designed to handle high-volume event processing efficiently:

1. **Memory Management**
   - Events are stored in rotating queues (100 max)
   - Older events are automatically discarded
   - Memory usage remains constant regardless of total events

2. **Processing Speed**
   - Manual events: Instant processing
   - Auto-generated events: 0.5 events/second (configurable)
   - WebSocket updates: Throttled to prevent UI overload

3. **Scaling for 10,000+ Events**
   ```python
   # To handle large volumes, modify these settings:
   
   # Increase event storage capacity
   event_logs = deque(maxlen=1000)
   notification_logs = deque(maxlen=1000)
   
   # Adjust monitoring frequency
   time.sleep(1)  # Update every 1 second instead of 2
   
   # Enable batch processing for notifications
   # (Implementation depends on specific requirements)
   ```

4. **Database Integration** (Future Enhancement)
   - For persistent storage of 10,000+ events
   - Implement SQLite or PostgreSQL backend
   - Add event archiving and retrieval functionality

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   ```
   Solution: Ensure Flask-SocketIO is properly installed
   pip install flask-socketio eventlet
   ```

2. **Port Already in Use**
   ```
   Error: Address already in use
   Solution: Kill existing processes or change ports in configuration
   ```

3. **Protocol Buffer Errors**
   ```
   Solution: Regenerate .proto files
   cd protos && protoc --python_out=. ecommerce.proto
   ```

4. **Events Not Appearing in UI**
   ```
   Solution: Check browser console for WebSocket errors
   Refresh the page and restart the system
   ```

### Debug Mode

Enable detailed logging by setting debug mode:
```python
# In web_ui/app.py
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
```

### Performance Debugging
```python
# Add these debug prints to monitor performance
print(f"Event processing time: {time.time() - start_time:.3f}s")
print(f"Current memory usage: {len(event_logs)} events, {len(notification_logs)} notifications")
```

## 📈 System Architecture Details

### Event Flow
1. **Event Creation**: User creates event via web interface
2. **Event Processing**: Event is logged and sent to broker
3. **Subscription Matching**: Broker matches event against active subscriptions
4. **Notification Generation**: Matching subscriptions generate notifications
5. **Real-time Updates**: WebSocket pushes updates to UI
6. **Statistics Update**: System statistics are updated and broadcast

### Data Structures
```protobuf
// Event structure (simplified)
message Event {
    string event_id = 1;
    int64 timestamp = 2;
    oneof event_type {
        PurchaseEvent purchase = 3;
        ProductViewEvent product_view = 4;
        UserRatingEvent user_rating = 5;
        InventoryUpdateEvent inventory_update = 6;
    }
}

// Notification structure
message Notification {
    string notification_id = 1;
    string subscription_id = 2;
    int64 timestamp = 3;
    oneof notification_type {
        SimpleNotification simple = 4;
        ComplexNotification complex = 5;
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed information
4. Include system information, error messages, and steps to reproduce

---

**Happy Event Processing! 🎉** 