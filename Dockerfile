FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN wget -qO- https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY webautomate_ai/pyproject.toml webautomate_ai/poetry.lock ./webautomate_ai/

# Install Node.js dependencies
RUN npm install

# Install Python dependencies
RUN pip install poetry && \
    cd webautomate_ai && \
    poetry config virtualenvs.create false && \
    poetry install --no-root && \
    poetry run playwright install --with-deps

# Copy the rest of the application
COPY . .

# Build the application
RUN cd webautomate_ai && python build.py

# Set the command to run your application
CMD ["npm", "start"]
