import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

def ask_model(prompt: str) -> str:
    # define payload dictionary
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "think": False,
    }

    # Create Request Object
    request = Request(
        OLLAMA_URL,
        data = json.dumps(payload).encode("utf-8"),
        headers = {"Content-Type": "application/json"},
        method = "POST",
    )
    # Handle possible errors
    try:
        with urlopen(request, timeout=120) as response:
            result = json.load(response)
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors = "replace")
        raise RuntimeError(
            f"Ollama returned HTTP {exc.code}: {details}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama. Make sure the Ollama app is running"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            "The request to Ollama timed out"
        ) from exc
 

    # Get content from response message
    content = result.get("message", {}).get("content")

    # Verify content is a string and not empty
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned no usable text response")

    return content.strip()

def main() -> None:
    prompt = (
        "You are helping test a local file organizer application. "
        "Reply with one short sentence confirming you received this message."
    )

    try:
        reply = ask_model(prompt)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}")
        return

    print(f"Model: {MODEL}")
    print(f"Reply: {reply}")


if __name__ == "__main__":
    main()