# CMD: docker build -t linebot .
# Use an official Python runtime as a parent image
FROM python:3.8

ENV TZ 'Asia/Taipei'
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ./ .

# Install the dependencies
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose port 8000 for the application
EXPOSE 8000

# Run the command to start the application
CMD [ "python3", "appLineBot.py" ]
