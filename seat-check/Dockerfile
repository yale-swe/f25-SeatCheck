# Use Node.js LTS as base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port 8081 (Expo default)
EXPOSE 8081

# Start the Expo web server
CMD ["npm", "run", "web"]
