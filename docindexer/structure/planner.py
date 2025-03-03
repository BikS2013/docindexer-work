import json
import re
from typing import Dict, List, Tuple, Union, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentChunker:
    def __init__(self, min_chunk_size: int = 500, max_chunk_size: int = 2000, 
                 chunk_overlap: int = 50, size_tolerance: float = 0.1):
        """
        Initialize the document chunker.
        
        Args:
            min_chunk_size: Minimum size for a chunk in characters
            max_chunk_size: Maximum size for a chunk in characters
            chunk_overlap: Overlap between chunks in characters
            size_tolerance: Tolerance for max size (e.g., 0.1 for 10% over max_chunk_size)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.size_tolerance = size_tolerance
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len
        )
    
    def load_document(self, json_file_path: str) -> Dict:
        """Load document from JSON file."""
        with open(json_file_path, 'r') as f:
            return json.load(f)
    
    def process_element(self, element: Dict) -> Dict:
        """
        Process an element and determine if it needs chunking.
        
        Returns a plan entry for this element with chunking details.
        """
        content = element.get('content', '')
        content_size = element.get('content_size', 0)
        element_id = element.get('id')
        
        plan_entry = {
            'id': element_id,
            'original_size': content_size,
            'action': 'keep_as_is',  # Default action
            'chunks': []
        }
        
        # Check if element exceeds max size with tolerance
        if content_size > self.max_chunk_size * (1 + self.size_tolerance):
            chunks = self.text_splitter.split_text(content)
            plan_entry['action'] = 'chunk'
            plan_entry['chunks'] = [{
                'index': i,
                'size': len(chunk),
                'preview': chunk[:50] + '...' if len(chunk) > 50 else chunk
            } for i, chunk in enumerate(chunks)]
        
        # Process child elements recursively
        child_plans = []
        for child in element.get('elements', []):
            child_plan = self.process_element(child)
            child_plans.append(child_plan)
        
        if child_plans:
            plan_entry['child_elements'] = child_plans
            
        return plan_entry
    
    def create_chunking_plan(self, document: Dict) -> Dict:
        """
        Create a chunking plan for the entire document.
        """
        plan = {
            'document_id': document.get('id'),
            'total_size': document.get('content_size', 0),
            'min_chunk_size': self.min_chunk_size,
            'max_chunk_size': self.max_chunk_size,
            'elements': []
        }
        
        # Process all elements in the document
        for element in document.get('elements', []):
            element_plan = self.process_element(element)
            plan['elements'].append(element_plan)
        
        # Second pass to identify merge candidates
        self._identify_merge_candidates(plan['elements'])
        
        return plan
    
    def _identify_merge_candidates(self, elements: List[Dict], parent_path: str = '') -> None:
        """
        Identify elements that should be merged to meet minimum size.
        Updates the plan entries in place.
        """
        # Gather small elements that might need merging
        merge_candidates = []
        current_size = 0
        current_group = []
        
        for i, element in enumerate(elements):
            # Skip elements that are already being chunked
            if element['action'] == 'chunk':
                # Finalize any pending merge group
                if current_group and current_size >= self.min_chunk_size:
                    for e in current_group:
                        e['action'] = 'merge'
                        e['merge_group'] = merge_candidates[-1]['group_id']
                current_group = []
                current_size = 0
                continue
                
            # If this is a small element, consider for merging
            if element['original_size'] < self.min_chunk_size:
                if not current_group:  # Start a new group
                    merge_group = {
                        'group_id': f"merge_{parent_path}_{len(merge_candidates)}",
                        'elements': [],
                        'total_size': 0
                    }
                    merge_candidates.append(merge_group)
                
                current_group.append(element)
                current_size += element['original_size']
                merge_candidates[-1]['elements'].append(element['id'])
                merge_candidates[-1]['total_size'] += element['original_size']
                
                element['merge_candidate'] = True
                
                # If we have enough to meet minimum size, mark them for merging
                if current_size >= self.min_chunk_size:
                    if current_size <= self.max_chunk_size * (1 + self.size_tolerance):
                        for e in current_group:
                            e['action'] = 'merge'
                            e['merge_group'] = merge_candidates[-1]['group_id']
                    else:
                        # The merged group would be too big, leave them as separate chunks
                        for e in current_group:
                            e['action'] = 'keep_as_is'
                            e.pop('merge_candidate', None)
                    
                    # Reset for next group
                    current_group = []
                    current_size = 0
            else:
                # This element is big enough on its own, finalize any pending merge
                if current_group and current_size >= self.min_chunk_size:
                    for e in current_group:
                        e['action'] = 'merge'
                        e['merge_group'] = merge_candidates[-1]['group_id']
                elif current_group:
                    # Not enough for a good merge, keep them separate
                    for e in current_group:
                        e['action'] = 'keep_as_is'
                        e.pop('merge_candidate', None)
                
                current_group = []
                current_size = 0
            
            # Recursively process child elements
            if 'child_elements' in element:
                self._identify_merge_candidates(
                    element['child_elements'], 
                    f"{parent_path}_{element['id']}" if parent_path else str(element['id'])
                )
        
        # Handle any remaining group
        if current_group and current_size >= self.min_chunk_size:
            for e in current_group:
                e['action'] = 'merge'
                e['merge_group'] = merge_candidates[-1]['group_id']
        elif current_group:
            for e in current_group:
                e['action'] = 'keep_as_is'
                e.pop('merge_candidate', None)
    
    def _extract_content_recursive(self, element: Dict, document: Dict) -> str:
        """
        Extract the content from an element by its ID.
        """
        # Helper function to find an element by ID in the document
        def find_element_by_id(doc: Dict, elem_id: int) -> Dict:
            if doc.get('id') == elem_id:
                return doc
            
            for child in doc.get('elements', []):
                result = find_element_by_id(child, elem_id)
                if result:
                    return result
            
            return None
        
        elem = find_element_by_id(document, element['id'])
        if not elem:
            return ""
        
        return elem.get('content', '')
    
    def generate_chunks(self, document: Dict, plan: Dict) -> List[Dict]:
        """
        Generate the actual text chunks based on the chunking plan.
        """
        chunks = []
        
        def process_element_plan(element_plan, document):
            element_id = element_plan['id']
            action = element_plan.get('action', 'keep_as_is')
            
            if action == 'chunk':
                # Element is too large, split into multiple chunks
                content = self._extract_content_recursive({'id': element_id}, document)
                chunk_texts = self.text_splitter.split_text(content)
                
                for i, chunk_text in enumerate(chunk_texts):
                    chunks.append({
                        'chunk_id': f"chunk_{element_id}_{i}",
                        'source_element': element_id,
                        'chunk_type': 'split',
                        'content': chunk_text,
                        'size': len(chunk_text)
                    })
            
            elif action == 'merge':
                # This will be handled in a second pass for complete merge groups
                pass
            
            else:  # keep_as_is
                # Element is within size limits, keep as a standalone chunk
                if not element_plan.get('merge_candidate'):
                    content = self._extract_content_recursive({'id': element_id}, document)
                    chunks.append({
                        'chunk_id': f"chunk_{element_id}",
                        'source_element': element_id,
                        'chunk_type': 'single',
                        'content': content,
                        'size': len(content)
                    })
            
            # Process child elements
            for child in element_plan.get('child_elements', []):
                process_element_plan(child, document)
        
        # First pass: process all elements except merges
        for element_plan in plan.get('elements', []):
            process_element_plan(element_plan, document)
        
        # Second pass: handle merge groups
        merge_groups = {}
        
        def collect_merge_groups(element_plan):
            if element_plan.get('action') == 'merge' and 'merge_group' in element_plan:
                group_id = element_plan['merge_group']
                if group_id not in merge_groups:
                    merge_groups[group_id] = []
                
                merge_groups[group_id].append(element_plan['id'])
            
            for child in element_plan.get('child_elements', []):
                collect_merge_groups(child)
        
        # Collect all merge groups
        for element_plan in plan.get('elements', []):
            collect_merge_groups(element_plan)
        
        # Process each merge group
        for group_id, element_ids in merge_groups.items():
            merged_content = ""
            for element_id in element_ids:
                content = self._extract_content_recursive({'id': element_id}, document)
                merged_content += content + "\n\n"  # Add separator between merged elements
            
            if merged_content:
                chunks.append({
                    'chunk_id': f"chunk_{group_id}",
                    'source_elements': element_ids,
                    'chunk_type': 'merged',
                    'content': merged_content.strip(),
                    'size': len(merged_content.strip())
                })
        
        return chunks
    
    def process_document(self, json_file_path: str) -> Tuple[Dict, List[Dict]]:
        """
        Process a document and generate both a chunking plan and actual chunks.
        
        Returns:
            Tuple containing (chunking_plan, text_chunks)
        """
        document = self.load_document(json_file_path)
        plan = self.create_chunking_plan(document)
        chunks = self.generate_chunks(document, plan)
        
        return plan, chunks


# Example usage
if __name__ == "__main__":
    # Initialize chunker with desired parameters
    chunker = DocumentChunker(
        min_chunk_size=800,   # Minimum chunk size in characters
        max_chunk_size=2000,  # Maximum chunk size in characters
        chunk_overlap=50,     # Overlap between chunks
        size_tolerance=0.1    # Allow up to 10% over max size
    )
    
    # Process the document
    chunking_plan, text_chunks = chunker.process_document('sample_doc_structure.json')
    
    # Save the chunking plan
    with open('chunking_plan.json', 'w') as f:
        json.dump(chunking_plan, f, indent=2)
    
    # Save the text chunks
    with open('text_chunks.json', 'w') as f:
        json.dump(text_chunks, f, indent=2)
    
    # Print some stats
    print(f"Generated {len(text_chunks)} chunks from document")
    print(f"Chunk sizes: {[chunk['size'] for chunk in text_chunks]}")