window.onload = function() {
    if (document.getElementById("forecast-popup")) {
        let popup = confirm("Do you want to see the 5-day forecast for the same city?");
        if (popup) {
            document.getElementById("same-city-form").submit();
        }
    }
};
