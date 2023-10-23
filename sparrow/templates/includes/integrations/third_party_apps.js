sparrow.ready(() => {
	$(".btn-delete-app").on("click", function(event) {
		sparrow.call({
			method:"sparrow.www.third_party_apps.delete_client",
			args: {"client_id": $(this).data("client_id"),
			}
		}).done(r => location.href="/third_party_apps");
	});
});
