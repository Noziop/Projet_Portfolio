FROM node:18-alpine

WORKDIR /app

# Création utilisateur avec le même UID
RUN adduser -u 1030 -D nodeuser && \
    chown -R nodeuser:nodeuser /app

USER nodeuser

# Copie des fichiers avec les bonnes permissions
COPY --chown=nodeuser:nodeuser package*.json ./
RUN npm install

# Copie du reste du code
COPY --chown=nodeuser:nodeuser . .

CMD ["npm", "run", "dev", "--", "--port", "8080", "--host", "0.0.0.0"]