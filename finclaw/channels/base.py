"""Base channel interface for chat platforms."""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from finclaw.bus.events import InboundMessage, OutboundMessage
from finclaw.bus.queue import MessageBus


class BaseChannel(ABC):
    """
    Abstract base class for chat channel implementations.
    
    Each channel (Telegram, Discord, etc.) should implement this interface
    to integrate with the finclaw message bus.
    """
    
    name: str = "base"
    
    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize the channel.
        
        Args:
            config: Channel-specific configuration.
            bus: The message bus for communication.
        """
        self.config = config
        self.bus = bus
        self._running = False
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the channel and begin listening for messages.
        
        This should be a long-running async task that:
        1. Connects to the chat platform
        2. Listens for incoming messages
        3. Forwards messages to the bus via _handle_message()
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources."""
        pass
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through this channel.
        
        Args:
            msg: The message to send.
        """
        pass
    
    _open_access_warned: bool = False
    _empty_allowlist_warned: bool = False

    def is_allowed(self, sender_id: str) -> bool:
        """
        Check if a sender is allowed to use this bot.

        Security — NemoClaw #1416 fail-closed model:
        - policy="allowlist" (default): only senders in allow_from are
          permitted.  If allow_from is empty, ALL messages are DENIED and
          an error is logged telling the operator to populate the list or
          explicitly set policy to "open".
        - policy="open": any sender is permitted (with a one-time warning).
        
        Args:
            sender_id: The sender's identifier.
        
        Returns:
            True if allowed, False otherwise.
        """
        policy = getattr(self.config, "policy", "allowlist")
        allow_list = getattr(self.config, "allow_from", [])
        
        # --- explicit open access ---
        if policy == "open":
            if not BaseChannel._open_access_warned:
                BaseChannel._open_access_warned = True
                logger.warning(
                    "⚠️  Channel policy is 'open' — ALL senders are "
                    "permitted.  Set policy to 'allowlist' and populate "
                    "allowFrom for production use."
                )
            return True
        
        # --- allowlist mode (default / fail-closed) ---
        if not allow_list:
            if not BaseChannel._empty_allowlist_warned:
                BaseChannel._empty_allowlist_warned = True
                logger.error(
                    f"🚫 Channel '{self.name}' policy is 'allowlist' but allow_from is empty — "
                    "ALL messages are BLOCKED.  Either add user/chat IDs to "
                    "allowFrom, or set policy to 'open' to allow everyone."
                )
            return False
        
        sender_str = str(sender_id)
        if sender_str in allow_list:
            return True

        # Support composite IDs (e.g. Telegram "12345|username").
        # Only match the *first* part (numeric platform ID) to prevent an
        # attacker from choosing a username that collides with another user's
        # numeric ID in the allowlist.  (NemoClaw #1416 pattern)
        if "|" in sender_str:
            primary_id = sender_str.split("|", 1)[0]
            if primary_id and primary_id in allow_list:
                return True
        return False
    
    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Handle an incoming message from the chat platform.
        
        This method checks permissions and forwards to the bus.
        
        Args:
            sender_id: The sender's identifier.
            chat_id: The chat/channel identifier.
            content: Message text content.
            media: Optional list of media URLs.
            metadata: Optional channel-specific metadata.
        """
        if not self.is_allowed(sender_id):
            logger.warning(
                f"Access denied for sender {sender_id} on channel {self.name}. "
                f"Add them to allowFrom list in config to grant access."
            )
            return
        
        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {}
        )
        
        await self.bus.publish_inbound(msg)
    
    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
