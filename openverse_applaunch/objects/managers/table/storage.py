"""
Storage module for dynamic attribute management.

This module provides a StorageVars class that extends dict functionality
to support dynamic attribute access and modification.
"""

from typing import Any

from tools_openverse import setup_logger

# Configure logging
logger = setup_logger(__name__)


class StorageVars(dict):
    """
    Dictionary-based storage class with dynamic attribute access.

    This class extends the built-in dict to allow accessing and setting
    dictionary keys as if they were object attributes, providing a more
    convenient API for configuration and state management.

    Features:
        - Access dict keys as attributes (obj.key instead of obj['key'])
        - Set dict values as attributes (obj.key = value)
        - Delete dict items as attributes (del obj.key)
        - Maintains all standard dict functionality

    Example:
        storage = StorageVars()
        storage.database_url = "postgresql://localhost/db"
        print(storage.database_url)  # postgresql://localhost/db
        print(storage['database_url'])  # postgresql://localhost/db
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize StorageVars instance.

        Args:
            *args: Variable length argument list passed to dict.__init__
            **kwargs: Arbitrary keyword arguments passed to dict.__init__
        """
        super().__init__(*args, **kwargs)
        logger.debug(f"Initialized StorageVars with {len(self)} items")
        if self:
            logger.debug(f"Initial keys: {list(self.keys())}")

    def __getattr__(self, name: str) -> Any:
        """
        Get attribute value from dictionary.

        This method is called when an attribute is accessed that doesn't exist
        in the class itself. It looks up the name in the dictionary.

        Args:
            name: Attribute name to retrieve

        Returns:
            Value associated with the attribute name

        Raises:
            AttributeError: If the attribute name is not found in the dictionary
        """
        logger.debug(f"Getting attribute: {name}")

        try:
            self_value = self[name]
            logger.debug(f"Retrieved attribute '{name}': {type(self_value).__name__}")
            return self_value
        except KeyError:
            error_msg = f"StorageVars object has no attribute '{name}'"
            logger.warning(error_msg)
            raise AttributeError(error_msg)

    def __setattr__(self, name: str, some_value: Any) -> None:
        """
        Set attribute value in dictionary or class.

        If the attribute name exists in the class definition, it's set normally.
        Otherwise, it's stored in the dictionary for dynamic access.

        Args:
            name: Attribute name to set
            value: Value to assign to the attribute
        """
        if name in self.__class__.__dict__:
            # Set class-defined attributes normally
            logger.debug(f"Setting class attribute: {name}")
            super().__setattr__(name, some_value)
        else:
            # Store dynamic attributes in dict
            logger.debug(
                f"Setting dynamic attribute '{name}': {type(some_value).__name__}"
            )
            self[name] = some_value

    def __delattr__(self, name: str) -> None:
        """
        Delete attribute from dictionary.

        Args:
            name: Attribute name to delete

        Raises:
            AttributeError: If the attribute name is not found in the dictionary
        """
        logger.debug(f"Deleting attribute: {name}")

        try:
            self.pop(name)
            logger.info(f"Successfully deleted attribute: {name}")
        except KeyError:
            error_msg = f"StorageVars object has no attribute '{name}'"
            logger.warning(error_msg)
            raise AttributeError(error_msg)

    def __repr__(self) -> str:
        """
        Return string representation of StorageVars instance.

        Returns:
            String representation showing all key-value pairs
        """
        items_vars = ", ".join(
            f"{key_var}={value_var!r}"
            for key_var, value_var in self.items()
        )
        representation = f"StorageVars({items_vars})"
        logger.debug(f"Generated representation with {len(self)} items")
        return representation

    def clear_all(self) -> None:
        """
        Clear all stored variables and log the operation.
        """
        count = len(self)
        logger.info(f"Clearing {count} stored variables")
        self.clear()
        logger.info("All variables cleared successfully")

    def update_from_dict(self, data_dict: dict[str, Any]) -> None:
        """
        Update storage with values from a dictionary.

        Args:
            data: Dictionary containing key-value pairs to update
        """
        logger.info(f"Updating storage with {len(data_dict)} items")
        logger.debug(f"Update keys: {list(data_dict.keys())}")

        self.update(data_dict)
        logger.info("Storage update completed successfully")

    def get_all_vars(self) -> dict[str, Any]:
        """
        Get all stored variables as a regular dictionary.

        Returns:
            Dictionary containing all stored key-value pairs
        """
        logger.debug(f"Retrieving all {len(self)} stored variables")
        return dict(self)
