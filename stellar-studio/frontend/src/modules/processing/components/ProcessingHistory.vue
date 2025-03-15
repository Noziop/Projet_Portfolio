<!-- src/modules/processing/components/ProcessingHistory.vue -->
<template>
    <v-card>
      <v-card-title class="d-flex align-center">
        Processing History
        <v-spacer></v-spacer>
        <v-chip
          v-if="hasActiveTask"
          color="info"
          size="small"
        >
          Processing...
        </v-chip>
      </v-card-title>
      
      <v-card-text class="pa-0">
        <v-list lines="two">
          <v-list-item
            v-for="task in history"
            :key="task.id"
            :subtitle="formatTimestamp(task.timestamp)"
            :prepend-icon="getTaskIcon(task.status)"
            :active="task.status === 'completed'"
            :disabled="task.status === 'failed'"
            @click="handleTaskClick(task)"
          >
            <template v-slot:title>
              <div class="d-flex align-center">
                <span>{{ task.filter }}</span>
                <v-chip
                  class="ml-2"
                  size="x-small"
                  :color="getStatusColor(task.status)"
                >
                  {{ task.status }}
                </v-chip>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </template>
  
  <script>
  export default {
    name: 'ProcessingHistory',
    
    props: {
      history: {
        type: Array,
        default: () => []
      }
    },
    
    emits: ['select-task'],
    
    computed: {
      hasActiveTask() {
        return this.history.some(task => 
          task.status === 'processing' || task.status === 'queued'
        );
      }
    },
    
    methods: {
      formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
      },
      
      getTaskIcon(status) {
        switch (status) {
          case 'completed': return 'mdi-check-circle';
          case 'processing': return 'mdi-progress-clock';
          case 'queued': return 'mdi-clock-outline';
          case 'failed': return 'mdi-alert-circle';
          default: return 'mdi-help-circle';
        }
      },
      
      getStatusColor(status) {
        switch (status) {
          case 'completed': return 'success';
          case 'processing': return 'info';
          case 'queued': return 'warning';
          case 'failed': return 'error';
          default: return 'grey';
        }
      },
      
      handleTaskClick(task) {
        if (task.status === 'completed' || task.status === 'processing') {
          this.$emit('select-task', task);
        }
      }
    }
  }
  </script>
  