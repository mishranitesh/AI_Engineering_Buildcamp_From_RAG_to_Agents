from app.tools.knowledge_base import add_document

# language-neutral version for now
patterns = [
    ("service-layer", "Best practice: Keep business logic in a service layer separate from HTTP route handlers. Routes should only handle request/response concerns."),
    ("session-management", "Best practice: Always release external resources (DB sessions, connections) in a finally block or using context managers to prevent leaks."),
    ("input-validation", "Best practice: Validate and sanitize all inputs at the API boundary using schema validation before passing to the service layer."),
    ("http-exceptions", "Best practice: Service layer should raise domain exceptions (ValueError, NotFoundError). Let the API layer catch and translate them to HTTP responses."),
    ("test-isolation", "Best practice: Each test should be fully isolated — use setup/teardown fixtures that reset state before and after every test function."),
    ("error-handling", "Best practice: Always handle rollback on failure when mutating shared state (DB, files). Leave the system in a consistent state on error."),
    ("api-contracts", "Best practice: Define explicit request and response schemas at the API boundary. Never expose internal data models directly."),
    ("separation-of-concerns", "Best practice: Separate data models (DB schema), business models (domain logic), and API schemas (request/response) into distinct layers."),
]

for doc_id, text in patterns:
    add_document(doc_id, text, {"type": "best_practice"})

print("Knowledge base seeded.")