FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install
RUN npm install @vitejs/plugin-vue --save-dev

# Ajouter un utilisateur non-root et donner les permissions
RUN adduser -D nodeuser && \
    mkdir -p node_modules/.vite && \
    chown -R nodeuser:nodeuser /app && \
    chmod -R 755 node_modules

# Switcher vers l'utilisateur non-root
USER nodeuser

# Copy application code
COPY . .

# Corriger le script de démarrage (il y avait un doublon dans les options)
EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--port", "8080", "--host"]
