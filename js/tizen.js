(function () {
    window.TizenApp = {
        // Reference: Free My TV, web/tv.js (samsungApps), MIT licensed.
        // Independent implementation; no source code copied from that project.
        getInstalledApps: function (onSuccess, onError) {
            if (
                !window.tizen ||
                !window.tizen.application ||
                typeof window.tizen.application.getAppsInfo !== "function"
            ) {
                onError({ name: "TizenUnavailable" });
                return;
            }

            // Samsung's getAppsInfo reference declares no required privilege.
            // Keep an empty successful list distinct from an API failure.
            try {
                window.tizen.application.getAppsInfo(function (applications) {
                    onSuccess(applications.map(function (application) {
                        return { id: application.id, name: application.name || "" };
                    }));
                }, function (error) {
                    onError({ name: error && error.name || "UnknownError" });
                });
            } catch (error) {
                onError({ name: error && error.name || "UnknownError" });
            }
        },

        exitApplication: function () {
            if (
                !window.tizen ||
                !window.tizen.application ||
                typeof window.tizen.application.getCurrentApplication !== "function"
            ) {
                throw new Error(
                    "A saída da aplicação está disponível apenas no ambiente Tizen."
                );
            }

            try {
                window.tizen.application.getCurrentApplication().exit();
            } catch (error) {
                throw new Error("Não foi possível encerrar a aplicação.");
            }
        }
    };
}());
