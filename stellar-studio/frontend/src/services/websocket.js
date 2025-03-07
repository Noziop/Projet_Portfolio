// src/services/websocket.js
import apiClient from './api'

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
    this.reconnectTimeout = null;
    this.disabled = true; // Désactivé par défaut
  }

  connect() {
    if (this.disabled) {
      console.log('WebSocket est désactivé, utilisation du polling à la place');
      return;
    }

    if (this.socket) {
      this.socket.close();
    }
    
    // Récupérer le token d'auth
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('Pas de token disponible pour la connexion WebSocket');
      return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws?token=${token}`;
    
    console.log('Connexion WebSocket à:', wsUrl);
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket connecté');
      this.connected = true;
      clearTimeout(this.reconnectTimeout);
    };
    
    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Message WebSocket reçu:', message);
        
        // Dispatch le message aux écouteurs concernés
        if (message.type && this.listeners[message.type]) {
          this.listeners[message.type].forEach(callback => {
            callback(message.data || message);
          });
        }
      } catch (error) {
        console.error('Erreur de traitement du message WebSocket:', error);
      }
    };
    
    this.socket.onclose = (event) => {
      console.log('WebSocket fermé. Code:', event.code, 'Raison:', event.reason);
      this.connected = false;
      
      // Tentative de reconnexion après 5 secondes
      this.reconnectTimeout = setTimeout(() => {
        console.log('Tentative de reconnexion WebSocket...');
        this.connect();
      }, 5000);
    };
    
    this.socket.onerror = (error) => {
      console.error('Erreur WebSocket:', error);
    };
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    clearTimeout(this.reconnectTimeout);
    this.connected = false;
  }
  
  addListener(type, callback) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(callback);
    console.log(`Écouteur pour ${type} ajouté (${this.disabled ? 'WebSocket désactivé' : 'WebSocket actif'})`);
  }
  
  removeListener(type, callback) {
    if (!this.listeners[type]) return;
    
    const index = this.listeners[type].indexOf(callback);
    if (index !== -1) {
      this.listeners[type].splice(index, 1);
      console.log(`Écouteur pour ${type} supprimé`);
    }
  }

  // Active ou désactive le service WebSocket
  setEnabled(enabled) {
    this.disabled = !enabled;
    console.log(`WebSocket ${this.disabled ? 'désactivé' : 'activé'}`);
    
    if (enabled && !this.socket) {
      this.connect();
    } else if (!enabled && this.socket) {
      this.disconnect();
    }
  }
}

// Créer une instance singleton
const websocketService = new WebSocketService();

// Fonction pour initialiser et retourner l'instance
export function createWebSocket(enabled = false) {
  // Définir si WebSocket est activé ou non
  websocketService.setEnabled(enabled);
  
  // Initialiser la connexion si activé
  if (enabled && !websocketService.connected && !websocketService.socket) {
    websocketService.connect();
  }
  return websocketService;
}

// Fonction utilitaire pour activer/désactiver facilement le WebSocket
export function toggleWebSocketGlobally(enabled = false) {
  console.log(`WebSocket globalement ${enabled ? 'activé' : 'désactivé'}`);
  websocketService.setEnabled(enabled);
  return websocketService;
}

// Permettre d'activer rapidement le WebSocket via la console pour déboguer
window.__enableWebSocket = () => toggleWebSocketGlobally(true);
window.__disableWebSocket = () => toggleWebSocketGlobally(false);

// Exporter l'instance par défaut pour la compatibilité
export default websocketService; 