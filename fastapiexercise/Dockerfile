# fastapiexercise/Dockerfile (This file needs to be updated in your GitHub repo)
FROM python:3.11.4

# Set the working directory inside the container.
# We'll copy all necessary files here.
WORKDIR /app

# Copy requirements.txt.
# Since this Dockerfile is in `fastapiexercise/` and the context is the Git repo root,
# we need to specify the path relative to the Git repo root.
# The previous error "COPY requirements.txt ." suggested that BuildKit might be
# implicitly treating the Dockerfile's location as the base for `COPY` source paths.
# Let's try specifying the full path relative to the build context again, as it should work.
# If this still fails with "requirements.txt: not found", then the alternative COPY . .
# below would be the most robust.
COPY fastapiexercise/requirements.txt .

# Install dependencies before copying the rest of the application
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'fastapiexercise' directory from the build context (the cloned Git repo root)
# into the /app directory inside the container.
# This ensures all your application code, including `myproject/`, `config.toml`, etc.,
# is available inside the container.
COPY fastapiexercise/ .

# Command to run the FastAPI application
# Ensure 'myproject.app.myapi:app' is the correct module path relative to /app
CMD ["uvicorn", "myproject.app.myapi:app", "--host", "0.0.0.0", "--port", "8000"]