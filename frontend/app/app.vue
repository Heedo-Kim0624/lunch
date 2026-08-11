<script setup lang="ts">
const { initialize } = useAuth()

onMounted(() => {
  void initialize()
})
</script>

<template>
  <div>
    <AppNav />
    <NuxtPage />
  </div>
</template>
