# C2 System - Project Structure

## Overview
This document describes the restructured C2 system with improved modular architecture.

## Directory Structure

```
C2/
├── core/                           # Core functionality
│   ├── __init__.py
│   ├── protocol/                   # Communication protocol
│   │   ├── __init__.py
│   │   └── protocol.py            # Frame, FramedStream, Heartbeat
│   ├── server/                     # C2 server implementation
│   │   ├── __init__.py
│   │   ├── c2_server.py           # Original C2 server
│   │   └── c2_server_new.py       # Improved C2 server
│   ├── client/                     # Bot agent implementation
│   │   ├── __init__.py
│   │   └── bot_agent.py           # Bot agent
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       └── logging.py             # Logging utilities
├── features/                       # Additional features
│   ├── __init__.py
│   ├── monitoring/                # Health checks and monitoring
│   │   ├── __init__.py
│   │   ├── health_check.py        # Health check functionality
│   │   ├── web_dashboard.py       # Web dashboard
│   │   ├── templates/             # HTML templates
│   │   └── static/                # Static assets (JS, CSS)
│   ├── proxy/                     # Proxy functionality (future)
│   │   └── __init__.py
│   └── management/                 # Management tools (future)
│       └── __init__.py
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   │   ├── __init__.py
│   │   └── test_protocol.py       # Protocol tests
│   ├── integration/               # Integration tests
│   │   ├── __init__.py
│   │   └── test_c2_bot_integration.py
│   └── e2e/                       # End-to-end tests
│       ├── __init__.py
│       └── test_proxy_chain.py
├── scripts/                       # Utility scripts
│   ├── health_check_client.py     # Advanced health check client
│   ├── simple_health_check.py     # Simple health check client
│   ├── test_connection_limits.py  # Connection limits test
│   ├── test_graceful_shutdown.py  # Graceful shutdown test
│   └── test_health_check.py       # Health check test
├── config/                        # Configuration files
│   ├── config.json               # Main configuration
│   └── config_template.json      # Configuration template
├── docs/                         # Documentation
│   └── ARCHITECTURE.md           # Architecture documentation
├── main_c2.py                    # C2 server entry point
├── main_bot.py                   # Bot agent entry point
├── run_tests.py                  # Test runner
├── setup.py                      # Setup script
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── README.md                     # Main documentation
└── PROJECT_STRUCTURE.md          # This file
```

## Module Descriptions

### Core Module (`core/`)

#### Protocol (`core/protocol/`)
- **Purpose**: Communication protocol between C2 and bots
- **Files**:
  - `protocol.py`: Frame, FramedStream, Heartbeat classes
- **Dependencies**: None (base protocol)

#### Server (`core/server/`)
- **Purpose**: C2 server implementation
- **Files**:
  - `c2_server.py`: Original C2 server implementation
  - `c2_server_new.py`: Improved modular C2 server
- **Dependencies**: `core.protocol`, `core.utils`, `features.monitoring`

#### Client (`core/client/`)
- **Purpose**: Bot agent implementation
- **Files**:
  - `bot_agent.py`: Bot agent for connecting to C2
- **Dependencies**: `core.protocol`, `core.utils`

#### Utils (`core/utils/`)
- **Purpose**: Shared utility functions
- **Files**:
  - `config.py`: Configuration loading and validation
  - `logging.py`: Logging setup and utilities
- **Dependencies**: None (base utilities)

### Features Module (`features/`)

#### Monitoring (`features/monitoring/`)
- **Purpose**: Health checks and monitoring capabilities
- **Files**:
  - `health_check.py`: Health status management
  - `web_dashboard.py`: Web UI for monitoring
- **Dependencies**: `core.utils`

### Tests Module (`tests/`)

#### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components
- **Files**:
  - `test_protocol.py`: Protocol component tests
- **Dependencies**: `core.*`, `unittest`

#### Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions
- **Files**:
  - `test_c2_bot_integration.py`: C2-Bot integration tests
- **Dependencies**: `core.*`, `features.*`, `unittest`

#### E2E Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows
- **Files**:
  - `test_proxy_chain.py`: End-to-end proxy tests
- **Dependencies**: `core.*`, `features.*`, `unittest`

## Entry Points

### Main Entry Points
- `main_c2.py`: C2 server entry point
- `main_bot.py`: Bot agent entry point

### Utility Scripts
- `run_tests.py`: Test runner
- `setup.py`: Project setup script

## Configuration

### Configuration Files
- `config/config.json`: Main configuration
- `config/config_template.json`: Configuration template

### Configuration Structure
```json
{
  "server": {
    "host": "0.0.0.0",
    "bot_port": 4443,
    "http_port": 8080,
    "socks_port": 1080,
    "api_port": 5001
  },
  "security": {
    "bot_token": "...",
    "tls_enabled": false,
    "certfile": "certs/server.crt",
    "keyfile": "certs/server.key"
  },
  "limits": {
    "max_bots": 100,
    "max_connections_per_bot": 50,
    "connection_timeout": 300
  },
  "monitoring": {
    "health_check_interval": 30
  }
}
```

## Dependencies

### Core Dependencies
- `asyncio`: Asynchronous I/O
- `ssl`: TLS/SSL support
- `json`: JSON handling
- `uuid`: Unique ID generation
- `time`: Time utilities
- `signal`: Signal handling
- `sys`: System utilities
- `os`: Operating system interface
- `typing`: Type hints

### Test Dependencies
- `unittest`: Unit testing framework
- `subprocess`: Process management
- `pathlib`: Path utilities

## Usage

### Setup
```bash
python3 setup.py
```

### Start C2 Server
```bash
python3 main_c2.py --config config/config.json
```

### Start Bot Agent
```bash
python3 main_bot.py --c2-host localhost --c2-port 4443 --token your_token
```

### Run Tests
```bash
# All tests
python3 run_tests.py --all

# Unit tests only
python3 run_tests.py --unit

# Integration tests only
python3 run_tests.py --integration

# E2E tests only
python3 run_tests.py --e2e
```

### Health Check
```bash
# Simple health check
python3 scripts/simple_health_check.py

# Advanced health check
python3 scripts/health_check_client.py --all
```

## Benefits of New Structure

### 1. Modularity
- Clear separation of concerns
- Easy to add new features
- Independent module testing

### 2. Maintainability
- Well-organized code structure
- Clear dependencies
- Comprehensive documentation

### 3. Testability
- Isolated unit tests
- Integration test coverage
- End-to-end validation

### 4. Scalability
- Easy to extend functionality
- Plugin-ready architecture
- Microservices preparation

### 5. Development Experience
- Clear entry points
- Easy setup process
- Comprehensive testing tools

## Migration from Old Structure

### Files Moved
- `protocol.py` → `core/protocol/protocol.py`
- `c2_server.py` → `core/server/c2_server.py`
- `bot_agent.py` → `core/client/bot_agent.py`

### New Files Added
- `core/server/c2_server_new.py`: Improved C2 server
- `features/monitoring/`: Monitoring features
- `tests/`: Comprehensive test suite
- `main_c2.py`, `main_bot.py`: Entry points

### Configuration Changes
- `config.json` → `config/config.json`
- Added configuration validation
- Improved error handling

## Future Enhancements

### Planned Features
1. **Microservices Architecture**: Split into smaller services
2. **Plugin System**: Custom feature plugins
3. **Database Integration**: Persistent storage
4. **Advanced Monitoring**: Prometheus/Grafana
5. **Container Support**: Docker/Kubernetes

### Extension Points
1. **Custom Protocols**: Alternative communication methods
2. **Custom Monitoring**: Additional health check types
3. **Custom Authentication**: Alternative auth methods
4. **Custom Proxies**: Additional proxy types
