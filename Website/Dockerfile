# Use the official Python 3.12 slim image as the base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install the dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Expose the port the Flask app runs on
EXPOSE 5000

# Set the environment variable to indicate the app is running in production
ENV FLASK_ENV=production

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
