<!-- src/components/layout/AppFooter.vue -->
<template>
    <v-footer app color="transparent" class="text-center">
      <v-container>
        <div class="text-body-2 text-medium-emphasis">
          Bound together by 
          <math>
            <mi>F</mi>
            <mo>=</mo>
            <mi>G</mi>
            <mfrac>
              <mrow>
                <msub><mi>m</mi><mi>code</mi></msub>
                <msub><mi>m</mi><mi>love</mi></msub>
              </mrow>
              <msup><mi>r</mi><mn>2</mn></msup>
            </mfrac>
          </math>  
          by StellarStudio © {{ new Date().getFullYear() }}
        </div>
      </v-container>
    </v-footer>
  </template>
  
  
  <script>
  export default {
    name: 'AppFooter'
  }
  </script>
  