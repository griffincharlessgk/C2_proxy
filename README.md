# C2 System

A modular Command and Control system with proxy capabilities.

## Structure

```
C2/
├── core/                    # Core functionality
│   ├── protocol/           # Communication protocol
│   ├── server/             # C2 server implementation
│   ├── client/             # Bot agent implementation
│   └── utils/              # Utility functions
├── features/               # Additional features
│   ├── monitoring/         # Health checks and monitoring
│   ├── proxy/              # Proxy functionality
│   └── management/         # Management tools
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── docs/                   # Documentation
└── main_c2.py             # C2 server entry point
    main_bot.py            # Bot agent entry point
```

## Quick Start

1. **Setup**:
   ```bash
   python3 setup.py
   ```

2. **Start C2 Server**:
   ```bash
   python3 main_c2.py
   ```

3. **Start Bot Agent**:
   ```bash
   python3 main_bot.py --c2-host localhost --c2-port 4443 --token your_token
   ```

4. **Run Tests**:
   ```bash
   python3 run_tests.py --all
   ```

## Features

- ✅ Modular architecture
- ✅ Health check endpoints
- ✅ Connection limits
- ✅ Graceful shutdown
- ✅ Comprehensive testing
- ✅ Web dashboard
- ✅ Proxy support (HTTP/SOCKS5)

## Documentation

See `docs/` directory for detailed documentation.
