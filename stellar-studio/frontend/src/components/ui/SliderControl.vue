<!-- src/components/ui/SliderControl.vue -->
<template>
    <div class="slider-control">
      <div class="d-flex justify-space-between">
        <label>{{ label }}</label>
        <span class="text-caption">{{ displayValue }}</span>
      </div>
      <v-slider
        v-model="internalValue"
        :min="min"
        :max="max"
        :step="step"
        :disabled="disabled"
        @update:model-value="updateValue"
      ></v-slider>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      modelValue: Number,
      label: String,
      min: { type: Number, default: 0 },
      max: { type: Number, default: 100 },
      step: { type: Number, default: 1 },
      unit: { type: String, default: '' },
      disabled: Boolean
    },
    
    emits: ['update:modelValue'],
    
    computed: {
      internalValue: {
        get() {
          return this.modelValue;
        },
        set(value) {
          this.$emit('update:modelValue', value);
        }
      },
      
      displayValue() {
        return `${this.modelValue}${this.unit}`;
      }
    },
    
    methods: {
      updateValue(value) {
        this.$emit('update:modelValue', value);
      }
    }
  }
  </script>
  