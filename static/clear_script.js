window.addEventListener("beforeunload", function (event) {
    fetch("/clear_session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });
});