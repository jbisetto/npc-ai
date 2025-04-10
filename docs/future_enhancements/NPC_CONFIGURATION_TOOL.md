# NPC Configuration Management Tool

## Executive Summary

As our language learning game evolves, we're facing increasing challenges in managing the interdependent configuration elements that define NPC behavior. Currently, developers must manually edit multiple JSON and YAML files across different directories, with no validation of cross-references or dependencies. This process is error-prone and lacks a unified interface for viewing related configuration components.

I propose developing a comprehensive **NPC Configuration Management Tool** that provides a centralized interface for viewing, creating, editing, and deleting configuration elements while maintaining consistency across the entire system. This tool will significantly improve developer productivity and reduce configuration errors.

## Current Challenges

Our game's configuration is currently spread across multiple files:

1. **NPC Profiles** (`src/data/profiles/*.json`): Define NPC personalities, knowledge areas, and behavior
2. **Knowledge Base** (`src/data/knowledge/tokyo-train-knowledge-base.json`): Contains game world information
3. **Configuration** (`src/config/npc-config.yaml`): System-wide settings for LLM backends and other parameters
4. **Prompt Templates**: Used in various parts of the system to generate LLM prompts

This fragmented approach creates several problems:

1. **No Dependency Tracking**: Changes to an NPC's knowledge areas aren't validated against the knowledge base
2. **Manual Cross-Referencing**: Developers must manually check references across files
3. **Inconsistent Editing**: No standardized process for making changes
4. **Hidden Relationships**: Difficult to visualize how profiles relate to each other (inheritance)
5. **Error-Prone Updates**: Easy to introduce typos or invalid references
6. **Poor Discoverability**: New developers struggle to understand the configuration structure

## Proposed Solution: NPC Configuration Management Tool

I propose building a unified configuration management tool with these key features:

### 1. Central Dashboard

A web-based interface showing:
- Overview of all NPCs and their relationships
- Knowledge base entries with usage statistics
- Config settings with environment-specific values
- System health and validation status

### 2. NPC Profile Management

- View all profiles with filtering and sorting
- Visualize profile inheritance relationships as a tree/graph
- Edit profiles with real-time validation
- Create new profiles with templates and inheritance selection
- Delete profiles with dependency checking

### 3. Knowledge Base Management

- Browse and search knowledge entries by type, importance, or related NPC
- Edit knowledge entries with syntax highlighting and formatting
- Add new knowledge entries with templates for different knowledge types
- Delete knowledge entries with usage analysis to prevent breaking references
- Visualize which NPCs reference specific knowledge entries

### 4. Configuration Management

- Edit `npc-config.yaml` with schema validation
- Environment-specific configuration views
- History of configuration changes
- Configuration presets for different scenarios (development, testing, production)

### 5. Prompt Template Management

- View and edit prompt templates
- Test templates with sample data
- Version history of template changes
- Template validation against available variables

### 6. Validation & Consistency Features

- **Cross-Reference Validation**: Ensure NPC knowledge areas reference valid knowledge base entries
- **Schema Validation**: Verify all JSON/YAML follows required schemas
- **Dependency Checking**: Prevent deletion of referenced items
- **Impact Analysis**: Show what would be affected by a change
- **Bulk Operations**: Safely update multiple related elements

## Technical Architecture

The tool will be built as a lightweight web application with:

1. **Backend**:
   - Python Flask/FastAPI service
   - File system access to read/write configuration files
   - Validation logic for all file types
   - Change tracking and version control integration

2. **Frontend**:
   - React-based UI with modern components
   - Interactive graph visualization for relationships
   - Form-based editors with validation
   - Search and filtering capabilities

3. **Integration Points**:
   - Version control system integration (Git)
   - CI/CD pipeline hooks for validation
   - Local development environment connection

## Implementation Plan

### Phase 1: Core Framework (2 weeks)
- Set up basic web application structure
- Implement file readers/writers for all configuration types
- Create basic CRUD operations for each entity type
- Develop schema validation

### Phase 2: UI Development (3 weeks)
- Build dashboard and navigation
- Implement entity-specific editors
- Create visualization components for relationships
- Develop search and filtering capabilities

### Phase 3: Validation & Cross-Referencing (2 weeks)
- Implement cross-entity validation
- Add dependency tracking
- Create impact analysis tools
- Develop bulk operations

### Phase 4: Testing & Documentation (1 week)
- Comprehensive testing across all features
- Documentation for users and developers
- Integration with existing workflows

## Expected Benefits

1. **Reduced Configuration Errors**: Validation prevents common mistakes
2. **Improved Developer Productivity**: 30-50% time savings on configuration tasks
3. **Better Onboarding**: New developers can understand the system more quickly
4. **Enhanced Collaboration**: Clearer visibility into configuration changes
5. **Safer Updates**: Impact analysis prevents breaking changes
6. **Configuration Consistency**: Ensures all related elements stay synchronized

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| File format changes | Design for extensibility with schema versioning |
| Performance with large files | Implement lazy loading and pagination |
| Concurrent edits | Add locking or merge capabilities |
| Learning curve | Provide inline documentation and tooltips |
| Git integration complexity | Start with simple file system access, add VCS later |

## Success Criteria

The tool will be considered successful if it:

1. Reduces configuration errors by 80%
2. Decreases time spent on configuration tasks by 30%
3. Achieves 80% developer adoption within 1 month
4. Demonstrates measurable improvements in onboarding time
5. Enhances overall system stability through better configuration

## Next Steps

1. Gather detailed requirements from the development team
2. Create mockups for key interface screens
3. Develop a prototype focused on read-only visualization
4. Establish validation rules for all configuration types
5. Begin implementation of Phase 1

## Conclusion

The proposed NPC Configuration Management Tool addresses a critical need in our development workflow. By providing a unified interface with validation and relationship management, it will significantly improve our ability to maintain consistency across the system's configuration. This investment will pay dividends through enhanced productivity, fewer errors, and a more maintainable codebase.

The tool aligns with our broader goals of improving developer experience and ensuring high-quality gameplay. I recommend we prioritize this work to address the increasing complexity of our configuration system before it becomes an even larger barrier to efficient development. 