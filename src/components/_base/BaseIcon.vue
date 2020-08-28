<template>
  <component
    :is="require(`@/assets/svgs/${name}.svg`).default"
    class="BaseIcon"
     v-bind="$attrs"
     @v-on="$listeners"
  />
</template>

<script>


export default {
  name: 'BaseIcon',
  
  props: {
    name: {
      type: String, 
      required: true,
    }
  }
}

</script>
