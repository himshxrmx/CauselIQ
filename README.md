# CauseIQ — AI Incident Root Cause Analyzer

An advanced, SRE-focused web application that automatically integrates with AWS CloudWatch and the Gemini 2.5 Flash AI model to diagnose and provide actionable remediations for production incidents.

![CauseIQ Dashboard Preview](https://via.placeholder.com/1000x500.png?text=CauseIQ+Dashboard)

## Features

- **AWS CloudWatch Integration**: Fetches real, live logs from your AWS account (Lambda, ECS, API Gateway, etc.) via `boto3`.
- **AI-Powered Diagnostics**: Uses Google's **Gemini 2.5 Flash** model to analyze raw logs, determine root causes, assess impact, and generate structured JSON responses.
- **Actionable Remediation**: Provides direct, copy-to-clipboard AWS CLI commands to resolve the detected issue.
- **Modern UI**: Dark-themed, glassmorphic React dashboard built with Tailwind CSS v4 and Lucide React.
- **Hackathon-Ready Simulations**: Test the application instantly by simulating pre-configured scenarios.

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Axios, Framer Motion (animations)
- **Backend**: Python 3.13, FastAPI, Uvicorn, Boto3 (AWS SDK), Google GenAI SDK (`google-genai`)
- **Cloud/AI**: AWS CloudWatch, Google Gemini 2.5 Flash (`gemini-2.5-flash`)

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- AWS CLI configured locally (`aws configure`)
- Google Gemini API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/himshxrmx/CauselIQ.git
   cd CauselIQ
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   ```
   *Edit `.env` and add your `GOOGLE_API_KEY`.*

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the App Locally

You can use the unified startup script from the root directory to launch both the frontend and backend concurrently:

```bash
python run.py
```

- **Dashboard:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

## Usage

1. Open the dashboard.
2. Click **+ Simulate Incident**.
3. Select an AWS function or scenario from the list. 
4. The backend will query AWS CloudWatch for the logs, pipe them to Gemini, and stream the structured root cause analysis back to the dashboard in real-time.

## License
MIT License
