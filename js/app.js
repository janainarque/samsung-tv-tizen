(function () {
    var button = document.getElementById("samsung-original");
    var status = document.getElementById("exit-status");

    function exitApplication() {
        status.textContent = "";

        try {
            TizenApp.exitApplication();
        } catch (error) {
            status.textContent = error.message;
        }
    }

    button.addEventListener("click", exitApplication);

    document.addEventListener("keydown", function (event) {
        var keyCode = event.keyCode;
        var isArrow =
            event.key === "ArrowLeft" ||
            event.key === "ArrowUp" ||
            event.key === "ArrowRight" ||
            event.key === "ArrowDown" ||
            (keyCode >= 37 && keyCode <= 40);

        if (isArrow) {
            event.preventDefault();
            button.focus();
        }
    });

    button.focus();
}());
