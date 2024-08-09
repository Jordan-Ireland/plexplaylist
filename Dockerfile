# Dockerfile

# Use the official image as a parent image
FROM python:3.11.8-slim

#set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# make port available to the world outside this container
EXPOSE ${PORT}

# Run app.py when the container launches
CMD ["python", "app.py"]