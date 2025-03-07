# Base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies ( --no-cache-dir)
COPY requirements.txt . 
RUN pip install -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Command to run the bot.py and three separate RQ workers
CMD ["python", "bot.py"]