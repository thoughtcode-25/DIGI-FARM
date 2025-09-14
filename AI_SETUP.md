
# AI Provider Setup Guide

## Supported AI Providers

### 1. Google Gemini (Recommended - Cost Effective)
- **Cost**: ~$0.075 per 1K tokens (much cheaper than OpenAI)
- **Setup**: Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Environment Variable**: `GEMINI_API_KEY`

### 2. OpenAI (Fallback)
- **Cost**: ~$0.03 per 1K tokens for GPT-4
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Environment Variable**: `OPENAI_API_KEY`

## Configuration Priority

1. **Primary**: Gemini (if `GEMINI_API_KEY` is set)
2. **Fallback**: OpenAI (if `OPENAI_API_KEY` is set)
3. **Last Resort**: Static farming advice

## Cost Comparison (Monthly estimates)

| Usage Level | Gemini Cost | OpenAI Cost | Savings |
|-------------|-------------|-------------|---------|
| Light (1K queries) | $2-5 | $15-30 | 70-85% |
| Medium (5K queries) | $10-25 | $75-150 | 65-80% |
| Heavy (10K queries) | $20-50 | $150-300 | 65-80% |

## Setup Instructions

1. Get Gemini API key from Google AI Studio
2. Add to Replit Secrets: `GEMINI_API_KEY`
3. Keep OpenAI key as backup (optional)
4. System automatically uses cheapest available provider

## Features Supported

✅ Chat assistance (both providers)
✅ Disease image analysis (both providers)  
✅ IoT sensor analysis (both providers)
✅ Prevention plan generation (both providers)
✅ Automatic fallback system
