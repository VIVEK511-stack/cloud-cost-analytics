"""
Model Evaluation Module
Evaluates ML model performance with metrics and visualizations.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, Any


class ModelEvaluator:
    """Evaluates and visualizes ML model performance."""

    def __init__(self, output_dir: str = 'output/charts'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def evaluate_regression(self, y_true, y_pred, model_name: str = 'Model') -> Dict[str, float]:
        """Evaluate regression model performance."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        metrics = {
            'MAE': round(mae, 2),
            'RMSE': round(rmse, 2),
            'R2': round(r2, 4),
            'MAPE': round(mape, 2)
        }

        print(f"\n{model_name} Regression Metrics:")
        print(f"  MAE:  ${mae:,.2f}")
        print(f"  RMSE: ${rmse:,.2f}")
        print(f"  R2:   {r2:.4f}")
        print(f"  MAPE: {mape:.2f}%")

        return metrics

    def evaluate_classification(self, y_true, y_pred, model_name: str = 'Model') -> Dict[str, float]:
        """Evaluate classification model performance."""
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)

        metrics = {
            'Accuracy': round(accuracy, 4),
            'Precision': round(precision, 4),
            'Recall': round(recall, 4),
            'F1 Score': round(f1, 4)
        }

        print(f"\n{model_name} Classification Metrics:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")

        return metrics

    def plot_actual_vs_predicted(self, y_true, y_pred, model_name: str = 'Model'):
        """Plot actual vs predicted values."""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(y_true, y_pred, alpha=0.5, color='#2E86AB')
        ax.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()],
               'r--', linewidth=2, label='Perfect Prediction')
        ax.set_xlabel('Actual Cost ($)')
        ax.set_ylabel('Predicted Cost ($)')
        ax.set_title(f'{model_name}: Actual vs Predicted', fontsize=14, fontweight='bold')
        ax.legend()
        path = os.path.join(self.output_dir, f'{model_name.lower().replace(" ", "_")}_actual_vs_predicted.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot_residuals(self, y_true, y_pred, model_name: str = 'Model'):
        """Plot residual distribution."""
        residuals = y_true - y_pred
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(residuals, bins=30, color='#2E86AB', edgecolor='white', alpha=0.7)
        ax.axvline(0, color='red', linestyle='--', linewidth=2)
        ax.set_xlabel('Residual ($)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{model_name}: Residual Distribution', fontsize=14, fontweight='bold')
        path = os.path.join(self.output_dir, f'{model_name.lower().replace(" ", "_")}_residuals.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot_confusion_matrix(self, y_true, y_pred, labels: list, model_name: str = 'Model'):
        """Plot confusion matrix for classification."""
        cm = confusion_matrix(y_true, y_pred)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=labels, yticklabels=labels)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(f'{model_name}: Confusion Matrix', fontsize=14, fontweight='bold')
        path = os.path.join(self.output_dir, f'{model_name.lower().replace(" ", "_")}_confusion_matrix.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot_feature_importance(self, features: list, importance: list, model_name: str = 'Model'):
        """Plot feature importance."""
        fig, ax = plt.subplots(figsize=(10, 6))
        sorted_idx = np.argsort(importance)
        ax.barh(range(len(sorted_idx)), np.array(importance)[sorted_idx], color='#2E86AB')
        ax.set_yticks(range(len(sorted_idx)))
        ax.set_yticklabels(np.array(features)[sorted_idx])
        ax.set_xlabel('Importance')
        ax.set_title(f'{model_name}: Feature Importance', fontsize=14, fontweight='bold')
        path = os.path.join(self.output_dir, f'{model_name.lower().replace(" ", "_")}_feature_importance.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")
