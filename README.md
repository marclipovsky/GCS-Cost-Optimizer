# 🚀 GCS Cost Optimizer

![Google Cloud Storage](https://img.shields.io/badge/Google_Cloud-Storage-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.6+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

**Stop overpaying for Google Cloud Storage!** This utility analyzes your GCS buckets and recommends optimizations to reduce your monthly bill.

## 📊 Features

- **Complete Storage Analysis**: Scans all buckets in your GCP project
- **Smart Recommendations**: Suggests storage class changes based on access patterns
- **Lifecycle Policy Creation**: Recommends and implements optimal lifecycle policies
- **Cost Savings Estimates**: Shows potential monthly and annual savings
- **Interactive Application**: Apply changes with confirmation or auto-approve
- **Exportable Reports**: Save analysis results as JSON for future reference

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gcs-cost-optimizer.git
cd gcs-cost-optimizer

# Install dependencies
pip install google-cloud-storage google-cloud-billing tabulate
```

## 🔑 Authentication

Before running the tool, you need to set up Google Cloud authentication:

```bash
# Set up application default credentials
gcloud auth application-default login

# Or specify a service account key file when running the tool
```

## 🚀 Usage

```bash
# Basic usage with your project ID
python gcs_cost_optimizer.py --project YOUR_PROJECT_ID

# Use a specific service account credentials file
python gcs_cost_optimizer.py --project YOUR_PROJECT_ID --credentials path/to/credentials.json

# Apply recommended optimizations (with confirmation prompts)
python gcs_cost_optimizer.py --project YOUR_PROJECT_ID --apply

# Apply all recommendations automatically without prompts
python gcs_cost_optimizer.py --project YOUR_PROJECT_ID --apply --auto-approve

# Export the analysis report to a file
python gcs_cost_optimizer.py --project YOUR_PROJECT_ID --export report.json
```

## 📋 Sample Output

```
===== STORAGE COST OPTIMIZATION REPORT =====

+------------------+-------------+----------+---------+---------------+----------------+----------+----------+
| Bucket           | Storage     | Size     | Objects | Current Cost  | Optimized Cost | Savings  | Savings % |
+------------------+-------------+----------+---------+---------------+----------------+----------+----------+
| my-app-assets    | STANDARD    | 156.42 GB| 12,345  | $3.13         | $1.56          | $1.57    | 50.0%    |
| my-app-backups   | STANDARD    | 892.10 GB| 532     | $17.84        | $3.57          | $14.27   | 80.0%    |
| my-app-logs      | NEARLINE    | 45.30 GB | 8,921   | $0.45         | $0.45          | $0.00    | 0.0%     |
+------------------+-------------+----------+---------+---------------+----------------+----------+----------+

Total Current Monthly Cost: $21.42
Total Optimized Monthly Cost: $5.58
Total Monthly Savings: $15.84 (74.0%)

===== DETAILED RECOMMENDATIONS =====

Bucket: my-app-assets
  1. Change storage class from STANDARD to NEARLINE
     Estimated monthly savings: $1.57/month

Bucket: my-app-backups
  1. Change storage class from STANDARD to ARCHIVE
     Estimated monthly savings: $14.27/month
  2. Implement lifecycle policy to transition older objects to cheaper storage classes
     Suggested policy: Move objects older than 30 days to NEARLINE, 90 days to COLDLINE, and 365 days to ARCHIVE
```

## 💡 How It Works

1. **Analysis**: The tool examines each bucket's metadata, object count, size, and access patterns
2. **Recommendation Engine**: Based on the analysis, it suggests:
   - Storage class changes (STANDARD → NEARLINE → COLDLINE → ARCHIVE)
   - Lifecycle policies for automatic transitions
   - Versioning optimizations
3. **Cost Calculation**: Estimates current and optimized costs using Google Cloud pricing
4. **Implementation**: Optionally applies the recommended changes to your buckets

## ⚠️ Important Notes

- **Access Pattern Simulation**: The tool uses object creation dates to simulate access patterns. For more accurate results, consider implementing detailed access logging.
- **Pricing Approximation**: Storage costs are approximated and may vary by region.
- **Test First**: Always run without the `--apply` flag first to review recommendations.
- **Permissions**: Requires Storage Admin permissions to apply changes.

## 💰 Did This Tool Save You Money?

If this tool helped reduce your Google Cloud costs, consider:

- ⭐ Starring the repository
- 🍴 Forking and contributing improvements
- ☕ [Buying me a coffee](https://buymeacoffee.com/marclipovsky)

**Every cup of coffee helps fuel more open-source tools to optimize your cloud costs!**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<p align="center">
  <i>Developed with ❤️ by <a href="https://github.com/marclipovsky">Marc Lipovsky</a></i>
</p>
