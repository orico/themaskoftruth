"""Poki SDK integration for HTML5 builds.

This module provides a wrapper around the Poki SDK that works in both
regular Python/Pygame mode and HTML5/WebAssembly mode.
"""

import logging
import sys
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PokiSDK:
    """Poki SDK wrapper that works in both Python and HTML5 environments."""

    def __init__(self):
        self._is_html5 = self._check_html5_environment()
        self._poki_sdk = None
        self._initialized = False

        if self._is_html5:
            self._init_html5_sdk()
        else:
            logger.info("Running in Python mode - Poki SDK events will be logged only")

    def _check_html5_environment(self) -> bool:
        """Check if we're running in HTML5/WebAssembly environment."""
        try:
            # Check for common indicators of HTML5 environment
            import platform

            is_emscripten = "emscripten" in platform.system().lower() or hasattr(
                sys, "_emscripten_info"
            )

            # Also check for js module availability (pygame-web specific)
            if is_emscripten:
                try:
                    import js

                    # Additional check: see if we can access window
                    if hasattr(js, "window"):
                        return True
                except ImportError:
                    pass

            logger.info(f"HTML5 environment check: emscripten={is_emscripten}")
            return is_emscripten
        except Exception as e:
            logger.info(f"HTML5 environment check failed: {e}")
            return False

    def _init_html5_sdk(self):
        """Initialize Poki SDK for HTML5 environment."""
        try:
            # Import the JavaScript Poki SDK
            import js

            # Check if PokiSDK is available on window object
            if hasattr(js, "window") and hasattr(js.window, "PokiSDK"):
                self._poki_sdk = js.window.PokiSDK
                logger.info("Poki SDK HTML5 module loaded successfully")
            else:
                # Try direct access
                try:
                    import js as js_module

                    if hasattr(js_module, "PokiSDK"):
                        self._poki_sdk = js_module.PokiSDK
                        logger.info("Poki SDK loaded via direct js import")
                    else:
                        logger.warning("PokiSDK not found in js module")
                        self._is_html5 = False
                except:
                    logger.warning("PokiSDK not found on window object or js module")
                    self._is_html5 = False
        except ImportError as e:
            logger.warning(f"Failed to import js module: {e}")
            self._is_html5 = False
        except Exception as e:
            logger.warning(f"Failed to initialize Poki SDK: {e}")
            self._is_html5 = False

    def init(self) -> bool:
        """Initialize the Poki SDK.

        Returns:
            bool: True if initialization was successful
        """
        if not self._is_html5:
            logger.info("PokiSDK.init() called (Python mode - no-op)")
            self._initialized = True
            return True

        if self._poki_sdk:
            try:
                # Initialize with debug mode in development
                # Note: Poki SDK init returns a promise, but we'll assume it's available immediately
                if hasattr(self._poki_sdk, "init"):
                    self._poki_sdk.init()
                if hasattr(self._poki_sdk, "setDebug"):
                    self._poki_sdk.setDebug(True)
                self._initialized = True
                logger.info("Poki SDK initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Poki SDK: {e}")
                return False
        else:
            logger.warning("Poki SDK not available")
            return False

    def gameLoadingFinished(self):
        """Signal that game loading has finished."""
        if not self._initialized:
            logger.warning("Poki SDK not initialized - skipping gameLoadingFinished")
            return

        if not self._is_html5:
            logger.info("PokiSDK.gameLoadingFinished() called (Python mode)")
            return

        if self._poki_sdk and hasattr(self._poki_sdk, "gameLoadingFinished"):
            try:
                self._poki_sdk.gameLoadingFinished()
                logger.info("Poki SDK: gameLoadingFinished")
            except Exception as e:
                logger.error(f"Failed to call gameLoadingFinished: {e}")
        else:
            logger.warning("gameLoadingFinished method not available")

    def gameplayStart(self):
        """Signal that gameplay has started."""
        if not self._initialized:
            logger.warning("Poki SDK not initialized - skipping gameplayStart")
            return

        if not self._is_html5:
            logger.info("PokiSDK.gameplayStart() called (Python mode)")
            return

        if self._poki_sdk and hasattr(self._poki_sdk, "gameplayStart"):
            try:
                self._poki_sdk.gameplayStart()
                logger.info("Poki SDK: gameplayStart")
            except Exception as e:
                logger.error(f"Failed to call gameplayStart: {e}")
        else:
            logger.warning("gameplayStart method not available")

    def gameplayStop(self):
        """Signal that gameplay has stopped."""
        if not self._initialized:
            logger.warning("Poki SDK not initialized - skipping gameplayStop")
            return

        if not self._is_html5:
            logger.info("PokiSDK.gameplayStop() called (Python mode)")
            return

        if self._poki_sdk and hasattr(self._poki_sdk, "gameplayStop"):
            try:
                self._poki_sdk.gameplayStop()
                logger.info("Poki SDK: gameplayStop")
            except Exception as e:
                logger.error(f"Failed to call gameplayStop: {e}")
        else:
            logger.warning("gameplayStop method not available")

    def commercialBreak(self, callback: Optional[Callable] = None) -> bool:
        """Show a commercial break ad.

        Args:
            callback: Function to call when ad completes

        Returns:
            bool: True if ad was shown or would be shown
        """
        if not self._initialized:
            logger.warning("Poki SDK not initialized - skipping commercialBreak")
            if callback:
                callback()
            return False

        if not self._is_html5:
            logger.info("PokiSDK.commercialBreak() called (Python mode)")
            if callback:
                callback()
            return True

        if self._poki_sdk and hasattr(self._poki_sdk, "commercialBreak"):
            try:
                if callback:
                    # Create a JavaScript function that can be called from JS
                    import js

                    js_callback = js.Func(callback)
                    self._poki_sdk.commercialBreak(js_callback)
                else:
                    self._poki_sdk.commercialBreak()
                logger.info("Poki SDK: commercialBreak started")
                return True
            except Exception as e:
                logger.error(f"Failed to show commercial break: {e}")
                if callback:
                    callback()
                return False
        else:
            logger.warning("Commercial break not available")
            if callback:
                callback()
            return False

    def rewardedBreak(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Show a rewarded video ad.

        Args:
            callback: Function to call when ad completes, receives with_reward parameter

        Returns:
            bool: True if ad was shown or would be shown
        """
        if not self._initialized:
            logger.warning("Poki SDK not initialized - skipping rewardedBreak")
            if callback:
                callback(False)  # Assume no reward in fallback
            return False

        if not self._is_html5:
            logger.info("PokiSDK.rewardedBreak() called (Python mode)")
            if callback:
                callback(True)  # Assume reward granted in Python mode
            return True

        if self._poki_sdk and hasattr(self._poki_sdk, "rewardedBreak"):
            try:

                def ad_callback(with_reward: bool):
                    logger.info(
                        f"Poki SDK: rewardedBreak completed (reward: {with_reward})"
                    )
                    if callback:
                        callback(with_reward)

                self._poki_sdk.rewardedBreak(ad_callback)
                return True
            except Exception as e:
                logger.error(f"Failed to show rewarded break: {e}")
                if callback:
                    callback(False)
                return False
        else:
            logger.warning("Rewarded break not available")
            if callback:
                callback(False)
            return False

    def isAdsBlocked(self) -> bool:
        """Check if ads are blocked by the user.

        Returns:
            bool: True if ads are blocked
        """
        if not self._is_html5:
            return False

        if self._poki_sdk and hasattr(self._poki_sdk, "adsBlocked"):
            try:
                return bool(self._poki_sdk.adsBlocked())
            except Exception as e:
                logger.error(f"Failed to check ad block status: {e}")
                return False
        return False


# Global instance
_poki_sdk_instance = None


def get_poki_sdk() -> PokiSDK:
    """Get the global Poki SDK instance."""
    global _poki_sdk_instance
    if _poki_sdk_instance is None:
        _poki_sdk_instance = PokiSDK()
    return _poki_sdk_instance
