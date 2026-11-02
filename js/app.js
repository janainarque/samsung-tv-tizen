(function () {
    var button = document.getElementById("samsung-original");
    var status = document.getElementById("exit-status");
    var clock = document.getElementById("clock");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".app-card"));
    var lastCardIndex = 0;
    var messageTimer;

    function showMessage(message) {
        window.clearTimeout(messageTimer);
        status.textContent = message;
        messageTimer = window.setTimeout(function () {
            status.textContent = "";
        }, 4000);
    }

    function updateClock() {
        var now = new Date();
        function pad(value) { return value < 10 ? "0" + value : String(value); }
        clock.textContent = pad(now.getHours()) + ":" + pad(now.getMinutes());
        clock.dateTime = now.toISOString();
    }

    function exitApplication() {
        status.textContent = "";

        try {
            TizenApp.exitApplication();
        } catch (error) {
            showMessage(error.message);
        }
    }

    button.addEventListener("click", exitApplication);

    cards.forEach(function (card, index) {
        card.addEventListener("focus", function () { lastCardIndex = index; });
        card.addEventListener("click", function () {
            showMessage(card.getAttribute("data-app") + " · Aplicativo demonstrativo.");
        });
    });

    // Layout offsets stay stable during the focus animation and support wrapped rows.
    function moveCardFocus(current, direction) {
        var originX = current.offsetLeft + current.offsetWidth / 2;
        var originY = current.offsetTop + current.offsetHeight / 2;
        var best = null;
        var bestScore = Infinity;
        cards.forEach(function (card) {
            if (card === current) { return; }
            var dx = card.offsetLeft + card.offsetWidth / 2 - originX;
            var dy = card.offsetTop + card.offsetHeight / 2 - originY;
            var horizontal = direction === "left" || direction === "right";
            var forward = direction === "left" ? -dx : direction === "right" ? dx : direction === "up" ? -dy : dy;
            var sideways = Math.abs(horizontal ? dy : dx);
            if (forward <= 10 || (horizontal && sideways > current.offsetHeight / 2)) { return; }
            var score = forward + sideways * 3;
            if (score < bestScore) { bestScore = score; best = card; }
        });
        if (best) { best.focus(); }
        else if (direction === "up") { button.focus(); }
    }

    document.addEventListener("keydown", function (event) {
        if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) { return; }
        var directions = { ArrowLeft: "left", ArrowUp: "up", ArrowRight: "right", ArrowDown: "down" };
        var legacyDirections = { 37: "left", 38: "up", 39: "right", 40: "down" };
        var direction = directions[event.key] || legacyDirections[event.keyCode];
        if (!direction) { return; }
        var focused = document.activeElement;
        if (focused !== button && cards.indexOf(focused) === -1) { return; }
        event.preventDefault();
        if (focused === button) {
            if (direction === "down") { cards[lastCardIndex].focus(); }
        } else {
            moveCardFocus(focused, direction);
        }
    });

    updateClock();
    window.setInterval(updateClock, 1000);
    cards[0].focus();

    // Temporary discovery diagnostics; never log IDs, paths or raw API errors.
    TizenApp.getInstalledApps(function (applications) {
        console.log("[Tizen apps] Consulta concluida. Total: " + applications.length);
        console.log("[Tizen apps] Nomes:", applications.map(function (application) {
            return application.name || "(sem nome)";
        }));
    }, function (error) {
        if (error.name === "TizenUnavailable") {
            console.log("[Tizen apps] API indisponivel neste ambiente; consulta ignorada.");
            return;
        }
        console.log("[Tizen apps] Falha na consulta: " + error.name);
    });
}());
