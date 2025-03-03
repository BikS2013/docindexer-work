# File Iterator Implementation Task

## Objective
Create a FileIterator class that generates a list of files to be processed based on CLI configuration parameters.

## Requirements

### Core Functionality
1. Implement a FileIterator class that:
   - Accepts the populated CLI Configuration object as input
   - Generates a list of file paths based on the configuration parameters
   - Provides methods to iterate through and access the file list
   - Handles various filtering options (extensions, recursive search, etc.)

2. FileIterator should specifically handle these configuration options:
   - Directory path(s) to search
   - File pattern matching (glob patterns, regex, etc.)
   - Inclusion/exclusion filters
   - Recursive vs. non-recursive search
   - Sorting options (by name, date, size, etc.)
   - Max depth for recursive searches

3. Implement a CLI controller that:
   - Uses the Configuration class to validate and process arguments
   - Utilizes the FileIterator to generate the file list
   - Displays the list of files to the console (no file operations yet)
   - Provides appropriate error handling and user feedback

### Technical Specifications
1. Follow SOLID principles:
   - Single Responsibility: FileIterator should only handle file discovery
   - Open/Closed: Design for extensibility with new filtering mechanisms
   - Liskov Substitution: Properly use inheritance if any subclasses are created
   - Interface Segregation: Define clear interfaces for iteration
   - Dependency Inversion: Depend on abstractions not concrete implementations

2. Implement proper error handling for:
   - Invalid paths
   - Permission issues
   - Non-existent directories
   - Malformed patterns

3. Performance considerations:
   - Implement lazy loading/evaluation where appropriate
   - Consider memory usage for large directory structures
   - Add proper cancellation support for long-running operations

4. Testing:
   - Include unit tests covering all main functionality
   - Add integration tests with the CLI controller
   - Test edge cases (empty directories, maximum path lengths, etc.)

## Integration Points
1. The FileIterator class should integrate with the existing Configuration class
2. The CLI controller should use both Configuration and FileIterator classes
3. No actual file processing should be implemented yet

## Deliverables
1. FileIterator class implementation
2. CLI controller implementation or extension
3. Unit and integration tests
4. Documentation including:
   - Class diagrams showing relationships
   - Usage examples
   - API documentation

## Constraints
- No actual file operations/modifications should be implemented
- Focus only on file discovery and listing functionality
- Must maintain compatibility with the existing Configuration class

----------------------------------------------------------------------
I want you to create a markdown file to explain in detail the structure, the capabilities and use cases of the FileIterator class and its supporting classes and code. 
----------------------------------------------------------------------
Can you add some diagrams (mermaid format) to visualize the content and make your explanation easily understandable?
----------------------------------------------------------------------
I want you to put the list command in a dedicated code file.

----------------------------------------------------------------------

I want you to create a file iterator class 
to get the cli configuration class (as populated by the cli interface) as input, 
and use it to create a list of files to be processed, according to the input parameters. 

The cli controller will get the file list from the file iterator and will display it 
on the console given that there aren't any file operations implemented yet. 

The code you will write must be structured, following the SOLID principles and be according the known coding best practices. 