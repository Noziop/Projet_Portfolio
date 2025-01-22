<!-- src/components/layout/AppFooter.vue -->
<template>
    <v-footer app color="transparent" class="text-center">
      <v-container>
        <div class="text-body-2 text-medium-emphasis">
          © {{ new Date().getFullYear() }} StellarStudio. All rights reserved.
        </div>
      </v-container>
    </v-footer>
  </template>
  
  <script>
  export default {
    name: 'AppFooter'
  }
  </script>
  