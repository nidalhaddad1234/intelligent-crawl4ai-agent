#!/usr/bin/env python3
"""
Authentication Strategies Package
Handles login, OAuth, and access control workflows
"""

from .auth_handler import AuthenticationStrategy
from .captcha_solver import CaptchaStrategy

__all__ = [
    "AuthenticationStrategy",
    "CaptchaStrategy"
]
