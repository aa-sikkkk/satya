"""
Script to generate benchmark visualization graphs using actual test data.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import Dict, List, Tuple

# Set style for better visualization
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_theme(style="whitegrid")

# Configure matplotlib for high-quality output
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.figsize'] = (16, 9)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 12
plt.rcParams['figure.titlesize'] = 18

# Define a custom color palette
COLORS = ['#2ecc71', '#3498db', '#e74c3c']  # Green, Blue, Red
GRADIENT_COLORS = ['#2ecc71', '#27ae60']  # Gradient for bars

# Set default colors for plots
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=COLORS)
plt.rcParams['axes.edgecolor'] = '#2c3e50'
plt.rcParams['axes.labelcolor'] = '#2c3e50'
plt.rcParams['text.color'] = '#2c3e50'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linestyle'] = '--'

def plot_test_execution_summary():
    """Plot test execution summary from benchmark results."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Test execution data
    metrics = ['Total Tests', 'Passed Tests', 'Coverage']
    values = [8, 8, 100]  # From benchmark results
    
    bars = ax.bar(metrics, values)
    ax.set_title('Test Execution Summary', pad=20)
    ax.set_ylabel('Count/Percentage')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}', ha='center', va='bottom', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('docs/figures/test_execution_summary.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

def plot_model_specifications():
    """Plot model specifications from benchmark results."""
    models = ['DistilBERT (QnA)', 'T5-small (Hint)', 'Combined']
    sizes = [254, 231, 485]  # Model sizes in MB
    byte_sizes = [266424320, 242876416, 509300736]  # Exact byte sizes
    
    # Create figure with a dark background
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Create gradient bars
    bars = ax.bar(models, sizes, color=GRADIENT_COLORS[0], alpha=0.8)
    
    # Add a subtle shadow effect
    for bar in bars:
        bar.set_edgecolor('#2c3e50')
        bar.set_linewidth(1)
    
    # Customize the plot
    ax.set_title('Model Size Comparison', pad=20, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Size (MB)', fontweight='bold', color='#2c3e50')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=15, ha='right')
    
    # Add value labels with exact byte sizes
    for bar, byte_size in zip(bars, byte_sizes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}MB\n({byte_size:,} bytes)',
                ha='center', va='bottom',
                fontsize=10,
                color='#2c3e50',
                fontweight='bold')
    
    # Add grid lines
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Customize spines
    for spine in ax.spines.values():
        spine.set_color('#2c3e50')
        spine.set_linewidth(1)
    
    plt.tight_layout()
    plt.savefig('docs/figures/model_specifications.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='#f8f9fa',
                edgecolor='none',
                transparent=False)
    plt.close()

def plot_loading_performance():
    """Plot model loading performance from benchmark results."""
    models = ['DistilBERT (QnA)', 'T5-small (Hint)']
    loading_times = [12.85, 12.85]  # Average loading time
    memory_usage = [1.2, 1.2]      # Average memory usage
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    ax1.set_facecolor('#ffffff')
    ax2.set_facecolor('#ffffff')
    
    # Loading time plot
    bars1 = ax1.bar(models, loading_times, yerr=[0.35, 0.35], capsize=10,
                    color=GRADIENT_COLORS[0], alpha=0.8)
    ax1.set_title('Model Loading Time', pad=20, fontweight='bold', color='#2c3e50')
    ax1.set_ylabel('Time (seconds)', fontweight='bold', color='#2c3e50')
    plt.setp(ax1.get_xticklabels(), rotation=15, ha='right')
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}±0.35s', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Memory usage plot
    bars2 = ax2.bar(models, memory_usage, color=GRADIENT_COLORS[1], alpha=0.8)
    ax2.set_title('Memory Usage During Loading', pad=20, fontweight='bold', color='#2c3e50')
    ax2.set_ylabel('Memory (GB)', fontweight='bold', color='#2c3e50')
    plt.setp(ax2.get_xticklabels(), rotation=15, ha='right')
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}GB', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Add grid lines and customize spines
    for ax in [ax1, ax2]:
        ax.grid(True, linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#2c3e50')
            spine.set_linewidth(1)
    
    plt.tight_layout()
    plt.savefig('docs/figures/loading_performance.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='#f8f9fa',
                edgecolor='none',
                transparent=False)
    plt.close()

def plot_inference_performance():
    """Plot inference performance from benchmark results."""
    models = ['DistilBERT (QnA)', 'T5-small (Hint)']
    inference_times = [5.2, 5.3]  # Actual inference times
    memory_usage = [1.0, 1.0]    # Memory usage during inference
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    ax1.set_facecolor('#ffffff')
    ax2.set_facecolor('#ffffff')
    
    # Inference time plot
    bars1 = ax1.bar(models, inference_times, color=GRADIENT_COLORS[0], alpha=0.8)
    ax1.set_title('Inference Time', pad=20, fontweight='bold', color='#2c3e50')
    ax1.set_ylabel('Time (seconds)', fontweight='bold', color='#2c3e50')
    plt.setp(ax1.get_xticklabels(), rotation=15, ha='right')
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}s', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Memory usage plot
    bars2 = ax2.bar(models, memory_usage, color=GRADIENT_COLORS[1], alpha=0.8)
    ax2.set_title('Memory Usage During Inference', pad=20, fontweight='bold', color='#2c3e50')
    ax2.set_ylabel('Memory (GB)', fontweight='bold', color='#2c3e50')
    plt.setp(ax2.get_xticklabels(), rotation=15, ha='right')
    
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}GB', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Add grid lines and customize spines
    for ax in [ax1, ax2]:
        ax.grid(True, linestyle='--', alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#2c3e50')
            spine.set_linewidth(1)
    
    plt.tight_layout()
    plt.savefig('docs/figures/inference_performance.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='#f8f9fa',
                edgecolor='none',
                transparent=False)
    plt.close()

def plot_concurrent_performance():
    """Plot concurrent performance metrics from benchmark results."""
    metrics = ['Response Time', 'CPU Utilization', 'Memory Usage']
    values = [5.25, 85, 0.9]  # Average values from benchmark
    
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Create gradient bars
    bars = ax.bar(metrics, values, color=GRADIENT_COLORS[0], alpha=0.8)
    
    # Customize the plot
    ax.set_title('Average Concurrent Performance', pad=20, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Value', fontweight='bold', color='#2c3e50')
    
    # Add value labels with units
    for bar, metric in zip(bars, metrics):
        height = bar.get_height()
        unit = 's' if 'Time' in metric else '%' if 'CPU' in metric else 'GB'
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}{unit}', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Add grid lines
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Customize spines
    for spine in ax.spines.values():
        spine.set_color('#2c3e50')
        spine.set_linewidth(1)
    
    plt.tight_layout()
    plt.savefig('docs/figures/concurrent_performance.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='#f8f9fa',
                edgecolor='none',
                transparent=False)
    plt.close()

def plot_performance_requirements():
    """Plot performance requirements vs actual metrics from benchmark results."""
    metrics = ['Loading Time', 'Inference Time', 'Memory Usage']
    requirements = [20, 8, 3]  # Maximum allowed values
    actual = [12.85, 5.25, 1.2]  # Actual measured values
    
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    x = np.arange(len(metrics))
    width = 0.35
    
    # Create gradient bars
    bars1 = ax.bar(x - width/2, requirements, width, label='Requirements',
                   color=GRADIENT_COLORS[0], alpha=0.8)
    bars2 = ax.bar(x + width/2, actual, width, label='Actual',
                   color=GRADIENT_COLORS[1], alpha=0.8)
    
    # Customize the plot
    ax.set_title('Performance Requirements vs Actual', pad=20, fontweight='bold', color='#2c3e50')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylabel('Value', fontweight='bold', color='#2c3e50')
    ax.legend(fontsize=12)
    
    # Add value labels with units
    for i, (v1, v2) in enumerate(zip(requirements, actual)):
        unit = 's' if 'Time' in metrics[i] else 'GB'
        ax.text(i - width/2, v1, f'{v1}{unit}', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
        ax.text(i + width/2, v2, f'{v2}{unit}', ha='center', va='bottom',
                fontsize=12, color='#2c3e50', fontweight='bold')
    
    # Add grid lines
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Customize spines
    for spine in ax.spines.values():
        spine.set_color('#2c3e50')
        spine.set_linewidth(1)
    
    plt.tight_layout()
    plt.savefig('docs/figures/performance_requirements.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='#f8f9fa',
                edgecolor='none',
                transparent=False)
    plt.close()

def main():
    """Generate all benchmark visualization graphs."""
    # Create figures directory if it doesn't exist
    import os
    os.makedirs('docs/figures', exist_ok=True)
    
    # Generate all plots
    plot_test_execution_summary()
    plot_model_specifications()
    plot_loading_performance()
    plot_inference_performance()
    plot_concurrent_performance()
    plot_performance_requirements()
    
    print("All benchmark graphs have been generated in docs/figures/")

if __name__ == "__main__":
    main() 