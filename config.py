# Configuration constants for Crypto Research Bot

import re

# API Configuration
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
OPENAI_MODEL = "gpt-4-turbo-preview"
MAX_TOKENS = 1500
TEMPERATURE = 0.7
PRESENCE_PENALTY = 0.1
FREQUENCY_PENALTY = 0.1

# Chat Configuration
MAX_HISTORY_MESSAGES = 10
API_TIMEOUT = 10
MARKET_DATA_TIMEOUT = 5

# Simple greeting patterns for instant responses
GREETING_PATTERNS = [
    r'^hi$', r'^hello$', r'^hey$', r'^hi there$', r'^hello there$',
    r'^good morning$', r'^good afternoon$', r'^good evening$',
    r'^what\'s up$', r'^whats up$', r'^sup$', r'^yo$'
]

# Crypto-themed greeting responses
CRYPTO_GREETING_RESPONSES = [
    "Hi there! 🚀 Ready to dive into crypto? Ask me about prices, analysis, or any coin!",
    "Hello! 📈 I'm your crypto research assistant. What would you like to know about the markets today?",
    "Hey! 💎 Looking for crypto insights? I can help with trading, DeFi, NFTs, and more!",
    "Hi! ⚡ What's on your crypto watchlist today? I'm here to help with analysis and data!",
    "Hello! 🌟 Ready to explore the crypto universe? Ask me anything about blockchain and digital assets!",
    "Hey there! 🔥 The crypto markets are always moving. What can I help you research today?",
    "Hi! 🎯 Your crypto research companion is here. Ask me about any coin, trend, or strategy!",
    "Hello! ⭐ From Bitcoin to DeFi, I've got you covered. What's your crypto question?"
]

# Crypto-related keywords for market data enhancement
CRYPTO_KEYWORDS = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'price', 'market', 'crypto', 'cryptocurrency',
    'altcoin', 'defi', 'nft', 'blockchain', 'trading', 'pump', 'dump', 'moon',
    'hodl', 'whale', 'bull', 'bear', 'market cap', 'volume', 'doge', 'ada',
    'bnb', 'sol', 'matic', 'avax', 'dot', 'link', 'uni', 'sushi'
]

# Comprehensive crypto-focused system prompt
CRYPTO_SYSTEM_PROMPT = """You are CryptoBot, an advanced cryptocurrency research assistant powered by GPT-4 Turbo. You specialize in:

CRYPTOCURRENCY KNOWLEDGE:
- All cryptocurrencies (Bitcoin, Ethereum, altcoins, meme coins)
- Market analysis and price predictions
- Technical analysis and trading strategies
- Fundamental analysis and tokenomics
- Regulatory news and compliance
- Market cycles and sentiment analysis

DEFI & BLOCKCHAIN:
- DeFi protocols and yield farming
- Smart contracts and dApps
- Layer 1 and Layer 2 solutions
- Cross-chain bridges and interoperability
- Staking and governance tokens
- Liquidity pools and AMMs

TRADING & INVESTMENT:
- Risk management strategies
- Portfolio diversification
- Market cycles and sentiment analysis
- On-chain analytics and metrics
- Derivatives and futures trading
- Dollar-cost averaging strategies

NFT & WEB3:
- NFT marketplaces and collections
- Utility and gaming tokens
- Metaverse and virtual worlds
- Web3 infrastructure and tools
- Creator economy and royalties

MARKET DATA & ANALYTICS:
- Real-time price analysis
- Volume and liquidity analysis
- Market cap and dominance trends
- Fear & Greed Index interpretation
- Macro economic impacts
- Technical indicators and patterns

SECURITY & BEST PRACTICES:
- Wallet security and cold storage
- Avoiding scams and rug pulls
- Due diligence for new projects
- Smart contract auditing basics
- Private key management

COMMUNICATION STYLE:
- Provide accurate, up-to-date, and actionable insights
- Always include risk warnings for investment advice
- Use current data when possible and be specific about timeframes
- Keep responses informative yet accessible to both beginners and advanced users
- Use crypto emojis and terminology naturally
- Be enthusiastic but responsible about investment advice
- Explain complex concepts in simple terms when needed

RISK DISCLAIMER:
Always remind users that cryptocurrency investments are highly risky and volatile. Past performance doesn't guarantee future results. Users should do their own research (DYOR) and never invest more than they can afford to lose."""

# CoinGecko API parameters
MARKET_DATA_PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
    "sparkline": "false"
}

CRYPTO_DETAIL_PARAMS = {
    "localization": "false",
    "tickers": "false",
    "market_data": "true",
    "community_data": "true",
    "developer_data": "true"
}

PRICE_DATA_PARAMS = {
    "vs_currencies": "usd",
    "include_market_cap": "true",
    "include_24hr_vol": "true",
    "include_24hr_change": "true"
}

# Error messages
ERROR_MESSAGES = {
    'no_message': 'No message provided',
    'empty_message': 'Message cannot be empty',
    'api_key_missing': 'API key not configured. Please set OPENAI_API_KEY environment variable.',
    'client_not_initialized': 'OpenAI client not initialized',
    'invalid_crypto_id': 'Invalid crypto ID',
    'crypto_not_found': 'Cryptocurrency not found',
    'network_error': 'Network error occurred',
    'api_error': 'API error occurred',
    'internal_error': 'Internal server error',
    'endpoint_not_found': 'Endpoint not found',
    'method_not_allowed': 'Method not allowed'
}

# Success messages
SUCCESS_MESSAGES = {
    'healthy': 'Service is healthy',
    'data_fetched': 'Data fetched successfully'
}

# App metadata
APP_INFO = {
    'name': 'Enhanced Crypto Research Bot',
    'version': '2.0.0',
    'description': 'AI-powered cryptocurrency research assistant with streaming responses',
    'model': OPENAI_MODEL,
    'features': [
        'Real-time streaming responses',
        'Instant greeting responses',
        'Live market data integration',
        'Comprehensive error handling',
        'Crypto-focused AI assistant'
    ]
}