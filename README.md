# KIWICLI2

## Overview
KIWICLI2 is a portfolio management application designed to help users manage their investments, track transactions, and view portfolio performance. The application provides a seamless user experience with a React frontend and a Flask backend. It integrates with external APIs like Alpha Vantage for real-time stock data and uses AWS Cognito for secure authentication.

## Project Structure

The project is organized as follows:

```
KIWICLI2/
├── app/                # Backend application code
│   ├── auth/           # Authentication logic
│   ├── models/         # Database models
│   ├── routes/         # API routes
│   ├── service/        # Business logic and external API integrations
│   └── main.py         # Application entry point
├── frontend/           # Frontend application code
│   ├── src/            # React components, pages, and utilities
│   ├── public/         # Static assets
│   └── vite.config.js  # Vite configuration
├── tests/              # Backend test cases
├── requirements.txt    # Python dependencies
├── package.json        # Node.js dependencies
└── README.md           # Project documentation
```

## Intent of Operations

KIWICLI2 is built to provide the following core functionalities:

1. **Portfolio Management**:
   - Create, update, and delete investment portfolios.
   - View portfolio performance and holdings.

2. **Transaction Tracking**:
   - Record buy and sell transactions for securities.
   - View transaction history.

3. **Real-Time Data Integration**:
   - Fetch real-time stock data using the Alpha Vantage API.

4. **Secure Authentication**:
   - User authentication and authorization using AWS Cognito.

5. **Responsive Frontend**:
   - A modern, responsive user interface built with React and Vite.

## Prerequisites

Before starting, ensure you have the following installed:

- **Node.js** (v16 or higher)
- **Python** (v3.9 or higher)
- **Git**

## Repository

Clone the repository from GitHub:

```bash
git clone https://github.com/tkitchenjr/KIWICLI2.git
cd KIWICLI2
```

## Backend Setup

1. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**

   Create a `.env` file in the root directory and configure the following variables:

   ```env
   FLASK_APP=app.main
   FLASK_ENV=development
   PORT=5050
   ```

   **Note:** Do not include sensitive data like API keys in the README.

4. **Run the backend server:**

   ```bash
   python3 -m flask run --port=5050
   ```

   The backend will be available at `http://localhost:5050`.

## Frontend Setup

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Run the development server:**

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`.

## Running the Application

To run the functional application:

1. Start the backend server:

   ```bash
   python3 -m flask run --port=5050
   ```

2. In a separate terminal start the frontend development server:

   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173` to access the application.

## Deployment

For deployment, ensure you configure production-ready settings for both the frontend and backend. Refer to the documentation for your hosting provider for specific instructions.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
