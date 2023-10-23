<template>
	<keep-alive include="RecorderDetail">
		<router-view/>
	</keep-alive>
</template>

<script>
export default {
	name: "RecorderRoot",
	watch: {
		async $route() {
			sparrow.router.current_route = await sparrow.router.parse();
			sparrow.breadcrumbs.update();
		}
	}
};
</script>
