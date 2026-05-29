_SYSTEM = (
    "You are a JFrog documentation assistant. "
    "Answer the question using only the documentation provided. "
    "If the documentation does not contain enough information, say: "
    "'I don't have enough information to answer that. Visit docs.jfrog.com for more.'"
)


def build_prompt(query: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    if not chunks:
        docs_section = "(No documentation found for this query.)"
    else:
        docs_section = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in chunks
        )

    history_section = ""
    if history:
        recent = history[-10:]
        turns = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in recent
        )
        history_section = f"\nConversation history:\n{turns}\n"

    return (
        f"{_SYSTEM}\n\n"
        f"Documentation:\n{docs_section}\n"
        f"{history_section}\n"
        f"Question: {query}\nAnswer:"
    )
