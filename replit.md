# Overview

This is a Flask-based Poultry Farm Management System designed for the Smart India Hackathon. The application provides comprehensive farm management capabilities including real-time dashboard analytics, daily data entry forms, and interactive reporting with Chart.js visualizations. It features a clean, responsive Bootstrap 5 interface with a dark theme optimized for modern web browsers.

The system manages key poultry farm metrics including chicken counts, egg production, feed consumption, and expense tracking. It includes hardcoded admin authentication for demo purposes and uses in-memory data storage with pre-populated sample data for immediate demonstration capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework Architecture
- **Flask Application Structure**: Uses a standard Flask app with route-based request handling and Jinja2 templating
- **Session Management**: Flask sessions for user authentication state with configurable secret keys
- **Template Inheritance**: Base template with extending child templates for consistent UI structure
- **Static Asset Organization**: Separate CSS and JavaScript files with CDN dependencies for Bootstrap and Chart.js

## Data Management Layer
- **In-Memory Storage**: Uses Python dictionaries and lists for data persistence within application runtime
- **DataManager Class**: Centralized data operations with methods for adding daily data and generating dashboard summaries
- **Sample Data Initialization**: Pre-populated with 7 days of demonstration data for immediate functionality
- **Date-based Indexing**: Daily farm data organized by date keys for efficient retrieval

## Authentication System
- **Hardcoded Credentials**: Simple admin login with username "admin" and password "password123" for demo purposes
- **Session-based Security**: Login state maintained in Flask session with logout functionality
- **Route Protection**: Navigation and features only accessible when logged in

## Frontend Architecture
- **Bootstrap 5 Framework**: Responsive grid system with dark theme customization
- **Component-based UI**: Modular cards, forms, and navigation elements with consistent styling
- **Interactive Charts**: Chart.js integration for data visualization with custom styling
- **Progressive Enhancement**: JavaScript charts with fallback error handling

## API Design
- **RESTful Endpoints**: Clean URL structure for dashboard, data entry, reports, and authentication
- **JSON API Routes**: Dedicated endpoints for chart data with error handling
- **Form Processing**: POST request handling with validation and flash messaging

# External Dependencies

## Frontend Libraries
- **Bootstrap 5**: CSS framework from CDN with Replit dark theme customization
- **Font Awesome 6.4.0**: Icon library for UI elements and visual hierarchy
- **Chart.js 4.4.0**: JavaScript charting library for interactive data visualization

## Python Libraries
- **Flask**: Core web framework for routing, templating, and session management
- **Python Standard Library**: datetime, timedelta, collections, os, and logging modules for core functionality

## Development Dependencies
- **Logging Module**: Built-in Python logging for debugging and error tracking
- **Environment Variables**: OS environment variable support for configuration management

## Hosting Environment
- **Replit Platform**: Configured for Replit hosting with custom theme integration
- **Port Configuration**: Flask app configured for host 0.0.0.0 on port 5000 with debug mode