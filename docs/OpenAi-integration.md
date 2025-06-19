# NEBedu - AI Learning Companion 🤖📚
<div align="center">
   <img height="180" width="180" src="https://github.com/user-attachments/assets/daa5d212-12b8-49e7-8d72-f8a57a7b0b46">
</div>

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Offline First](https://img.shields.io/badge/Offline-First-green)](https://github.com/yourusername/NEBedu)

An offline-first, community-editable AI learning companion for Grade 10 students in Nepal, focusing on Computer Science, Science, and English subjects. Built with lightweight AI models and structured educational content, designed to work in low-resource environments.


# OpenAI Proxy Integration Guide for NEBedu

## Overview

NEBedu supports secure, online Q&A using OpenAI models via a proxy server. This allows students to ask any question and get an answer from OpenAI, **without ever exposing the OpenAI API key to the user**. This guide details how the proxy integration works, how to set it up, and best practices for security and maintenance.

---

## 1. How the Proxy Works

### Architecture & Flow
- The NEBedu client app (student/teacher) sends questions to a secure proxy server (FastAPI-based).
- The proxy server authenticates requests using a `PROXY_AUTH_KEY` and uses its own `OPENAI_API_KEY` to call OpenAI.
- The answer is returned to the client. The OpenAI API key is **never** sent to or stored on the client.

**Diagram:**
```
[Student App] --(question + PROXY_AUTH_KEY)--> [Proxy Server] --(OPENAI_API_KEY)--> [OpenAI API]
      ^                                                                                 |
      |-------------------(answer) <---------------------------------------------------|
```

---

## 2. Roles & Responsibilities

- **Stakeholders/IT Admins:**
  - Set up and maintain the proxy server.
  - Manage environment variables and secrets.
  - Monitor usage and security.
- **Teachers/Students:**
  - Use the NEBedu app as normal. No server setup or configuration required.

---

## 3. Setting Up the Proxy Server

### Prerequisites
- Python 3.8+
- FastAPI, Uvicorn, OpenAI Python SDK
- A secure server (cloud VM, on-prem, etc.)

### Installation
```bash
pip install fastapi uvicorn openai
```

### Environment Variables
- `OPENAI_API_KEY` — Your OpenAI API key (never shared with users)
- `PROXY_AUTH_KEY` — A strong secret key for authenticating client requests

### Example: Running the Proxy Server
```bash
export OPENAI_API_KEY=sk-...your-openai-key...
export PROXY_AUTH_KEY=super-secret-proxy-key
uvicorn openai_proxy:app --host 0.0.0.0 --port 8000
```

### Security Configuration
- **HTTPS:** Use a reverse proxy (Nginx, Caddy) or cloud provider to serve over HTTPS.
- **CORS:** Restrict allowed origins in FastAPI:
  ```python
  ALLOWED_ORIGINS = ["https://yourdomain.com"]
  ```
- **Firewall:** Restrict access to only trusted networks if possible.

### Rate Limiting & Monitoring
- The proxy implements per-user rate limiting (default: 10 requests/minute/user).
- Monitor logs for abuse or unusual activity.

---

## 4. Configuring the Client (Student App)

- **No OpenAI API key is ever needed on the client.**
- Set the following environment variables on the client device:
  - `OPENAI_PROXY_URL` — The URL of your proxy server (e.g., `https://your-proxy.com/ask`)
  - `OPENAI_PROXY_KEY` — The value of `PROXY_AUTH_KEY` (to authenticate to the proxy)

### Example: Running the Client
```bash
export OPENAI_PROXY_URL=https://your-proxy.com/ask
export OPENAI_PROXY_KEY=super-secret-proxy-key
python -m student_app.interface.cli_interface
```

---

## 5. Security Best Practices

- **Never share the OpenAI API key with users.**
- Use a strong, unique `PROXY_AUTH_KEY` and rotate it periodically.
- Use HTTPS for all communications.
- Restrict CORS origins to trusted domains.
- Monitor and log all requests.
- Set up alerts for rate limit violations or suspicious activity.
- Regularly update dependencies and patch security vulnerabilities.

---

## 6. Troubleshooting

- **Mock Answer Displayed:**
  - Cause: The client cannot reach the proxy server, or environment variables are not set.
  - Solution: Ensure the proxy is running and the client has correct `OPENAI_PROXY_URL` and `OPENAI_PROXY_KEY`.

- **Authentication Error:**
  - Cause: The `PROXY_AUTH_KEY` on the server and `OPENAI_PROXY_KEY` on the client do not match.
  - Solution: Update the client to use the correct key.

- **Rate Limit Exceeded:**
  - Cause: Too many requests from a user in a short time.
  - Solution: Wait and try again later.

- **CORS Error:**
  - Cause: The proxy server is not allowing requests from the client's domain.
  - Solution: Update `ALLOWED_ORIGINS` in the proxy server config.

---

## 7. Example Flows

### Student Q&A (Success)
1. Student opens NEBedu and selects "Search with OpenAI (Online)".
2. Student enters a question.
3. The app sends the question to the proxy server with the `OPENAI_PROXY_KEY`.
4. The proxy authenticates, calls OpenAI, and returns the answer.
5. The student sees the answer in the app.

### Student Q&A (Proxy Down or Not Configured)
1. Student tries to use online Q&A.
2. The app cannot reach the proxy or is missing config.
3. The app displays a mock answer and suggests using offline features.

---

## 8. FAQ

**Q: Who should set up the proxy server?**
A: The NEBedu technical team or your school's IT administrator. Teachers and students do not need to set up or manage the server.

**Q: Is my OpenAI API key safe?**
A: Yes! The key is only stored on the proxy server and never shared with clients or users.

**Q: Can students or teachers use the online Q&A feature offline?**
A: No, online Q&A requires internet access and a running proxy server. All other features work offline.

**Q: How do I rotate the proxy key?**
A: Change `PROXY_AUTH_KEY` on the server and update `OPENAI_PROXY_KEY` on all clients.

**Q: What if the proxy is abused?**
A: Monitor logs, rotate keys, and restrict access as needed. Consider IP allow-listing for extra security.

---

## 9. References
- See `OpenAi_Proxy/openai_proxy.py` for the proxy server code.
- See `student_app/learning/openai_proxy_client.py` for the client integration.
- See `readme.md` for a user-friendly overview.
- See `architecture.png` for a visual diagram (if available).

--- 