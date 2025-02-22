# Gunakan image Node.js resmi
FROM node:16

# Set working directory
WORKDIR /app

# Copy package.json dan package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy seluruh kode aplikasi
COPY . .

# Build aplikasi Nuxt.js
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Jalankan Nuxt.js
CMD ["npm", "run", "start"]