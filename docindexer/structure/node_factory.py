"""
Factory class for creating different types of markdown document nodes.
"""
from typing import Dict, Any, List, Optional


class NodeFactory:
    """Factory class for creating document node dictionaries."""

    @staticmethod
    def create_node( type: str, content: str, content_size: int, size: int, 
                    visualize: Optional[bool]=True, vectorize: Optional[bool]=True,
                    start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        return {
            "type": type,
            "content": content,
            "content_size": content_size,
            "size": size,
            "elements": [],
            "vectorize": vectorize
        }        
    
    @staticmethod
    def create_document_node(content: str) -> Dict[str, Any]:
        """Create a document root node."""
        return NodeFactory.create_node("document", content, len(content), len(content))
    
    @staticmethod
    def create_header_node(level: int, content: str, start_line: Optional[int] = None,
                          end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a header node."""
        node = NodeFactory.create_node(f"h{level}", content, len(content), len(content), start_line=start_line, end_line=end_line)
        node["level"] = level
        return node
    
    @staticmethod
    def create_paragraph_node(content: str, start_line: Optional[int] = None,
                            end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a paragraph node."""
        node = NodeFactory.create_node("paragraph", content, len(content), len(content), start_line=start_line, end_line=end_line)
        return node
    
    @staticmethod
    def create_list_node(list_type: str, items: List[Dict[str, Any]], 
                        start_line: Optional[int] = None,
                        end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a list node."""
        list_content = " ".join([item.get("content", "") for item in items])
        list_content_size = len(list_content)
        node = NodeFactory.create_node("list", list_content, list_content_size, list_content_size, start_line=start_line, end_line=end_line)
        node["list_type"] = list_type
        node["items"] = items
        return node
    
    @staticmethod
    def create_list_item_node(content: str, list_type: str) -> Dict[str, Any]:
        """Create a list item node."""
        node = NodeFactory.create_node("list_item", content, len(content), len(content))
        node["list_type"] = list_type
        return node
    
    @staticmethod
    def create_table_node(content: str, rows: List[List[str]], 
                         start_line: Optional[int] = None,
                         end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a table node."""
        node = NodeFactory.create_node("table", content, len(content), len(content), start_line=start_line, end_line=end_line)
        node["rows"] = rows

        return node
    
    @staticmethod
    def create_code_node(content: str, language: str = "", 
                        start_line: Optional[int] = None,
                        end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a code block node."""
        node = NodeFactory.create_node("code_block", content, len(content), len(content), start_line=start_line, end_line=end_line)
        node["language"] = language

        return node
    
    @staticmethod
    def create_hr_node() -> Dict[str, Any]:
        """Create a horizontal rule node."""
        node = NodeFactory.create_node("hr", "---", 3, 3, vectorize=False)
        return node
    
    @staticmethod
    def create_blockquote_node(start_line: Optional[int] = None,
                              end_line: Optional[int] = None) -> Dict[str, Any]:
        """Create a blockquote node."""
        node = NodeFactory.create_node("blockquote", "", 0, 0, start_line=start_line, end_line=end_line)
        return node
    
    @staticmethod
    def create_image_node(alt: str, src: str) -> Dict[str, Any]:
        """Create an image node."""
        content = f"![{alt}]({src})"
        node = NodeFactory.create_node("image", content, len(content), len(content), vectorize=False)
        node["alt"] = alt
        node["src"] = src
        return node
    
    @staticmethod
    def create_link_node(text: str, url: str) -> Dict[str, Any]:
        """Create a link node."""
        content = f"[{text}]({url})"
        node = NodeFactory.create_node("link", content, len(content), len(content), vectorize=False)
        node["text"] = text
        node["url"] = url
        return node
