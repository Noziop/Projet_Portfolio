FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install  # Au lieu de npm ci

# Ajouter un utilisateur non-root et donner les permissions
RUN adduser -D nodeuser && \
    mkdir -p node_modules/.vite && \
    chown -R nodeuser:nodeuser /app && \
    chmod -R 755 node_modules

USER nodeuser

COPY --chown=nodeuser:nodeuser . .

EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--port", "8080", "--host"]
