#!/usr/bin/env python3
"""
Polygon PoS Validator Behavior Analysis

This script analyzes validator behavior on Polygon PoS by examining:
1. Block proposal patterns
2. Validator voting timestamps
3. Concentration of votes around specific times
"""

import requests
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

class PolygonValidatorAnalyzer:
    def __init__(self, rpc_url="https://polygon-rpc.com/"):
        self.rpc_url = rpc_url
        self.session = requests.Session()
        
    def make_rpc_call(self, method, params=None):
        """Make an RPC call to the Polygon network"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        try:
            response = self.session.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"RPC Error: {data['error']}")
            
            return data['result']
        except Exception as e:
            print(f"Error making RPC call: {e}")
            return None
    
    def get_latest_block_number(self):
        """Get the latest block number"""
        result = self.make_rpc_call("eth_blockNumber")
        if result:
            return int(result, 16)
        return None
    
    def get_block_by_number(self, block_number):
        """Get block data by block number"""
        hex_block = hex(block_number)
        result = self.make_rpc_call("eth_getBlockByNumber", [hex_block, True])
        return result
    
    def get_block_by_hash(self, block_hash):
        """Get block data by block hash"""
        result = self.make_rpc_call("eth_getBlockByHash", [block_hash, True])
        return result
    
    def analyze_block_range(self, start_block, end_block):
        """Analyze a range of blocks for validator behavior"""
        print(f"Analyzing blocks {start_block} to {end_block}...")
        
        blocks_data = []
        validator_stats = defaultdict(list)
        
        for block_num in range(start_block, end_block + 1):
            print(f"Fetching block {block_num}...", end="\r")
            
            block_data = self.get_block_by_number(block_num)
            if not block_data:
                print(f"Failed to fetch block {block_num}")
                continue
            
            # Extract relevant information
            block_info = {
                'number': block_num,
                'timestamp': int(block_data['timestamp'], 16),
                'miner': block_data.get('miner', ''),
                'hash': block_data['hash'],
                'parent_hash': block_data['parentHash'],
                'gas_used': int(block_data['gasUsed'], 16),
                'gas_limit': int(block_data['gasLimit'], 16),
                'transaction_count': len(block_data.get('transactions', [])),
                'size': int(block_data['size'], 16)
            }
            
            blocks_data.append(block_info)
            
            # Track validator (miner) statistics
            if block_info['miner']:
                validator_stats[block_info['miner']].append({
                    'block_number': block_num,
                    'timestamp': block_info['timestamp'],
                    'gas_used': block_info['gas_used'],
                    'transaction_count': block_info['transaction_count']
                })
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        print(f"\nAnalyzed {len(blocks_data)} blocks")
        return blocks_data, validator_stats
    
    def analyze_voting_patterns(self, blocks_data):
        """Analyze voting patterns and timing concentration"""
        if not blocks_data:
            return None
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(blocks_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        df['minute'] = df['datetime'].dt.minute
        df['second'] = df['datetime'].dt.second
        
        # Calculate time differences between consecutive blocks
        df['time_diff'] = df['timestamp'].diff()
        df['time_diff_seconds'] = df['time_diff'] / 1000  # Convert from milliseconds
        
        # Analyze validator distribution
        validator_counts = df['miner'].value_counts()
        
        # Analyze timing patterns
        timing_analysis = {
            'total_blocks': len(df),
            'unique_validators': len(validator_counts),
            'avg_block_time': df['time_diff_seconds'].mean(),
            'median_block_time': df['time_diff_seconds'].median(),
            'min_block_time': df['time_diff_seconds'].min(),
            'max_block_time': df['time_diff_seconds'].max(),
            'validator_distribution': validator_counts.to_dict(),
            'hourly_distribution': df['hour'].value_counts().sort_index().to_dict(),
            'minute_distribution': df['minute'].value_counts().sort_index().to_dict()
        }
        
        return timing_analysis, df
    
    def plot_analysis(self, df, timing_analysis, output_dir="plots"):
        """Create visualizations of the analysis"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig_size = (15, 10)
        
        # 1. Block timing distribution
        plt.figure(figsize=fig_size)
        plt.subplot(2, 3, 1)
        plt.hist(df['time_diff_seconds'], bins=50, alpha=0.7, edgecolor='black')
        plt.title('Block Time Distribution')
        plt.xlabel('Time Between Blocks (seconds)')
        plt.ylabel('Frequency')
        plt.axvline(df['time_diff_seconds'].mean(), color='red', linestyle='--', label=f'Mean: {df["time_diff_seconds"].mean():.2f}s')
        plt.legend()
        
        # 2. Hourly distribution
        plt.subplot(2, 3, 2)
        hours = list(timing_analysis['hourly_distribution'].keys())
        counts = list(timing_analysis['hourly_distribution'].values())
        plt.bar(hours, counts, alpha=0.7, edgecolor='black')
        plt.title('Block Production by Hour of Day')
        plt.xlabel('Hour of Day')
        plt.ylabel('Number of Blocks')
        plt.xticks(range(0, 24, 2))
        
        # 3. Validator distribution
        plt.subplot(2, 3, 3)
        validator_counts = list(timing_analysis['validator_distribution'].values())
        plt.hist(validator_counts, bins=20, alpha=0.7, edgecolor='black')
        plt.title('Validator Block Production Distribution')
        plt.xlabel('Number of Blocks Produced')
        plt.ylabel('Number of Validators')
        
        # 4. Timeline of block production
        plt.subplot(2, 3, 4)
        plt.plot(df['datetime'], df['time_diff_seconds'], alpha=0.7)
        plt.title('Block Time Over Time')
        plt.xlabel('Time')
        plt.ylabel('Time Between Blocks (seconds)')
        plt.xticks(rotation=45)
        
        # 5. Gas usage over time
        plt.subplot(2, 3, 5)
        plt.plot(df['datetime'], df['gas_used'], alpha=0.7)
        plt.title('Gas Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Gas Used')
        plt.xticks(rotation=45)
        
        # 6. Transaction count distribution
        plt.subplot(2, 3, 6)
        plt.hist(df['transaction_count'], bins=30, alpha=0.7, edgecolor='black')
        plt.title('Transaction Count Distribution')
        plt.xlabel('Number of Transactions per Block')
        plt.ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/polygon_validator_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create a detailed validator analysis plot
        self.plot_validator_details(df, output_dir)
    
    def plot_validator_details(self, df, output_dir):
        """Create detailed validator analysis plots"""
        # Top validators by block production
        top_validators = df['miner'].value_counts().head(10)
        
        plt.figure(figsize=(15, 8))
        
        # Validator block production
        plt.subplot(2, 2, 1)
        top_validators.plot(kind='bar', alpha=0.7, edgecolor='black')
        plt.title('Top 10 Validators by Block Production')
        plt.xlabel('Validator Address')
        plt.ylabel('Number of Blocks')
        plt.xticks(rotation=45, ha='right')
        
        # Validator timing patterns
        plt.subplot(2, 2, 2)
        validator_timing = df.groupby('miner')['time_diff_seconds'].mean().sort_values(ascending=False)
        validator_timing.head(10).plot(kind='bar', alpha=0.7, edgecolor='black')
        plt.title('Average Block Time by Validator')
        plt.xlabel('Validator Address')
        plt.ylabel('Average Time Between Blocks (seconds)')
        plt.xticks(rotation=45, ha='right')
        
        # Gas efficiency by validator
        plt.subplot(2, 2, 3)
        gas_efficiency = df.groupby('miner')['gas_used'].mean().sort_values(ascending=False)
        gas_efficiency.head(10).plot(kind='bar', alpha=0.7, edgecolor='black')
        plt.title('Average Gas Usage by Validator')
        plt.xlabel('Validator Address')
        plt.ylabel('Average Gas Used')
        plt.xticks(rotation=45, ha='right')
        
        # Transaction throughput by validator
        plt.subplot(2, 2, 4)
        tx_throughput = df.groupby('miner')['transaction_count'].mean().sort_values(ascending=False)
        tx_throughput.head(10).plot(kind='bar', alpha=0.7, edgecolor='black')
        plt.title('Average Transaction Count by Validator')
        plt.xlabel('Validator Address')
        plt.ylabel('Average Transactions per Block')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/polygon_validator_details.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, timing_analysis, df):
        """Generate a comprehensive analysis report"""
        report = f"""
# Polygon PoS Validator Behavior Analysis Report

## Summary Statistics
- **Total Blocks Analyzed**: {timing_analysis['total_blocks']}
- **Unique Validators**: {timing_analysis['unique_validators']}
- **Average Block Time**: {timing_analysis['avg_block_time']:.2f} seconds
- **Median Block Time**: {timing_analysis['median_block_time']:.2f} seconds
- **Fastest Block Time**: {timing_analysis['min_block_time']:.2f} seconds
- **Slowest Block Time**: {timing_analysis['max_block_time']:.2f} seconds

## Validator Distribution
The top 10 most active validators:
"""
        
        for i, (validator, count) in enumerate(list(timing_analysis['validator_distribution'].items())[:10], 1):
            report += f"{i}. {validator[:10]}...: {count} blocks\n"
        
        report += f"""
## Timing Analysis
- **Hourly Distribution**: Blocks are distributed across hours as follows:
"""
        
        for hour, count in sorted(timing_analysis['hourly_distribution'].items()):
            report += f"  - Hour {hour:02d}:00: {count} blocks\n"
        
        # Calculate concentration metrics
        time_diffs = df['time_diff_seconds'].dropna()
        concentration_metrics = {
            'std_deviation': time_diffs.std(),
            'coefficient_of_variation': time_diffs.std() / time_diffs.mean(),
            'quartile_25': time_diffs.quantile(0.25),
            'quartile_75': time_diffs.quantile(0.75),
            'iqr': time_diffs.quantile(0.75) - time_diffs.quantile(0.25)
        }
        
        report += f"""
## Concentration Analysis
- **Standard Deviation**: {concentration_metrics['std_deviation']:.2f} seconds
- **Coefficient of Variation**: {concentration_metrics['coefficient_of_variation']:.2f}
- **25th Percentile**: {concentration_metrics['quartile_25']:.2f} seconds
- **75th Percentile**: {concentration_metrics['quartile_75']:.2f} seconds
- **Interquartile Range**: {concentration_metrics['iqr']:.2f} seconds

## Key Findings
"""
        
        # Analyze concentration patterns
        if concentration_metrics['coefficient_of_variation'] < 0.1:
            report += "- **Low Variation**: Block times are very consistent, indicating stable validator performance.\n"
        elif concentration_metrics['coefficient_of_variation'] < 0.3:
            report += "- **Moderate Variation**: Block times show some variation but within acceptable ranges.\n"
        else:
            report += "- **High Variation**: Block times show significant variation, which may indicate network instability or validator performance issues.\n"
        
        # Check for timing patterns
        hourly_std = np.std(list(timing_analysis['hourly_distribution'].values()))
        if hourly_std < 5:
            report += "- **Even Distribution**: Blocks are evenly distributed throughout the day.\n"
        else:
            report += "- **Uneven Distribution**: Blocks show concentration at certain hours, indicating potential validator scheduling patterns.\n"
        
        return report

def main():
    """Main function to run the analysis"""
    print("Polygon PoS Validator Behavior Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = PolygonValidatorAnalyzer()
    
    # Get latest block number
    latest_block = analyzer.get_latest_block_number()
    if not latest_block:
        print("Failed to get latest block number")
        return
    
    print(f"Latest block number: {latest_block}")
    
    # Analyze recent blocks (adjust range as needed)
    end_block = latest_block
    start_block = end_block - 100  # Analyze last 100 blocks
    
    print(f"Analyzing blocks {start_block} to {end_block}")
    
    # Perform analysis
    blocks_data, validator_stats = analyzer.analyze_block_range(start_block, end_block)
    
    if not blocks_data:
        print("No block data retrieved")
        return
    
    # Analyze patterns
    timing_analysis, df = analyzer.analyze_voting_patterns(blocks_data)
    
    if timing_analysis:
        # Generate and save report
        report = analyzer.generate_report(timing_analysis, df)
        with open('polygon_validator_report.md', 'w') as f:
            f.write(report)
        
        print("\nAnalysis Report:")
        print(report)
        
        # Create visualizations
        print("\nGenerating visualizations...")
        analyzer.plot_analysis(df, timing_analysis)
        
        print("\nAnalysis complete! Check the generated plots and report.")
    else:
        print("Failed to analyze timing patterns")

if __name__ == "__main__":
    main()
