#!/usr/bin/env python3
"""
Google Cloud Storage Cost Optimizer

This script analyzes your Google Cloud Storage usage and settings,
then recommends and optionally applies optimizations to reduce costs.
"""

import argparse
import datetime
import json
import os
import sys
from typing import Dict, List, Tuple, Optional

try:
    from google.cloud import storage
    from google.cloud.storage import Bucket
    from google.cloud import billing
    from google.cloud.billing import CloudCatalogClient
    from tabulate import tabulate
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "google-cloud-storage", "google-cloud-billing", "tabulate"])
    from google.cloud import storage
    from google.cloud.storage import Bucket
    from google.cloud import billing
    from google.cloud.billing import CloudCatalogClient
    from tabulate import tabulate

# Storage class pricing (approximate, may vary by region)
STORAGE_CLASS_PRICING = {
    'STANDARD': 0.020,  # per GB/month
    'NEARLINE': 0.010,  # per GB/month
    'COLDLINE': 0.004,  # per GB/month
    'ARCHIVE': 0.0012,  # per GB/month
}

# Early deletion fees
EARLY_DELETION_FEES = {
    'STANDARD': 0,
    'NEARLINE': 30,  # days
    'COLDLINE': 90,  # days
    'ARCHIVE': 365,  # days
}

# Retrieval costs per GB
RETRIEVAL_COSTS = {
    'STANDARD': 0,
    'NEARLINE': 0.01,
    'COLDLINE': 0.02,
    'ARCHIVE': 0.05,
}


class GCSCostOptimizer:
    """Analyzes and optimizes Google Cloud Storage costs."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """Initialize the optimizer with project details."""
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.catalog_client = CloudCatalogClient()
        self.buckets_data = []
        self.total_current_cost = 0
        self.total_optimized_cost = 0
        
    def analyze_storage(self) -> None:
        """Analyze all buckets in the project."""
        print(f"Analyzing storage for project: {self.project_id}")
        
        buckets = list(self.storage_client.list_buckets())
        if not buckets:
            print("No buckets found in this project.")
            return
            
        print(f"Found {len(buckets)} buckets. Analyzing each bucket...")
        
        for bucket in buckets:
            self._analyze_bucket(bucket)
            
        print("\nAnalysis complete!")
        
    def _analyze_bucket(self, bucket: Bucket) -> None:
        """Analyze a single bucket for optimization opportunities."""
        print(f"Analyzing bucket: {bucket.name}")
        
        # Get bucket metadata
        bucket_data = {
            'name': bucket.name,
            'location': bucket.location,
            'storage_class': bucket.storage_class,
            'size_bytes': 0,
            'object_count': 0,
            'access_frequency': {},
            'last_accessed': {},
            'current_cost': 0,
            'recommendations': [],
            'optimized_cost': 0,
            'savings': 0,
        }
        
        # Analyze objects
        blobs = list(self.storage_client.list_blobs(bucket.name))
        bucket_data['object_count'] = len(blobs)
        
        # Calculate total size and analyze access patterns
        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        ninety_days_ago = now - datetime.timedelta(days=90)
        year_ago = now - datetime.timedelta(days=365)
        
        access_counts = {'recent': 0, 'medium': 0, 'rare': 0, 'cold': 0}
        
        for blob in blobs:
            bucket_data['size_bytes'] += blob.size
            
            # Check last access time (if available)
            if hasattr(blob, 'time_created'):
                created = blob.time_created
                
                # Simulate access patterns (in a real scenario, you'd use actual access logs)
                if created > thirty_days_ago:
                    access_counts['recent'] += 1
                elif created > ninety_days_ago:
                    access_counts['medium'] += 1
                elif created > year_ago:
                    access_counts['rare'] += 1
                else:
                    access_counts['cold'] += 1
        
        bucket_data['access_frequency'] = access_counts
        
        # Calculate current monthly cost
        size_gb = bucket_data['size_bytes'] / (1024 ** 3)
        current_rate = STORAGE_CLASS_PRICING.get(bucket.storage_class, STORAGE_CLASS_PRICING['STANDARD'])
        bucket_data['current_cost'] = size_gb * current_rate
        self.total_current_cost += bucket_data['current_cost']
        
        # Generate recommendations
        self._generate_recommendations(bucket_data)
        
        self.buckets_data.append(bucket_data)
        
    def _generate_recommendations(self, bucket_data: Dict) -> None:
        """Generate cost optimization recommendations for a bucket."""
        size_gb = bucket_data['size_bytes'] / (1024 ** 3)
        access_freq = bucket_data['access_frequency']
        
        # Default to current cost
        bucket_data['optimized_cost'] = bucket_data['current_cost']
        
        # Recommend storage class changes based on access patterns
        current_class = bucket_data['storage_class']
        cold_ratio = (access_freq.get('rare', 0) + access_freq.get('cold', 0)) / max(bucket_data['object_count'], 1)
        
        recommendations = []
        
        # Storage class recommendations
        if current_class == 'STANDARD' and cold_ratio > 0.7:
            if cold_ratio > 0.9:
                new_class = 'ARCHIVE' if access_freq.get('cold', 0) > access_freq.get('rare', 0) else 'COLDLINE'
                new_cost = size_gb * STORAGE_CLASS_PRICING[new_class]
                savings = bucket_data['current_cost'] - new_cost
                recommendations.append({
                    'type': 'storage_class',
                    'action': f"Change storage class from {current_class} to {new_class}",
                    'savings': savings,
                    'details': f"Estimated monthly savings: ${savings:.2f}"
                })
                bucket_data['optimized_cost'] = new_cost
            else:
                new_class = 'NEARLINE'
                new_cost = size_gb * STORAGE_CLASS_PRICING[new_class]
                savings = bucket_data['current_cost'] - new_cost
                recommendations.append({
                    'type': 'storage_class',
                    'action': f"Change storage class from {current_class} to {new_class}",
                    'savings': savings,
                    'details': f"Estimated monthly savings: ${savings:.2f}"
                })
                bucket_data['optimized_cost'] = new_cost
        
        # Lifecycle policy recommendations
        if not recommendations:
            if cold_ratio > 0.3:
                savings = bucket_data['current_cost'] * 0.3  # Approximate savings
                recommendations.append({
                    'type': 'lifecycle',
                    'action': "Implement lifecycle policy to transition older objects to cheaper storage classes",
                    'savings': savings,
                    'details': (
                        "Suggested policy: Move objects older than 30 days to NEARLINE, "
                        "90 days to COLDLINE, and 365 days to ARCHIVE"
                    )
                })
                bucket_data['optimized_cost'] = bucket_data['current_cost'] - savings
        
        # Object versioning check
        if bucket_data['object_count'] > 1000:
            recommendations.append({
                'type': 'versioning',
                'action': "Review object versioning settings",
                'savings': 0,  # Cannot estimate without knowing versioning status
                'details': "If enabled, consider adding lifecycle rules to delete old versions"
            })
        
        bucket_data['recommendations'] = recommendations
        bucket_data['savings'] = bucket_data['current_cost'] - bucket_data['optimized_cost']
        self.total_optimized_cost += bucket_data['optimized_cost']
    
    def display_results(self) -> None:
        """Display analysis results and recommendations."""
        if not self.buckets_data:
            print("No data to display. Run analyze_storage() first.")
            return
        
        print("\n===== STORAGE COST OPTIMIZATION REPORT =====\n")
        
        # Summary table
        summary_data = []
        for bucket in self.buckets_data:
            size_gb = bucket['size_bytes'] / (1024 ** 3)
            summary_data.append([
                bucket['name'],
                bucket['storage_class'],
                f"{size_gb:.2f} GB",
                bucket['object_count'],
                f"${bucket['current_cost']:.2f}",
                f"${bucket['optimized_cost']:.2f}",
                f"${bucket['savings']:.2f}",
                f"{(bucket['savings'] / max(bucket['current_cost'], 0.01)) * 100:.1f}%"
            ])
        
        print(tabulate(
            summary_data,
            headers=["Bucket", "Storage Class", "Size", "Objects", "Current Cost", "Optimized Cost", "Savings", "Savings %"],
            tablefmt="grid"
        ))
        
        # Total savings
        total_savings = self.total_current_cost - self.total_optimized_cost
        savings_percent = (total_savings / max(self.total_current_cost, 0.01)) * 100
        
        print(f"\nTotal Current Monthly Cost: ${self.total_current_cost:.2f}")
        print(f"Total Optimized Monthly Cost: ${self.total_optimized_cost:.2f}")
        print(f"Total Monthly Savings: ${total_savings:.2f} ({savings_percent:.1f}%)")
        
        # Detailed recommendations
        print("\n===== DETAILED RECOMMENDATIONS =====\n")
        
        for bucket in self.buckets_data:
            if bucket['recommendations']:
                print(f"\nBucket: {bucket['name']}")
                for i, rec in enumerate(bucket['recommendations'], 1):
                    print(f"  {i}. {rec['action']}")
                    print(f"     {rec['details']}")
                    if rec['savings'] > 0:
                        print(f"     Estimated savings: ${rec['savings']:.2f}/month")
            else:
                print(f"\nBucket: {bucket['name']} - No optimization recommendations")
    
    def apply_recommendations(self, auto_approve: bool = False) -> None:
        """Apply the recommended optimizations."""
        if not self.buckets_data:
            print("No recommendations to apply. Run analyze_storage() first.")
            return
        
        print("\n===== APPLYING RECOMMENDATIONS =====\n")
        
        for bucket_data in self.buckets_data:
            if not bucket_data['recommendations']:
                continue
                
            bucket_name = bucket_data['name']
            print(f"Processing bucket: {bucket_name}")
            
            for rec in bucket_data['recommendations']:
                print(f"  - {rec['action']}")
                
                if not auto_approve:
                    response = input("    Apply this recommendation? (y/n): ").lower()
                    if response != 'y':
                        print("    Skipped.")
                        continue
                
                try:
                    if rec['type'] == 'storage_class':
                        # Change default storage class
                        bucket = self.storage_client.get_bucket(bucket_name)
                        new_class = rec['action'].split(' ')[-1]
                        bucket.storage_class = new_class
                        bucket.patch()
                        print(f"    ✓ Changed default storage class to {new_class}")
                    
                    elif rec['type'] == 'lifecycle':
                        # Add lifecycle rules
                        bucket = self.storage_client.get_bucket(bucket_name)
                        lifecycle_rules = {
                            'rule': [
                                {
                                    'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
                                    'condition': {'age': 30}
                                },
                                {
                                    'action': {'type': 'SetStorageClass', 'storageClass': 'COLDLINE'},
                                    'condition': {'age': 90}
                                },
                                {
                                    'action': {'type': 'SetStorageClass', 'storageClass': 'ARCHIVE'},
                                    'condition': {'age': 365}
                                }
                            ]
                        }
                        bucket.lifecycle_rules = lifecycle_rules
                        bucket.patch()
                        print("    ✓ Added lifecycle rules")
                    
                    elif rec['type'] == 'versioning':
                        print("    ℹ Manual review required for versioning settings")
                        
                except Exception as e:
                    print(f"    ✗ Error applying recommendation: {str(e)}")
        
        print("\nRecommendations applied. Run analyze_storage() again to see the updated state.")
    
    def export_report(self, filename: str = "gcs_optimization_report.json") -> None:
        """Export the analysis report to a file."""
        if not self.buckets_data:
            print("No data to export. Run analyze_storage() first.")
            return
        
        report = {
            'project_id': self.project_id,
            'generated_at': datetime.datetime.now().isoformat(),
            'summary': {
                'total_buckets': len(self.buckets_data),
                'total_current_cost': self.total_current_cost,
                'total_optimized_cost': self.total_optimized_cost,
                'total_savings': self.total_current_cost - self.total_optimized_cost,
                'savings_percent': ((self.total_current_cost - self.total_optimized_cost) / 
                                   max(self.total_current_cost, 0.01)) * 100
            },
            'buckets': self.buckets_data
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report exported to {filename}")


def main():
    """Main function to run the optimizer."""
    parser = argparse.ArgumentParser(description="Google Cloud Storage Cost Optimizer")
    parser.add_argument("--project", "-p", required=True, help="Google Cloud Project ID")
    parser.add_argument("--credentials", "-c", help="Path to service account credentials JSON file")
    parser.add_argument("--apply", "-a", action="store_true", help="Apply recommended optimizations")
    parser.add_argument("--auto-approve", action="store_true", help="Automatically approve all recommendations")
    parser.add_argument("--export", "-e", help="Export report to specified file")
    
    args = parser.parse_args()
    
    try:
        optimizer = GCSCostOptimizer(args.project, args.credentials)
        optimizer.analyze_storage()
        optimizer.display_results()
        
        if args.apply:
            optimizer.apply_recommendations(args.auto_approve)
        
        if args.export:
            optimizer.export_report(args.export)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
