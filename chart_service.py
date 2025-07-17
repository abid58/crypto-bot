"""
Chart Service for Crypto Research Bot
Handles chart generation and data processing using Plotly
"""

import json
import logging
from datetime import datetime
import requests
import time
import random

logger = logging.getLogger(__name__)

# Optional imports for chart functionality
try:
    import plotly.graph_objects as go
    import plotly.utils
    import pandas as pd
    CHART_AVAILABLE = True
    logger.info("Plotly and pandas imported successfully")
except ImportError as e:
    CHART_AVAILABLE = False
    logger.warning(f"Plotly/pandas not available: {e}")

class ChartService:
    """Service class for handling cryptocurrency chart generation"""
    
    def __init__(self, coingecko_api_base, api_timeout):
        self.coingecko_api_base = coingecko_api_base
        self.api_timeout = api_timeout
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Minimum 1.2 seconds between requests
        logger.info("ChartService initialized")
    
    def is_available(self):
        """Check if chart functionality is available"""
        return CHART_AVAILABLE
    
    def _rate_limit(self):
        """Implement rate limiting to avoid 429 errors"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_chart_data(self, crypto_id, days="1825", interval="daily"):
        """
        Get chart data for a specific cryptocurrency
        
        Args:
            crypto_id (str): CoinGecko cryptocurrency ID
            days (str): Number of days of data to fetch (default: 1825 for 5 years)
            interval (str): Data interval (default: "daily")
            
        Returns:
            dict: Chart data and metadata
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Chart functionality not available. Install plotly and pandas.'
            }
        
        try:
            logger.info(f"Fetching chart data for {crypto_id}")
            
            # Apply rate limiting
            self._rate_limit()
            
            # Get historical data from CoinGecko
            url = f"{self.coingecko_api_base}/coins/{crypto_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": interval
            }
            
            # Add headers to look more like a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(
                url, 
                params=params, 
                timeout=self.api_timeout,
                headers=headers
            )
            
            if response.status_code == 429:
                logger.warning("Rate limit hit (429). Retrying with longer delay...")
                time.sleep(5)  # Wait 5 seconds before retry
                return self.get_chart_data(crypto_id, days, interval)  # Retry once
            
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': f'Cryptocurrency "{crypto_id}" not found'
                }
            elif response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code} - {response.text[:100]}'
                }
            
            data = response.json()
            
            # Process the data
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            if not prices:
                return {
                    'success': False,
                    'error': 'No price data available'
                }
            
            # Create chart
            chart_data = self._create_chart(prices, volumes)
            
            # Calculate additional metrics
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['volume'] = [vol[1] for vol in volumes] if volumes else [0] * len(prices)
            
            current_price = df['price'].iloc[-1]
            price_change_24h = 0
            if len(df) > 1:
                price_change_24h = ((df['price'].iloc[-1] - df['price'].iloc[-2]) / df['price'].iloc[-2] * 100)
            volume_24h = df['volume'].iloc[-1]
            
            logger.info(f"Chart data generated successfully for {crypto_id}")
            
            return {
                'success': True,
                'chart_data': chart_data,
                'current_price': current_price,
                'price_change_24h': price_change_24h,
                'volume_24h': volume_24h,
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Chart data request error: {str(e)}")
            return {
                'success': False,
                'error': 'Network error occurred'
            }
        except Exception as e:
            logger.error(f"Chart data error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to fetch chart data: {str(e)}'
            }
    
    def get_mock_chart_data(self, crypto_id):
        """
        Generate mock chart data for testing when API is unavailable
        """
        try:
            logger.info(f"Generating mock chart data for {crypto_id}")
            
            # Generate mock data
            import numpy as np
            from datetime import datetime, timedelta
            
            # Create 5 years of daily data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1825)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate realistic price data with trends and volatility
            np.random.seed(42)  # For reproducible results
            
            # Base price (different for each crypto)
            base_prices = {
                'bitcoin': 45000,
                'ethereum': 2800,
                'solana': 100,
                'binancecoin': 300,
                'cardano': 0.5,
                'ripple': 0.6,
                'avalanche-2': 35,
                'matic-network': 0.8,
                'dogecoin': 0.08,
                'polkadot': 7
            }
            
            base_price = base_prices.get(crypto_id, 100)
            
            # Generate price series with trend and noise
            n_days = len(dates)
            trend = np.linspace(0, 2, n_days)  # Upward trend
            noise = np.random.normal(0, 0.02, n_days)  # Daily volatility
            seasonal = 0.1 * np.sin(np.linspace(0, 4*np.pi, n_days))  # Seasonal pattern
            
            prices = base_price * (1 + trend + noise + seasonal)
            prices = np.maximum(prices, base_price * 0.1)  # Ensure positive prices
            
            # Generate volume data
            volumes = np.random.lognormal(15, 0.5, n_days) * (1 + 0.5 * np.abs(np.diff(prices, prepend=prices[0])))
            
            # Create DataFrame
            df = pd.DataFrame({
                'date': dates,
                'price': prices,
                'volume': volumes
            })
            
            # Create the chart
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['price'],
                mode='lines',
                name='Price',
                line=dict(color='#1f77b4', width=2),
                fill='tonexty',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            
            # Add volume bars
            colors = ['#2ca02c' if df['price'].iloc[i] >= df['price'].iloc[i-1] else '#d62728' 
                     for i in range(1, len(df))]
            colors.insert(0, '#2ca02c')
            
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.6,
                yaxis='y2'
            ))
            
            # Update layout
            fig.update_layout(
                title=None,
                xaxis=dict(
                    title=None,
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    gridwidth=1,
                    showline=True,
                    linecolor='rgba(0,0,0,0.2)',
                    linewidth=1,
                    rangeslider=dict(visible=False)
                ),
                yaxis=dict(
                    title=None,
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    gridwidth=1,
                    showline=True,
                    linecolor='rgba(0,0,0,0.2)',
                    linewidth=1,
                    side='right'
                ),
                yaxis2=dict(
                    title=None,
                    showgrid=False,
                    showline=False,
                    side='left',
                    overlaying='y',
                    showticklabels=False
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=50, t=30, b=50),
                height=300,
                showlegend=False,
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='rgba(0,0,0,0.2)',
                    font_size=12
                )
            )
            
            # Convert to JSON
            chart_json = plotly.utils.PlotlyJSONEncoder().encode(fig)
            
            return {
                'success': True,
                'chart_data': json.loads(chart_json),
                'current_price': df['price'].iloc[-1],
                'price_change_24h': ((df['price'].iloc[-1] - df['price'].iloc[-2]) / df['price'].iloc[-2] * 100) if len(df) > 1 else 0,
                'volume_24h': df['volume'].iloc[-1],
                'timestamp': datetime.now().isoformat(),
                'note': 'Mock data (API rate limited)'
            }
            
        except Exception as e:
            logger.error(f"Mock chart generation error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to generate mock chart: {str(e)}'
            }
    
    def _create_chart(self, prices, volumes):
        """
        Create a Plotly chart from price and volume data
        
        Args:
            prices (list): List of [timestamp, price] pairs
            volumes (list): List of [timestamp, volume] pairs
            
        Returns:
            dict: Plotly chart configuration
        """
        # Convert to pandas DataFrame
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['volume'] = [vol[1] for vol in volumes] if volumes else [0] * len(prices)
        
        # Create the chart
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['price'],
            mode='lines',
            name='Price',
            line=dict(color='#1f77b4', width=2),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
        
        # Add volume bars with color coding
        colors = self._get_volume_colors(df)
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6,
            yaxis='y2'
        ))
        
        # Update layout for clean, modern look
        fig.update_layout(
            title=None,
            xaxis=dict(
                title=None,
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                gridwidth=1,
                showline=True,
                linecolor='rgba(0,0,0,0.2)',
                linewidth=1,
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                title=None,
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                gridwidth=1,
                showline=True,
                linecolor='rgba(0,0,0,0.2)',
                linewidth=1,
                side='right'
            ),
            yaxis2=dict(
                title=None,
                showgrid=False,
                showline=False,
                side='left',
                overlaying='y',
                showticklabels=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=30, b=50),
            height=300,
            showlegend=False,
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='rgba(0,0,0,0.2)',
                font_size=12
            )
        )
        
        # Convert to JSON for frontend
        chart_json = plotly.utils.PlotlyJSONEncoder().encode(fig)
        return json.loads(chart_json)
    
    def _get_volume_colors(self, df):
        """
        Generate color array for volume bars based on price movement
        
        Args:
            df (DataFrame): Price data DataFrame
            
        Returns:
            list: List of colors for volume bars
        """
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append('#2ca02c')  # First bar is green
            else:
                # Green if price went up, red if down
                if df['price'].iloc[i] >= df['price'].iloc[i-1]:
                    colors.append('#2ca02c')  # Green
                else:
                    colors.append('#d62728')  # Red
        return colors
    
    def get_supported_cryptocurrencies(self):
        """Get list of supported cryptocurrencies for the chart selector"""
        return [
            {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC'},
            {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH'},
            {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL'},
            {'id': 'binancecoin', 'name': 'BNB', 'symbol': 'BNB'},
            {'id': 'cardano', 'name': 'Cardano', 'symbol': 'ADA'},
            {'id': 'ripple', 'name': 'XRP', 'symbol': 'XRP'},
            {'id': 'avalanche-2', 'name': 'Avalanche', 'symbol': 'AVAX'},
            {'id': 'matic-network', 'name': 'Polygon', 'symbol': 'MATIC'},
            {'id': 'dogecoin', 'name': 'Dogecoin', 'symbol': 'DOGE'},
            {'id': 'polkadot', 'name': 'Polkadot', 'symbol': 'DOT'}
        ]
    
    def get_timeframe_options(self):
        """Get available timeframe options"""
        return [
            {'value': '1D', 'label': '1 Day', 'days': '1'},
            {'value': '1W', 'label': '1 Week', 'days': '7'},
            {'value': '1M', 'label': '1 Month', 'days': '30'},
            {'value': '3M', 'label': '3 Months', 'days': '90'},
            {'value': '1Y', 'label': '1 Year', 'days': '365'},
            {'value': '5Y', 'label': '5 Years', 'days': '1825'}
        ] 