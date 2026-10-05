"""
Sample Data Generator
Generates synthetic cloud billing data for testing the pipeline.
"""

import csv
import random
import os
from datetime import date, timedelta

def generate_billing_data(days: int = 90, output_file: str = None):
    """Generate synthetic billing data for the specified number of days."""

    accounts = ['Production', 'Development', 'Staging']
    services = {
        'Production': ['EC2', 'S3', 'RDS', 'Lambda', 'CloudWatch', 'EBS', 'VPC'],
        'Development': ['EC2', 'S3', 'RDS', 'Lambda'],
        'Staging': ['EC2', 'S3', 'RDS']
    }
    regions = {
        'Production': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'Development': ['us-west-2', 'us-east-1'],
        'Staging': ['us-east-1']
    }
    teams = {
        'Production': ['Engineering', 'Data', 'ML-Team'],
        'Development': ['Engineering', 'Data'],
        'Staging': ['QA', 'Engineering']
    }
    projects = {
        'Production': ['Platform', 'Analytics', 'ML-Pipeline'],
        'Development': ['Platform', 'Analytics'],
        'Staging': ['Platform']
    }
    environments = {
        'Production': ['Prod'],
        'Development': ['Dev'],
        'Staging': ['UAT']
    }

    # Base costs per service
    base_costs = {
        'EC2': (800, 1500), 'S3': (30, 80), 'RDS': (250, 400),
        'Lambda': (15, 50), 'CloudWatch': (60, 120), 'EBS': (100, 200), 'VPC': (40, 70)
    }

    rows = []
    end_date = date.today()

    for day_offset in range(days):
        current_date = end_date - timedelta(days=day_offset)

        for account in accounts:
            for service in services[account]:
                # Not every service runs every day
                if random.random() < 0.3:
                    continue

                region = random.choice(regions[account])
                team = random.choice(teams[account])
                project = random.choice(projects[account])
                env = random.choice(environments[account])

                base_min, base_max = base_costs.get(service, (50, 200))
                cost = round(random.uniform(base_min, base_max), 2)

                # Inject occasional anomaly (5% chance)
                if random.random() < 0.05:
                    cost = round(cost * random.uniform(2.5, 5.0), 2)

                usage_map = {
                    'EC2': (round(random.uniform(200, 800), 1), 'hours'),
                    'S3': (round(random.uniform(100, 1000), 1), 'GB'),
                    'RDS': (round(random.uniform(200, 800), 1), 'hours'),
                    'Lambda': (random.randint(100000, 2000000), 'requests'),
                    'CloudWatch': (0, 'USD'),
                    'EBS': (round(random.uniform(500, 3000), 1), 'GB'),
                    'VPC': (0, 'USD')
                }
                usage_qty, usage_unit = usage_map.get(service, (0, 'USD'))

                rows.append({
                    'date': current_date.isoformat(),
                    'account_name': account,
                    'service_name': service,
                    'region': region,
                    'team_name': team,
                    'project_name': project,
                    'environment': env,
                    'cost': cost,
                    'usage_quantity': usage_qty,
                    'usage_unit': usage_unit,
                    'currency': 'USD',
                    'provider': 'AWS'
                })

    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), '..', 'raw', 'billing_data.csv')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} billing records -> {output_file}")
    return output_file


def generate_budget_data(output_file: str = None):
    """Generate sample budget data."""

    budgets = [
        ('Production', 'Engineering', 'Platform', 'Prod', 'Monthly', '2024-01-01', '2024-01-31', 15000),
        ('Production', 'Data', 'Analytics', 'Prod', 'Monthly', '2024-01-01', '2024-01-31', 5000),
        ('Production', 'ML-Team', 'ML-Pipeline', 'Prod', 'Monthly', '2024-01-01', '2024-01-31', 2000),
        ('Development', 'Engineering', 'Platform', 'Dev', 'Monthly', '2024-01-01', '2024-01-31', 3000),
        ('Development', 'Data', 'Analytics', 'Dev', 'Monthly', '2024-01-01', '2024-01-31', 1500),
        ('Staging', 'QA', 'Platform', 'UAT', 'Monthly', '2024-01-01', '2024-01-31', 2000),
    ]

    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), '..', 'raw', 'budget_data.csv')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['account_name', 'team_name', 'project_name', 'environment',
                         'budget_period', 'budget_start_date', 'budget_end_date',
                         'budget_amount', 'currency'])
        for b in budgets:
            writer.writerow(list(b) + ['USD'])

    print(f"Generated {len(budgets)} budget records -> {output_file}")
    return output_file


if __name__ == '__main__':
    generate_billing_data(days=90)
    generate_budget_data()
