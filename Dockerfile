FROM python:3.12

# Set working directory
WORKDIR /app

# Install system packages and uv dependencies
RUN apt-get update && \
    apt-get install -y curl gcc libpq-dev

# Install uv via pip
RUN pip install uv

# Copy pyproject and lock file
COPY pyproject.toml uv.lock ./

# Install dependencies with uv into system site-packages
RUN uv pip install --system --no-deps .

# Copy the rest of the project
COPY . .

# Set Flask environment variables (if you're using Flask for your project)
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Expose the port
EXPOSE 8080

# Start the Flask app using uv
CMD ["uv", "run", "app.py"]
