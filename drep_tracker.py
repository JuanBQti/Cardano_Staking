#!/usr/bin/env python3
"""
DRep Tracker - Monitor the number of DReps over time from adastat.net
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
from typing import Optional, Dict, Any

class DRepTracker:
    def __init__(self, data_file: str = "drep_data.json", csv_file: str = "drep_data.csv"):
        self.data_file = data_file
        self.csv_file = csv_file
        self.url = "https://adastat.net/dreps"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_drep_count(self) -> Optional[int]:
        """Scrape the current number of DReps from the website"""
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for various patterns that might contain the DRep count
            # This will need to be adjusted based on the actual website structure
            
            # Try to find numbers that could be DRep count
            potential_counts = []
            
            # Look for text containing "DRep" or similar patterns
            for element in soup.find_all(text=True):
                text = element.strip()
                if 'drep' in text.lower() or 'delegated' in text.lower():
                    # Extract numbers from this text
                    import re
                    numbers = re.findall(r'\d+', text)
                    potential_counts.extend(numbers)
            
            # Look for common patterns in tables or cards
            for element in soup.find_all(['div', 'span', 'td', 'th'], class_=True):
                class_names = ' '.join(element.get('class', []))
                if any(keyword in class_names.lower() for keyword in ['count', 'number', 'total', 'drep']):
                    text = element.get_text(strip=True)
                    import re
                    numbers = re.findall(r'\d+', text)
                    potential_counts.extend(numbers)
            
            # Look for any large numbers that could be the count
            for element in soup.find_all(text=True):
                text = element.strip()
                if text.isdigit() and len(text) >= 2:  # At least 2 digits
                    potential_counts.append(text)
            
            # Return the most likely count (largest number found)
            if potential_counts:
                counts = [int(x) for x in potential_counts if x.isdigit()]
                if counts:
                    return max(counts)  # Return the largest number found
            
            print(f"Could not find DRep count. Found potential numbers: {potential_counts}")
            return None
            
        except Exception as e:
            print(f"Error scraping DRep count: {e}")
            return None
    
    def save_data(self, count: int, timestamp: str = None):
        """Save the DRep count to both JSON and CSV files"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Load existing data
        data = self.load_data()
        
        # Add new entry
        data.append({
            'timestamp': timestamp,
            'count': count,
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Save to JSON
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save to CSV
        with open(self.csv_file, 'w', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'count', 'datetime'])
                writer.writeheader()
                writer.writerows(data)
        
        print(f"Saved DRep count: {count} at {timestamp}")
    
    def load_data(self) -> list:
        """Load existing data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def plot_data(self, save_plot: bool = True):
        """Create a plot of DRep count over time"""
        data = self.load_data()
        if not data:
            print("No data to plot")
            return
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['count'], marker='o', linewidth=2, markersize=4)
        plt.title('Number of DReps Over Time', fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Number of DReps', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_plot:
            plt.savefig('drep_timeline.png', dpi=300, bbox_inches='tight')
            print("Plot saved as 'drep_timeline.png'")
        
        plt.show()
    
    def run_continuous_monitoring(self, interval_minutes: int = 60):
        """Run continuous monitoring of DRep count"""
        print(f"Starting continuous monitoring every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                count = self.get_drep_count()
                if count is not None:
                    self.save_data(count)
                else:
                    print("Failed to get DRep count, will retry next interval")
                
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    def get_current_status(self):
        """Get current DRep count and display recent history"""
        count = self.get_drep_count()
        if count is not None:
            print(f"Current DRep count: {count}")
            self.save_data(count)
        else:
            print("Could not retrieve current DRep count")
        
        # Show recent history
        data = self.load_data()
        if data:
            print("\nRecent DRep counts:")
            for entry in data[-5:]:  # Show last 5 entries
                print(f"  {entry['datetime']}: {entry['count']} DReps")

def main():
    tracker = DRepTracker()
    
    print("DRep Tracker - Monitor DReps from adastat.net")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Get current DRep count")
        print("2. Plot historical data")
        print("3. Start continuous monitoring")
        print("4. Show recent history")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            tracker.get_current_status()
        elif choice == '2':
            tracker.plot_data()
        elif choice == '3':
            try:
                interval = int(input("Enter monitoring interval in minutes (default 60): ") or "60")
                tracker.run_continuous_monitoring(interval)
            except ValueError:
                print("Invalid input, using default 60 minutes")
                tracker.run_continuous_monitoring()
        elif choice == '4':
            data = tracker.load_data()
            if data:
                print("\nRecent DRep counts:")
                for entry in data[-10:]:  # Show last 10 entries
                    print(f"  {entry['datetime']}: {entry['count']} DReps")
            else:
                print("No historical data available")
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    main()
