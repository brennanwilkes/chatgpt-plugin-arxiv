# Use the official Python image as the base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the port your app will run on
EXPOSE 5001

# Run the application
CMD ["python", "main.py"]
