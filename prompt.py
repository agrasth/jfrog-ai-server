_SYSTEM = (
    "You are a JFrog documentation assistant. "
    "Answer the question using only the documentation provided. "
    "If the documentation does not contain enough information, say: "
    "'I don't have enough information to answer that. Visit docs.jfrog.com for more.'"
)


def build_prompt(query: str, chunks: list[dict]) -> str:
    if not chunks:
        docs_section = "(No documentation found for this query.)"
    else:
        docs_section = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )
    return f"{_SYSTEM}\n\nDocumentation:\n{docs_section}\n\nQuestion: {query}\nAnswer:"
