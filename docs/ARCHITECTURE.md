# C2 System Architecture

## Overview

The C2 system is a modular Command and Control platform designed with clean architecture principles. It provides proxy capabilities, health monitoring, and management features through a well-structured codebase.

## Architecture Principles

### 1. Modular Design
- **Separation of Concerns**: Each module has a single responsibility
- **Loose Coupling**: Modules interact through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Layered Architecture
```
┌─────────────────────────────────────┐
│           Presentation Layer        │  ← Web UI, API endpoints
├─────────────────────────────────────┤
│           Business Layer            │  ← Core logic, features
├─────────────────────────────────────┤
│           Data Layer                │  ← Protocol, communication
└─────────────────────────────────────┘
```

### 3. Dependency Inversion
- High-level modules don't depend on low-level modules
- Both depend on abstractions
- Abstractions don't depend on details

## Project Structure

```
C2/
├── core/                    # Core components
│   ├── protocol/           # Communication protocol
│   │   └── protocol.py     # Frame, FramedStream, Heartbeat
│   ├── server/            # C2 server logic
│   │   └── c2_server.py   # Main C2 server implementation
│   ├── client/            # Bot agent logic
│   │   └── bot_agent.py   # Bot agent implementation
│   └── utils/             # Utilities
│       ├── config.py      # Configuration management
│       └── logging.py     # Logging utilities
├── features/              # Feature modules
│   ├── monitoring/        # Health checks & web dashboard
│   │   ├── health_check.py
│   │   ├── web_dashboard.py
│   │   ├── templates/
│   │   └── static/
│   ├── proxy/            # Proxy features (placeholder)
│   └── management/       # Management tools (placeholder)
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/            # End-to-end tests
├── scripts/             # Utility scripts
├── config/              # Configuration files
├── docs/               # Documentation
├── main_c2.py          # C2 server entry point
├── main_bot.py         # Bot agent entry point
└── run_tests.py        # Test runner
```

## Module Structure

### Core Module (`core/`)
Contains the essential functionality of the system.

#### Protocol (`core/protocol/`)
- **Purpose**: Communication protocol between C2 and bots
- **Components**:
  - `Frame`: Message structure
  - `FramedStream`: Stream wrapper for reliable communication
  - `Heartbeat`: Keep-alive mechanism

#### Server (`core/server/`)
- **Purpose**: C2 server implementation
- **Components**:
  - `C2Server`: Main server class
  - Bot session management
  - Proxy handling (HTTP/SOCKS5)
  - Connection management

#### Client (`core/client/`)
- **Purpose**: Bot agent implementation
- **Components**:
  - `BotAgent`: Bot client class
  - Connection to C2 server
  - Upstream traffic handling

#### Utils (`core/utils/`)
- **Purpose**: Shared utility functions
- **Components**:
  - `config`: Configuration management
  - `logging`: Logging utilities

### Features Module (`features/`)
Contains additional capabilities and features.

#### Monitoring (`features/monitoring/`)
- **Purpose**: Health checks and monitoring
- **Components**:
  - `health_check`: Health status management
  - `web_dashboard`: Web UI for monitoring

#### Proxy (`features/proxy/`)
- **Purpose**: Proxy functionality
- **Components**:
  - HTTP proxy implementation
  - SOCKS5 proxy implementation
  - Load balancing

#### Management (`features/management/`)
- **Purpose**: System management tools
- **Components**:
  - Bot management commands
  - Configuration management
  - System administration

### Tests Module (`tests/`)
Comprehensive test suite for the system.

#### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components
- **Coverage**: Protocol, utilities, individual functions
- **Tools**: unittest, mock

#### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions
- **Coverage**: C2-Bot communication, API endpoints
- **Tools**: unittest, subprocess

#### E2E Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows
- **Coverage**: Full proxy chain, end-to-end scenarios
- **Tools**: unittest, external tools

## Data Flow

### 1. Bot Connection
```
Bot Agent → C2 Server
    ↓
Authentication
    ↓
Session Creation
    ↓
Heartbeat Start
```

### 2. Proxy Request
```
Client → C2 Server → Bot Agent → Target
    ↓
Load Balancing
    ↓
Connection Tracking
    ↓
Data Forwarding
```

### 3. Health Check
```
Monitor → C2 Server
    ↓
Status Collection
    ↓
Health Assessment
    ↓
Response Generation
```

## Configuration Management

### Configuration Hierarchy
1. **Default Configuration**: Built-in defaults
2. **File Configuration**: `config/config.json`
3. **Command Line**: Runtime overrides
4. **Environment Variables**: System settings

### Configuration Structure
```json
{
  "server": {
    "host": "0.0.0.0",
    "ports": { ... }
  },
  "security": {
    "bot_token": "...",
    "tls": { ... }
  },
  "limits": {
    "max_bots": 100,
    "max_connections_per_bot": 50
  },
  "monitoring": {
    "health_check": { ... }
  }
}
```

## Error Handling

### Error Categories
1. **Connection Errors**: Network issues, timeouts
2. **Authentication Errors**: Invalid tokens, failed auth
3. **Resource Errors**: Limits exceeded, resource unavailable
4. **Protocol Errors**: Invalid frames, malformed data

### Error Handling Strategy
- **Fail Fast**: Detect errors early
- **Graceful Degradation**: Continue operation when possible
- **Comprehensive Logging**: Log all errors with context
- **User-Friendly Messages**: Clear error messages

## Security Considerations

### Authentication
- Bot token validation
- Session management
- Token rotation support

### Encryption
- TLS support for C2-Bot communication
- Certificate management
- Secure key storage

### Access Control
- Connection limits
- Rate limiting
- IP whitelisting (planned)

## Performance Considerations

### Scalability
- Asynchronous I/O with asyncio
- Connection pooling
- Load balancing

### Resource Management
- Connection limits
- Memory management
- CPU usage optimization

### Monitoring
- Health checks
- Metrics collection
- Performance monitoring

## Deployment Architecture

### Single Server Deployment
```
┌─────────────────┐
│   C2 Server     │
│   + Web UI      │
│   + API         │
└─────────────────┘
         │
    ┌─────────┐
    │  Bot 1  │
    └─────────┘
```

### Distributed Deployment
```
┌─────────────────┐    ┌─────────────────┐
│   C2 Server 1   │    │   C2 Server 2   │
│   + Load Balancer│    │   + Load Balancer│
└─────────────────┘    └─────────────────┘
         │                       │
    ┌─────────┐              ┌─────────┐
    │  Bot 1  │              │  Bot 2  │
    └─────────┘              └─────────┘
```

## Future Enhancements

### Planned Features
1. **Microservices Architecture**: Split into smaller services
2. **Message Queue**: Use Redis/RabbitMQ for communication
3. **Database Integration**: Persistent storage for sessions
4. **Advanced Monitoring**: Prometheus/Grafana integration
5. **Container Support**: Docker/Kubernetes deployment

### Extension Points
1. **Plugin System**: Custom feature plugins
2. **Custom Protocols**: Alternative communication methods
3. **Custom Monitoring**: Additional health check types
4. **Custom Authentication**: Alternative auth methods

## Development Guidelines

### Code Organization
- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Write comprehensive docstrings
- Keep functions small and focused

### Testing Strategy
- Write tests for all new features
- Maintain high test coverage
- Use appropriate test types (unit/integration/e2e)
- Test error conditions and edge cases

### Documentation
- Keep documentation up to date
- Use clear, concise language
- Include examples and diagrams
- Document API endpoints and configuration options
