# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
OpenAI Proxy Client Utility

This module provides an interface for sending questions to a secure OpenAI proxy server.
Supports authentication, user_id, and model selection.
Falls back to mock mode if no proxy_url is set.
"""
import logging
from typing import Optional
import requests

class OpenAIProxyClient:
    """
    Handles communication with a secure OpenAI proxy server.
    """
    def __init__(self, proxy_url: Optional[str] = None, api_key: Optional[str] = None, default_model: str = "gpt-3.5-turbo"):
        """
        Initialize the client.
        Args:
            proxy_url (str, optional): The URL of the OpenAI proxy server. If None, uses mock mode.
            api_key (str, optional): The API key for authenticating with the proxy server.
            default_model (str): The default model to use (e.g., 'gpt-3.5-turbo').
        """
        self.proxy_url = proxy_url
        self.api_key = api_key
        self.default_model = default_model
        if not proxy_url:
            logging.info("OpenAIProxyClient initialized in mock mode (no proxy_url provided)")
        else:
            logging.info(f"OpenAIProxyClient will use proxy at: {proxy_url}")

    def ask(self, question: str, user_id: Optional[str] = None, model: Optional[str] = None) -> str:
        """
        Send a question to the OpenAI proxy and return the answer.
        Args:
            question (str): The question to send.
            user_id (str, optional): The user ID for tracking (optional).
            model (str, optional): The model to use (optional).
        Returns:
            str: The answer from OpenAI (or a mock answer).
        """
        if not self.proxy_url:
            # Mock response
            return (
                "[OpenAI Proxy Mock] This is a placeholder answer. "
                "(In production, this would be replaced by a real OpenAI response.)"
            )
        headers = {"X-API-KEY": self.api_key or "dev-secret"}
        payload = {
            "question": question,
            "user_id": user_id or "anonymous",
            "model": model or self.default_model
        }
        try:
            response = requests.post(self.proxy_url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            if "answer" in data and data["answer"]:
                return data["answer"]
            elif "error" in data:
                return f"[OpenAI Proxy Error] {data['error']}"
            else:
                return "[OpenAI Proxy Error] Unexpected response format."
        except Exception as e:
            return f"[OpenAI Proxy Error] {e}" 