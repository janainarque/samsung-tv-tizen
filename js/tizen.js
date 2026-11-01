(function () {
    window.TizenApp = {
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
