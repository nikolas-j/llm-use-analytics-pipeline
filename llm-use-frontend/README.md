# LLM Use Analytics Frontend

## Overview

Simple web dashboard for visualizing LLM usage metrics retrieved from the REST API. Displays daily team adoption rates, task categories, and conversation volumes.

## Configuration

**API Endpoint:** Set in [script.js](script.js) - Update the `API_BASE_URL` constant to point to your API Gateway URL:
```javascript
const API_BASE_URL = 'https://your-api-gateway-url';
```

## AWS Deployment

**CloudFront + S3:**
1. Upload `index.html`, `script.js`, `styles.css` to S3 bucket
2. Enable static website hosting
3. Create CloudFront distribution pointing to S3 bucket
4. Update API endpoint in `script.js` before deployment

## Limitations

- **Demo purposes only** - Basic visualization for proof-of-concept
- **CORS protection only** - No authentication or authorization
- **No persistent storage** - Data fetched on demand from API
- **Suitable as foundation** for building production analytics dashboards with proper security, authentication, and advanced visualizations
