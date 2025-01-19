<template>
    <v-app>
      <v-app-bar app>
        <v-app-bar-title>Stellar Studio</v-app-bar-title>
        <v-spacer></v-spacer>
        <v-btn to="/">Home</v-btn>
        <v-btn to="/processing">Processing</v-btn>
      </v-app-bar>
  
      <v-main>
        <v-container>
          <slot></slot>
        </v-container>
      </v-main>
    </v-app>
  </template>
  
  <script>
  export default {
    name: 'DefaultLayout'
  }
  </script>
  