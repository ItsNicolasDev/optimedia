# OptiMedia API

OptiMedia API is a FastAPI-based service designed to compress images and videos, contributing to the optimization of web pages for reduced weight, increased speed, and environmental sustainability.
This was done at less than 10hours, as part of the Nuit de l'Info 2023 by Nicolas Nadé.

## Getting Started

1. Clone the repository: `git clone https://github.com/ItsNicolasDev/optimedia.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the API: `uvicorn main:app --reload`

The API will be accessible at `http://127.0.0.1:8000`.

## Web Interface

OptiMedia includes a user-friendly web interface. Visit `http://127.0.0.1:8000/web` in your browser to access the interface.

![Web Interface](/images/web.png)

## Usage

To compress an image or video, send a POST request to the `/compress` endpoint with a JSON payload containing the URL and maximum size.

Example using cURL:
```bash
curl -X POST "http://127.0.0.1:8000/compress" -H "accept: application/json" -H "Content-Type: application/json" -d '{"url":"https://example.com/sample_image.jpg", "max_size": 1000}'
```
![Request](/images/request.png)

