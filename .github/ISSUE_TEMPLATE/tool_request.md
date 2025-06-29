---
name: New AI Tool Request
about: Request a new AI-discoverable tool
title: '[TOOL] '
labels: 'tool-request', 'enhancement'
assignees: ''

---

## Tool Purpose
<!-- What should this tool do? -->

## Example Usage
<!-- Provide examples of how users would request this functionality -->

User might say:
- "..."
- "..."
- "..."

## Tool Interface
<!-- Describe the expected parameters and return values -->

```python
@ai_tool(
    name="suggested_tool_name",
    description="...",
    examples=[
        # Add examples here
    ]
)
async def tool_function(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    # What should this return?
    pass
```

## Integration Points
<!-- How should this tool integrate with existing tools? -->

- [ ] Works standalone
- [ ] Combines with: [list tools]
- [ ] Requires new dependencies
- [ ] Needs external API access

## Success Criteria
<!-- How do we know this tool is working correctly? -->

- [ ] 
- [ ] 
- [ ] 

## Additional Context
<!-- Any additional information about the tool request -->
