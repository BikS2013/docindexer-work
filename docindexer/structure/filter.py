"""
Module for filtering document structure properties.
"""
from copy import deepcopy
from typing import Dict, Any, List, Set


class Filter:
    """
    Class for filtering properties from document structures.
    Creates a new copy of a document structure with specified properties removed.
    """
    
    def filter_document(self, document_structure: Dict[str, Any], 
                       exclude_properties: List[str]) -> Dict[str, Any]:
        """
        Create a filtered copy of the document structure.
        
        Args:
            document_structure: Original document structure to filter
            exclude_properties: List of property names to exclude from the structure
            
        Returns:
            New document structure with specified properties removed
        """
        # Create a deep copy to avoid modifying the original
        filtered_doc = deepcopy(document_structure)
        
        # Convert list to set for O(1) lookups
        properties_to_exclude = set(exclude_properties)
        
        # Filter the document structure recursively
        self._filter_node(filtered_doc, properties_to_exclude)
        
        return filtered_doc
    
    def _filter_node(self, node: Dict[str, Any], exclude_properties: Set[str]) -> None:
        """
        Recursively filter properties from a node and its children.
        
        Args:
            node: Node to filter
            exclude_properties: Set of property names to exclude
        """
        # Remove excluded properties from the current node
        for prop in exclude_properties:
            node.pop(prop, None)
        
        # Process any child elements
        if "elements" in node:
            for child in node["elements"]:
                self._filter_node(child, exclude_properties)
        
        # Process list items if present
        if "items" in node:
            for item in node["items"]:
                self._filter_node(item, exclude_properties)
        
        # Note: No need to process table rows as they are just strings