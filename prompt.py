_SYSTEM = (
    "You are a JFrog documentation assistant. "
    "Answer the question directly and concisely using only the documentation provided. "
    "Extract the relevant information and explain it clearly — do not say 'refer to the docs' or 'see the documentation'. "
    "Do not generate, invent, or include any URLs or links. "
    "Format your answer for a terminal: use newlines between paragraphs, "
    "indent code examples with 2 spaces (no markdown fences), "
    "and keep answers concise and scannable. "
    "If the documentation does not contain enough information to answer, say: "
    "'I don't have enough information to answer that.'"
)


def build_prompt(query: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    if not chunks:
        docs_section = "(No documentation found for this query.)"
    else:
        docs_section = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text'][:800]}" for c in chunks
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
