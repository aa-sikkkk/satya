# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Performance Utilities Module

Provides tools for timing, memory/CPU usage tracking, and logging performance metrics.
"""

import time
import functools
import logging
import os
import psutil
from typing import Callable, Any

# Configures performance logger
PERF_LOG_FILE = os.path.join(os.path.dirname(__file__), 'performance.log')
logging.basicConfig(
    filename=PERF_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def timeit(func: Callable) -> Callable:
    """
    Decorator to time a function and log its execution time.
    Args:
        func (Callable): The function to time
    Returns:
        Callable: Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        logging.info(f"Function {func.__name__} executed in {elapsed:.4f} seconds.")
        return result
    return wrapper


def log_resource_usage(note: str = "") -> None:
    """
    Log current memory and CPU usage.
    Args:
        note (str): Optional note to include in the log
    """
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)  # MB
    cpu = process.cpu_percent(interval=0.1)
    logging.info(f"{note} Memory usage: {mem:.2f} MB, CPU usage: {cpu:.2f}%.")


def log_performance_metric(message: str) -> None:
    """
    Log a custom performance metric message.
    Args:
        message (str): The message to log
    """
    logging.info(message) 