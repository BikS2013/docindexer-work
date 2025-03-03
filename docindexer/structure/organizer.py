"""
Document organizer module for creating hierarchical structure from markdown files.
Uses markdown-it-py for proper markdown parsing.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import markdown processing libraries
from markdown_it import MarkdownIt
from markdown_it.token import Token

from .node_factory import NodeFactory


class Organizer:
    """
    Class for organizing markdown content into a hierarchical structure.
    
    This organizer uses markdown-it-py to parse markdown documents and creates
    a JSON representation of their structure, including headers, paragraphs,
    lists, tables, images, and links.
    """
    
    def __init__(self):
        """Initialize the document organizer with markdown parser."""
        self.md_parser = MarkdownIt()
    
    def organize_document(self, content: str) -> Dict[str, Any]:
        """
        Organize markdown content into a hierarchical structure.
        
        Args:
            content: The markdown content to organize
            
        Returns:
            Dictionary representing the document structure
        """
        # Initialize the root document structure
        doc_structure = NodeFactory.create_document_node(content)
        
        # Parse the markdown content
        tokens = self.md_parser.parse(content)
        
        # Process tokens and build structure with proper nesting
        self._process_tokens(tokens, content, doc_structure)
        
        # Update sizes to include children
        self._update_sizes_with_children(doc_structure)
        
        # Add sequential IDs to elements
        self._add_sequential_ids(doc_structure)
        
        return doc_structure

    @staticmethod
    def get_end_indx(tokens: List[Token], i: int, open_tag: list[str], close_tag: list[str]) -> int:
        # Find the end of the blockquote
        end_idx = i + 1
        depth = 1
        while end_idx < len(tokens) and depth > 0:
            if tokens[end_idx].type in open_tag:
                depth += 1
            elif tokens[end_idx].type in close_tag:
                depth -= 1
            end_idx += 1
        return end_idx

    @staticmethod
    def handle_heading_open(token: Token, content_token: Token) -> Dict [str, Any]:
        if token.type == 'heading_open':
            # Extract heading level
            level = int(token.tag[1])  # e.g., 'h1' -> 1
            heading_text = content_token.content
            
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create header node using factory
            header_node = NodeFactory.create_header_node(
                level=level,
                content=heading_text,
                start_line=start_line,
                end_line=end_line
            )
            return header_node
        
    @staticmethod
    def handle_paragraph(token: Token, content_token: Token) -> Dict[str, Any]:
        if token.type == 'paragraph_open':
            para_text = content_token.content
            
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create paragraph node using factory
            para_node = NodeFactory.create_paragraph_node(
                content=para_text,
                start_line=start_line,
                end_line=end_line
            )
            return para_node
        
    @staticmethod
    def handle_list_open(token: Token, tokens:List[Token], token_idx: int, end_idx: int ) -> Dict[str, Any]:
        if token.type == 'bullet_list_open' or token.type == 'ordered_list_open':
            # Determine list type
            list_type = "unordered" if token.type == 'bullet_list_open' else "ordered"
            
            # Extract list content tokens
            list_tokens = tokens[token_idx+1:end_idx-1]
            
            # Process list items
            list_items = Organizer._process_list_items(list_tokens, list_type)
            
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create list node using factory
            list_node = NodeFactory.create_list_node(
                list_type=list_type,
                items=list_items,
                start_line=start_line,
                end_line=end_line
            )
            return list_node

    @staticmethod
    def handle_table(token: Token, tokens: List[Token], token_idx: int, end_idx: int) -> Dict[str, Any]:
        if token.type == 'table_open':

            
            # Extract table content tokens
            table_tokens = tokens[token_idx+1:end_idx]
            
            # Process table rows and cells
            rows = Organizer._process_table(table_tokens)
            
            # Create table content string
            table_content = Organizer._format_table_content(rows)
            
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create table node using factory
            table_node = NodeFactory.create_table_node(
                content=table_content,
                rows=rows,
                start_line=start_line,
                end_line=end_line
            )
            return table_node

    @staticmethod
    def handle_code_block(token: Token) -> Dict[str, Any]:
        if token.type == 'code_block':
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create code block node using factory
            code_node = NodeFactory.create_code_node(
                content=token.content,
                language=token.info if token.info else "",
                start_line=start_line,
                end_line=end_line
            )
            return code_node

    @staticmethod
    def handle_fence(token: Token) -> Dict[str, Any]:
        if token.type == 'fence':
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create fenced code block node using factory
            code_node = NodeFactory.create_code_node(
                content=token.content,
                language=token.info if token.info else "",
                start_line=start_line,
                end_line=end_line
            )
            return code_node

    @staticmethod
    def handle_blockquote(token: Token) -> Dict[str, Any]:
        if token.type == 'blockquote_open':
            # Get line numbers if available
            start_line = token.map[0] if hasattr(token, 'map') and token.map else None
            end_line = token.map[1] if hasattr(token, 'map') and token.map else None
            
            # Create blockquote node using factory
            quote_node = NodeFactory.create_blockquote_node(
                start_line=start_line,
                end_line=end_line
            )
            return quote_node
                    
    def _process_tokens(self, tokens: List[Token], content: str, parent: Dict[str, Any]) -> None:
        """
        Process markdown tokens and build document structure.
        
        Args:
            tokens: List of markdown tokens
            content: Original markdown content
            parent: Parent element to add children to
        """
        if "elements" not in parent:
            parent["elements"] = []
        
        # Create a stack to track the current parent at each nesting level
        # Start with the provided parent
        parent_stack = [parent]
        
        # Track header levels for proper nesting
        header_level_stack = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            current_parent = parent_stack[-1]  # Current parent is the top of the stack
            
            # Handle different token types
            if token.type == 'heading_open':
                content_token = tokens[i+1]
                header_node = self.handle_heading_open(token, content_token)
                
                level = int(header_node["level"])
                
                # Pop header levels that are same or higher
                while header_level_stack and header_level_stack[-1] >= level:
                    header_level_stack.pop()
                    parent_stack.pop()
                
                # The current parent is now the appropriate level for this header
                current_parent = parent_stack[-1]
                
                # Add this header to the current parent
                current_parent["elements"].append(header_node)
                
                # Add this header to the stacks
                parent_stack.append(header_node)
                header_level_stack.append(level)
                
                # Skip the content and closing tokens
                i += 3
            
            elif token.type == 'paragraph_open':
                # Get paragraph content (in the next token)
                content_token = tokens[i+1]
                para_node = self.handle_paragraph(token, content_token)
                
                # Look for inline elements in the paragraph
                self._process_inline_elements(content_token, para_node)
                
                # Add paragraph to current parent
                current_parent["elements"].append(para_node)
                
                # Skip the content and closing tokens
                i += 3
            
            elif token.type == 'bullet_list_open' or token.type == 'ordered_list_open':

                end_idx = self.get_end_indx(tokens, i, 
                                            ['bullet_list_open','ordered_list_open'], 
                                            ['bullet_list_close', 'ordered_list_close'])

                list_node = self.handle_list_open(token, tokens, i, end_idx )
                
                # Add list to current parent
                current_parent["elements"].append(list_node)
                
                # Skip to after the list close token
                i = end_idx
            
            elif token.type == 'table_open':
                end_idx = self.get_end_indx(tokens, i, ['table_open'], ['table_close'])
                table_node = self.handle_table(token, tokens, i, end_idx)
                # Add table to current parent
                current_parent["elements"].append(table_node)
                
                # Skip to after the table close token
                i = end_idx + 1
            
            elif token.type == 'code_block':
                code_node = self.handle_code_block(token)
                
                # Add code block to current parent
                current_parent["elements"].append(code_node)
                
                # Move to next token
                i += 1
            
            elif token.type == 'fence':
                code_node = self.handle_fence(token)

                # Add code block to current parent
                current_parent["elements"].append(code_node)
                
                # Move to next token
                i += 1
            
            elif token.type == 'hr':
                # Create horizontal rule node using factory
                hr_node = NodeFactory.create_hr_node()
                
                # Add horizontal rule to current parent
                current_parent["elements"].append(hr_node)
                
                # Move to next token
                i += 1
            
            elif token.type == 'blockquote_open':
                # Find the end of the blockquote
                end_idx = self.get_end_indx(tokens, i, ['blockquote_open'], ['blockquote_close'])

                quote_node = self.handle_blockquote(token, tokens, i, end_idx)
                quote_tokens = tokens[i+1:end_idx-1]
                
                # Add blockquote to current parent and process its content
                current_parent["elements"].append(quote_node)
                
                # Process blockquote content with the blockquote as the parent
                self._process_tokens(quote_tokens, content, quote_node)
                
                # Update blockquote content and size
                quote_content = " ".join([element.get("content", "") for element in quote_node["elements"]])
                quote_node["content"] = quote_content
                quote_node["content_size"] = len(quote_content)
                
                # Skip to after the blockquote close token
                i = end_idx
            
            else:
                # Skip other token types
                i += 1
    
    @staticmethod
    def _process_inline_elements(token: Token, parent: Dict[str, Any]) -> None:
        """
        Process inline elements within a token.
        
        Args:
            token: Token containing inline elements
            parent: Parent element to add children to
        """
        if not hasattr(token, 'children') or not token.children:
            return
        
        for child in token.children:
            if child.type == 'image':
                # Extract image attributes
                alt = child.content
                src = child.attrs['src'] if 'src' in child.attrs else ''
                
                # Create image node using factory
                img_node = NodeFactory.create_image_node(
                    alt=alt,
                    src=src
                )
                
                # Add image to parent
                parent["elements"].append(img_node)
            
            elif child.type == 'link':
                # Extract link attributes
                text = child.content
                url = child.attrs['href'] if 'href' in child.attrs else ''
                
                # Create link node using factory
                link_node = NodeFactory.create_link_node(
                    text=text,
                    url=url
                )
                
                # Add link to parent
                parent["elements"].append(link_node)
            
            # Process other inline elements if needed
            # Add additional cases for bold, italic, code, etc.
    
    @staticmethod
    def _process_list_items(tokens: List[Token], list_type: str) -> List[Dict[str, Any]]:
        """
        Process list item tokens.
        
        Args:
            tokens: List item tokens
            list_type: Type of list (ordered/unordered)
            
        Returns:
            List of dictionaries representing list items
        """
        items = []
        i = 0
        
        while i < len(tokens):
            if tokens[i].type == 'list_item_open':
                # Find the content of this list item
                content_idx = i + 1
                while content_idx < len(tokens) and tokens[content_idx].type != 'paragraph_open':
                    content_idx += 1
                
                if content_idx < len(tokens) and tokens[content_idx].type == 'paragraph_open':
                    # Get the content in the next token
                    content_token = tokens[content_idx + 1]
                    item_text = content_token.content
                    
                    # Create list item node using factory
                    item_node = NodeFactory.create_list_item_node(
                        content=item_text,
                        list_type=list_type
                    )
                    
                    # Process inline elements in the list item
                    if hasattr(content_token, 'children') and content_token.children:
                        item_node["elements"] = []
                        Organizer._process_inline_elements(content_token, item_node)
                    
                    # Add the item to the list
                    items.append(item_node)
                
                # Find the end of this list item
                end_idx = i + 1
                while end_idx < len(tokens) and tokens[end_idx].type != 'list_item_close':
                    end_idx += 1
                
                # Move to the next list item
                i = end_idx + 1
            else:
                i += 1
        
        return items
    
    @staticmethod
    def _process_table(tokens: List[Token]) -> List[List[str]]:
        """
        Process table tokens.
        
        Args:
            tokens: Table tokens
            
        Returns:
            List of rows, each containing cells as strings
        """
        rows = []
        current_row = []
        
        for token in tokens:
            if token.type == 'tr_open':
                current_row = []
            elif token.type == 'tr_close':
                rows.append(current_row)
            elif token.type == 'th_open' or token.type == 'td_open':
                # Next token should be inline with the cell content
                next_token_idx = tokens.index(token) + 1
                if next_token_idx < len(tokens) and tokens[next_token_idx].type == 'inline':
                    current_row.append(tokens[next_token_idx].content)
                else:
                    current_row.append("")
        
        return rows
    
    @staticmethod   
    def _format_table_content(rows: List[List[str]]) -> str:
        """
        Format table content into a markdown string.
        
        Args:
            rows: Table rows with cells
            
        Returns:
            Formatted table string
        """
        if not rows:
            return ""
        
        # Create header row
        result = "| " + " | ".join(rows[0]) + " |\n"
        
        # Create separator row
        result += "| " + " | ".join(["---"] * len(rows[0])) + " |\n"
        
        # Create data rows
        for row in rows[1:]:
            result += "| " + " | ".join(row) + " |\n"
        
        return result
    
    @staticmethod
    def _update_sizes_with_children(element: Dict[str, Any]) -> int:
        """
        Recursively update element sizes to include the size of their children.
        
        Args:
            element: The element to update
            
        Returns:
            The total size of the element including its children
        """
        # Store original content size
        content_size = element.get("content_size", element.get("size", 0))
        
        # Calculate total size including children
        total_size = content_size
        
        # Process children if they exist
        if "elements" in element and element["elements"]:
            for child in element["elements"]:
                child_size = Organizer._update_sizes_with_children(child)
                total_size += child_size
                
        # Process list items if this is a list
        if "items" in element and element["items"]:
            for item in element["items"]:
                if "elements" in item and item["elements"]:
                    # Process nested elements in list items
                    item_size = Organizer._update_sizes_with_children(item)
                else:
                    item_size = item.get("content_size", item.get("size", 0))
                    # Update item size
                    item["size"] = item_size
                
                total_size += item_size
        
        # Process table rows if this is a table
        if "rows" in element and element["rows"]:
            # Rows are already counted in content_size
            pass
        
        # Update the element's size to include children
        element["size"] = total_size
        
        return total_size
    
    @staticmethod
    def _add_sequential_ids(structure: Dict[str, Any], counter: List[int] = None) -> Dict[str, Any]:
        """
        Recursively add sequential IDs to each element in the document structure.
        
        Args:
            structure: The document structure to process
            counter: List containing a single integer to track the ID counter across recursive calls
            
        Returns:
            Document structure with added sequential IDs
        """
        # Initialize counter if not provided
        if counter is None:
            counter = [1]
            
        if isinstance(structure, dict):
            # Add ID to elements with type, ensuring id comes first
            if "type" in structure:
                # Create new dict with id first, then merge with existing structure
                new_structure = {"id": counter[0]}
                new_structure.update(structure)
                structure.clear()
                structure.update(new_structure)
                counter[0] += 1
                
            # Process nested elements
            if "elements" in structure and structure["elements"]:
                for element in structure["elements"]:
                    Organizer._add_sequential_ids(element, counter)
                    
            # Process list items
            if "items" in structure and structure["items"]:
                for item in structure["items"]:
                    Organizer._add_sequential_ids(item, counter)
                    
        return structure
        
    @staticmethod
    def _filter_properties(structure: Dict[str, Any], properties_to_omit: List[str]) -> Dict[str, Any]:
        """
        Recursively remove specified properties from the document structure.
        
        Args:
            structure: The document structure to filter
            properties_to_omit: List of property names to omit
            
        Returns:
            Filtered document structure
        """
        # Make a copy to avoid modifying the original
        if isinstance(structure, dict):
            result = {}
            # Copy all properties except those to be omitted
            for key, value in structure.items():
                if key not in properties_to_omit:
                    if isinstance(value, dict) or isinstance(value, list):
                        result[key] = Organizer._filter_properties(value, properties_to_omit)
                    else:
                        result[key] = value
            return result
        elif isinstance(structure, list):
            # Process each item in the list
            return [Organizer._filter_properties(item, properties_to_omit) for item in structure]
        else:
            # Return primitive values as is
            return structure

    @staticmethod
    def _filter_empty_elements(structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively remove the empty elements property from the document structure.
        
        Args:
            structure: The document structure to filter
            
        Returns:
            Filtered document structure
        """
        # Make a copy to avoid modifying the original
        if isinstance(structure, dict):
            result = {}
            # Copy all properties except those to be omitted
            for key, value in structure.items():
                if key != "elements" or value != []:
                    if isinstance(value, dict) or isinstance(value, list):
                        result[key] = Organizer._filter_empty_elements(value)
                    else:
                        result[key] = value
            return result
        elif isinstance(structure, list):
            # Process each item in the list
            return [Organizer._filter_empty_elements(item) for item in structure]
        else:
            # Return primitive values as is
            return structure

    @staticmethod   
    def save_organization_to_json(document_structure: Dict[str, Any], output_path: Path, 
                                 omit_properties: Optional[List[str]] = None) -> None:
        """
        Save the document organization to a JSON file.
        
        Args:
            document_structure: The document structure to save
            output_path: Path where to save the JSON file
            omit_properties: List of property names to omit from the JSON output
        """
        filtered_structure = Organizer._filter_empty_elements(document_structure)
        if omit_properties:
            # Create a deep copy to avoid modifying the original structure
            filtered_structure = Organizer._filter_properties(
                filtered_structure, omit_properties
            )

            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_structure, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_structure_from_markdown_content(markdown_content: str) -> Dict[str, Any]:
        """
        Load markdown content and organize it into a structure.
        
        Args:
            markdown_content: The markdown content to organize
            
        Returns:
            Dictionary representing the document structure
        """
        organizer = Organizer()
        return organizer.organize_document(markdown_content)
    
    @staticmethod
    def load_structure_from_markdown_file(markdown_file: Path) -> Dict[str, Any]:
        """
        Load markdown content from a file and organize it into a structure.
        
        Args:
            markdown_file: Path to the markdown file
            
        Returns:
            Dictionary representing the document structure
        """
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        organizer = Organizer()
        return organizer.organize_document(content)