# Extracting Panopto Transcripts for LLM and RAG Pipelines

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22010162.svg)](https://doi.org/10.5281/zenodo.22010162)

Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) pipelines require clean, structured text to function effectively. Extracting closed-caption transcripts from Panopto for this purpose presents a unique technical challenge: the platform's public REST API does not currently feature a native endpoint for exporting transcripts directly as plain text or JSON.

While caption uploads and deletions can be managed via the standard API, downloading existing caption tracks relies on a legacy web handler known as `GenerateSRT.ashx`. This article outlines the documented, programmatic approach to navigating this legacy handler, sanitising the output, and serialising the transcript data into a structured JSON payload.

## The Authentication Challenge

The primary hurdle in automating this extraction is that the `GenerateSRT.ashx` endpoint does not accept modern OAuth2 Bearer tokens directly within the HTTP headers. Standard authentication attempts against this endpoint will typically fail or return an empty payload.

To bypass this, you must execute a specific two-step authentication handshake:

1. A standard OAuth2 token is generated.
2. This token is exchanged via a specific endpoint to acquire a legacy session cookie, which is then used to authorise the download.

## The Extraction Pipeline

<img width="1223" height="917" alt="image" src="https://github.com/user-attachments/assets/1be0bab8-42ed-4148-b302-e2fdd5f08714" />


The extraction process follows a strict five-step pipeline (see *Fig. 1: Panopto transcript extraction & ingestion pipeline*):

1. **OAuth2 Authentication** — The script authenticates against the Panopto server using the password grant type, passing the Client ID and Client Secret via HTTP Basic Authentication to retrieve a Bearer access token.

2. **Session Cookie Exchange** — The Bearer token is submitted to the `/api/v1/auth/legacyLogin` endpoint. This returns an `.ASPXAUTH` session cookie in the response headers.

3. **Transcript Retrieval** — The script queries `GenerateSRT.ashx` using the `.ASPXAUTH` cookie. Because Panopto maps caption tracks internally to either language strings (e.g., `English_UK`) or integer IDs (e.g., `1`), the request must iterate through common identifiers to locate the active track.

4. **Data Cleansing** — The raw response is returned in SubRip Subtitle (`.srt`) format. The script uses regular expressions to strip sequence numbers, timestamps, system disclaimers (such as `[Auto-generated transcript]`), and HTML formatting, leaving only plain text.

5. **JSON Export** — The sanitised text and session metadata are serialised into a clean JSON file, ready for pipeline ingestion.

## Implementation Prerequisites

To implement this workflow, you require:

- Python version 3.8 or higher.
- A user account with viewing access to the target Panopto videos.
- A Panopto API Client created under **System > API Clients**. Crucially, the Client Type must be set strictly to **User Based Server Application**. Other client types will result in an `invalid_client` error from the server.

## Configuration and Execution

Once the Python environment is established and the `requests` library is installed, the extraction script requires basic configuration. The credentials and target session ID are defined as variables:

```python
SERVER = "your-instance.cloud.panopto.eu"
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
USERNAME = "your-username"
PASSWORD = "your-password"
SESSION_ID = "panopto-session-delivery-id"
```

When the script is executed, the `requests.Session()` object automatically manages the transition from the OAuth2 token to the `.ASPXAUTH` cookie, passing it to the final download handler.

## The Output Structure

Upon successful execution, the pipeline generates a structured JSON file formatted specifically for LLM context windows or vector database ingestion. The output removes all chronological distractions and isolates the core content:

```json
{
    "source": "Panopto",
    "session_id": "8e8a64d9-2d24-4048-8362-b4aa00a94349",
    "language_track": "1",
    "transcript": "Cleaned transcript text ready for context window or vector database ingestion."
}
```


#hopethishelps

/JV
